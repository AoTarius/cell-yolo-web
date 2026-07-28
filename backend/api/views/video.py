"""
视频管理相关视图

提供视频上传、原始视频访问、视频列表、删除、重命名等功能。
支持 MP4、AVI、MOV、MKV 格式。
"""

import json
import os
import shutil
import uuid
from pathlib import Path

import cv2
import pymysql
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse, HttpResponseNotFound

load_dotenv()


class UploadVideoView(APIView):
    """上传视频接口"""

    def post(self, request):
        try:
            video_file = request.FILES.get('video')
            if not video_file:
                return Response(
                    {'error': '未找到视频文件'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 验证文件类型
            allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv']
            file_ext = Path(video_file.name).suffix.lower()
            if file_ext not in allowed_extensions:
                return Response(
                    {'error': f'不支持的视频格式，支持的格式: {", ".join(allowed_extensions)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 获取用户名
            username = request.data.get('username', '')
            if not username:
                return Response(
                    {'error': '未提供用户名'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 连接数据库
            try:
                connection = pymysql.connect(
                    host=os.getenv('DB_HOST', 'localhost'),
                    port=int(os.getenv('DB_PORT', 3306)),
                    user=os.getenv('DB_USER', 'root'),
                    password=os.getenv('DB_PASSWORD', ''),
                    database=os.getenv('DB_NAME', 'cell_tracking'),
                    cursorclass=pymysql.cursors.DictCursor
                )
            except pymysql.Error as e:
                return Response(
                    {'error': f'数据库连接失败: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            try:
                with connection.cursor() as cursor:
                    # 查询用户信息
                    user_sql = "SELECT id, output_base_path FROM users WHERE username = %s AND is_deleted = FALSE"
                    cursor.execute(user_sql, (username,))
                    user = cursor.fetchone()

                    if not user:
                        return Response(
                            {'error': '用户不存在'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    user_id = user['id']
                    output_base_path = Path(user['output_base_path'])

                    # 检查视频是否已存在（包含软删除记录，避免唯一键冲突）
                    check_sql = "SELECT id, video_path, is_deleted FROM videos WHERE user_id = %s AND video_name = %s"
                    cursor.execute(check_sql, (user_id, video_file.name))
                    existing_video = cursor.fetchone()

                    if existing_video:
                        if not existing_video['is_deleted']:
                            # 视频已存在，直接返回现有视频信息
                            video_id = existing_video['id']
                            task_id = str(uuid.uuid4())
                            return Response({
                                'task_id': task_id,
                                'video_id': video_id,
                                'video_name': video_file.name,
                                'status': 'existing',
                                'message': '视频已存在，将使用现有视频'
                            }, status=status.HTTP_200_OK)

                        # 已软删除：恢复原记录并复用原 video_id
                        video_id = existing_video['id']
                        restore_sql = """
                        UPDATE videos
                        SET is_deleted = FALSE,
                            deleted_at = NULL,
                            updated_at = NOW(),
                            total_frames = NULL,
                            video_duration = NULL,
                            file_size = NULL
                        WHERE id = %s
                        """
                        cursor.execute(restore_sql, (video_id,))
                        connection.commit()
                    else:
                        # 创建 videos 记录
                        insert_sql = """
                        INSERT INTO videos (user_id, video_name, video_path, created_at, updated_at, is_deleted, deleted_at)
                        VALUES (%s, %s, %s, NOW(), NOW(), FALSE, NULL)
                        """
                        cursor.execute(insert_sql, (user_id, video_file.name, ''))
                        connection.commit()
                        video_id = cursor.lastrowid

                    # 生成视频路径：videos/{video_id}/{video_name}
                    video_path_relative = f"videos/{video_id}/{video_file.name}"
                    video_path_full = output_base_path / video_path_relative

                    # 更新视频路径
                    update_sql = "UPDATE videos SET video_path = %s WHERE id = %s"
                    cursor.execute(update_sql, (video_path_relative, video_id))
                    connection.commit()

                    # 创建视频目录并保存文件
                    video_path_full.parent.mkdir(parents=True, exist_ok=True)
                    with open(video_path_full, 'wb') as f:
                        for chunk in video_file.chunks():
                            f.write(chunk)

                    # 获取视频元数据
                    cap = cv2.VideoCapture(str(video_path_full))
                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    video_fps = cap.get(cv2.CAP_PROP_FPS)
                    video_duration = total_frames / video_fps if video_fps > 0 else 0
                    file_size = video_path_full.stat().st_size
                    cap.release()

                    # 更新视频元数据
                    update_meta_sql = """
                    UPDATE videos
                    SET total_frames = %s, video_duration = %s, file_size = %s
                    WHERE id = %s
                    """
                    cursor.execute(update_meta_sql, (total_frames, video_duration, file_size, video_id))
                    connection.commit()

                    # 生成任务ID
                    task_id = str(uuid.uuid4())

                    return Response({
                        'task_id': task_id,
                        'video_id': video_id,
                        'video_name': video_file.name,
                        'status': 'uploaded',
                        'message': '视频上传成功'
                    }, status=status.HTTP_201_CREATED)

            finally:
                connection.close()

        except Exception as e:
            return Response(
                {'error': f'上传失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OriginalVideoView(APIView):
    """获取原始视频接口"""

    def get(self, request, task_id):
        try:
            # 连接数据库
            connection = pymysql.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 3306)),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'cell_tracking'),
                cursorclass=pymysql.cursors.DictCursor
            )
        except pymysql.Error as e:
            return Response(
                {'error': f'数据库连接失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            with connection.cursor() as cursor:
                # 查询任务信息和视频路径
                task_sql = """
                SELECT v.video_name, v.video_path, u.output_base_path
                FROM tasks t
                JOIN videos v ON t.video_id = v.id
                JOIN users u ON t.user_id = u.id
                WHERE t.task_id = %s AND t.is_deleted = FALSE AND v.is_deleted = FALSE AND u.is_deleted = FALSE
                """
                cursor.execute(task_sql, (task_id,))
                task_info = cursor.fetchone()

                if not task_info:
                    return HttpResponseNotFound('任务不存在或视频不存在')

                video_name = task_info['video_name']
                video_path_relative = task_info['video_path']
                output_base_path = Path(task_info['output_base_path'])

                # 拼接完整路径
                video_path = output_base_path / video_path_relative

                if not video_path.exists():
                    return HttpResponseNotFound('视频文件不存在')

                # 返回视频文件
                return FileResponse(
                    open(video_path, 'rb'),
                    content_type='video/mp4',
                    as_attachment=False
                )

        finally:
            connection.close()


class VideoListView(APIView):
    """获取可用视频列表接口"""

    def get(self, request):
        """从数据库获取用户的视频列表，并拼接完整路径"""
        username = request.GET.get('username')

        if not username:
            return Response(
                {'error': '未提供用户名'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 连接数据库
        try:
            connection = pymysql.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 3306)),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'cell_tracking'),
                cursorclass=pymysql.cursors.DictCursor
            )
        except pymysql.Error as e:
            return Response(
                {'error': f'数据库连接失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            with connection.cursor() as cursor:
                # 查询用户信息
                user_sql = "SELECT id, output_base_path FROM users WHERE username = %s AND is_deleted = FALSE"
                cursor.execute(user_sql, (username,))
                user = cursor.fetchone()

                if not user:
                    return Response(
                        {'error': '用户不存在'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                user_id = user['id']
                output_base_path = user['output_base_path']

                # 查询用户的视频列表
                videos_sql = """
                SELECT id, video_name, video_path, total_frames, video_duration, file_size
                FROM videos
                WHERE user_id = %s AND is_deleted = FALSE
                ORDER BY created_at DESC
                """
                cursor.execute(videos_sql, (user_id,))
                video_records = cursor.fetchall()

                # 构建视频列表
                videos = []
                videos_dir = Path(output_base_path) / 'videos'

                for record in video_records:
                    video_name = (record.get('video_name') or '').strip()
                    video_path = str(record.get('video_path') or '').strip()
                    video_id = record.get('id')

                    # 构建完整路径
                    if video_path:
                        # 去掉开头的 "videos/"（如果存在）
                        if video_path.startswith('videos/'):
                            video_path = video_path[7:]  # 去掉 "videos/" 前缀
                        full_path = videos_dir / video_path
                    else:
                        full_path = videos_dir / str(video_id) / video_name

                    if full_path.exists() and full_path.is_file():
                        try:
                            relative_path = str(full_path.relative_to(videos_dir))
                        except Exception:
                            relative_path = video_path

                        videos.append({
                            'id': video_id,
                            'name': video_name,
                            'size_mb': round(record.get('file_size', 0) / (1024 * 1024), 2),
                            'path': relative_path,
                            'total_frames': record.get('total_frames', 0),
                            'duration': record.get('video_duration', 0)
                        })
                    else:
                        # 文件不存在但数据库有记录，仍返回记录
                        videos.append({
                            'id': video_id,
                            'name': video_name,
                            'size_mb': 0,
                            'path': video_path,
                            'total_frames': 0,
                            'duration': 0
                        })

                return Response({
                    'videos': videos
                }, status=status.HTTP_200_OK)

        finally:
            connection.close()


class DeleteVideoView(APIView):
    """删除视频接口"""

    def delete(self, request):
        """删除指定的视频文件和数据库记录"""
        try:
            username = request.GET.get('username')
            video_id = request.GET.get('video_id')

            if not username:
                return Response(
                    {'error': '未提供用户名'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not video_id:
                return Response(
                    {'error': '未提供视频ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 连接数据库
            try:
                connection = pymysql.connect(
                    host=os.getenv('DB_HOST', 'localhost'),
                    port=int(os.getenv('DB_PORT', 3306)),
                    user=os.getenv('DB_USER', 'root'),
                    password=os.getenv('DB_PASSWORD', ''),
                    database=os.getenv('DB_NAME', 'cell_tracking'),
                    cursorclass=pymysql.cursors.DictCursor
                )
            except pymysql.Error as e:
                return Response(
                    {'error': f'数据库连接失败: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            try:
                with connection.cursor() as cursor:
                    # 查询用户信息
                    user_sql = "SELECT id, output_base_path FROM users WHERE username = %s AND is_deleted = FALSE"
                    cursor.execute(user_sql, (username,))
                    user = cursor.fetchone()

                    if not user:
                        return Response(
                            {'error': '用户不存在'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    user_id = user['id']
                    output_base_path = user['output_base_path']

                    # 查询视频信息
                    video_sql = """
                    SELECT video_name, video_path
                    FROM videos
                    WHERE id = %s AND user_id = %s AND is_deleted = FALSE
                    """
                    cursor.execute(video_sql, (video_id, user_id))
                    video_record = cursor.fetchone()

                    if not video_record:
                        return Response(
                            {'error': '视频不存在'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    video_name = video_record['video_name']
                    video_path = video_record['video_path']

                    # 检查是否有任务正在使用该视频
                    check_tasks_sql = """
                    SELECT COUNT(*) as task_count
                    FROM tasks
                    WHERE video_id = %s AND is_deleted = FALSE AND status IN ('pending', 'processing')
                    """
                    cursor.execute(check_tasks_sql, (video_id,))
                    task_count = cursor.fetchone()

                    if task_count['task_count'] > 0:
                        return Response(
                            {'error': f'无法删除：有 {task_count["task_count"]} 个任务正在使用该视频'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # 删除数据库记录（软删除）
                    delete_sql = """
                    UPDATE videos
                    SET is_deleted = TRUE, deleted_at = NOW()
                    WHERE id = %s AND user_id = %s AND is_deleted = FALSE
                    """
                    cursor.execute(delete_sql, (video_id, user_id))
                    connection.commit()

                # 删除本地文件
                videos_dir = Path(output_base_path) / 'videos'
                video_dir = videos_dir / str(video_id)

                # 删除视频文件和目录
                if video_dir.exists():
                    shutil.rmtree(video_dir)

                return Response({
                    'message': '视频已成功删除',
                    'video_name': video_name
                }, status=status.HTTP_200_OK)

            finally:
                connection.close()

        except Exception as e:
            return Response(
                {'error': f'删除视频失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RenameVideoView(APIView):
    """修改视频名称接口"""

    def post(self, request):
        """修改视频的名称（只修改数据库中的video_name，不修改文件名）"""
        try:
            data = json.loads(request.body)
            username = data.get('username')
            video_id = data.get('video_id')
            new_video_name = data.get('new_video_name')

            if not username:
                return Response(
                    {'error': '未提供用户名'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not video_id:
                return Response(
                    {'error': '未提供视频ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not new_video_name:
                return Response(
                    {'error': '未提供新视频名称'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 验证新名称不为空
            if not new_video_name.strip():
                return Response(
                    {'error': '新视频名称不能为空'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 验证文件扩展名
            allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv']
            file_ext = Path(new_video_name).suffix.lower()
            if file_ext not in allowed_extensions:
                return Response(
                    {'error': f'不支持的视频格式，支持的格式: {", ".join(allowed_extensions)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 连接数据库
            try:
                connection = pymysql.connect(
                    host=os.getenv('DB_HOST', 'localhost'),
                    port=int(os.getenv('DB_PORT', 3306)),
                    user=os.getenv('DB_USER', 'root'),
                    password=os.getenv('DB_PASSWORD', ''),
                    database=os.getenv('DB_NAME', 'cell_tracking'),
                    cursorclass=pymysql.cursors.DictCursor
                )
            except pymysql.Error as e:
                return Response(
                    {'error': f'数据库连接失败: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            try:
                with connection.cursor() as cursor:
                    # 查询用户信息
                    user_sql = "SELECT id FROM users WHERE username = %s AND is_deleted = FALSE"
                    cursor.execute(user_sql, (username,))
                    user = cursor.fetchone()

                    if not user:
                        return Response(
                            {'error': '用户不存在'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    user_id = user['id']

                    # 查询视频信息
                    video_sql = """
                    SELECT video_name
                    FROM videos
                    WHERE id = %s AND user_id = %s AND is_deleted = FALSE
                    """
                    cursor.execute(video_sql, (video_id, user_id))
                    video_record = cursor.fetchone()

                    if not video_record:
                        return Response(
                            {'error': '视频不存在'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    old_video_name = video_record['video_name']

                    # 检查新名称是否与原名称相同
                    if new_video_name == old_video_name:
                        return Response(
                            {'message': '新名称与原名称相同'},
                            status=status.HTTP_200_OK
                        )

                    # 检查新名称是否已被其他视频使用
                    check_sql = """
                    SELECT id FROM videos
                    WHERE user_id = %s AND video_name = %s AND id != %s AND is_deleted = FALSE
                    """
                    cursor.execute(check_sql, (user_id, new_video_name, video_id))
                    existing_video = cursor.fetchone()

                    if existing_video:
                        return Response(
                            {'error': f'视频名称 "{new_video_name}" 已存在'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # 更新视频名称
                    update_sql = """
                    UPDATE videos
                    SET video_name = %s, updated_at = NOW()
                    WHERE id = %s AND user_id = %s AND is_deleted = FALSE
                    """
                    cursor.execute(update_sql, (new_video_name, video_id, user_id))
                    connection.commit()

                return Response({
                    'message': '视频名称修改成功',
                    'old_video_name': old_video_name,
                    'new_video_name': new_video_name
                }, status=status.HTTP_200_OK)

            finally:
                connection.close()

        except Exception as e:
            return Response(
                {'error': f'修改视频名称失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
