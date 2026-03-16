import os
import json
import uuid
import threading
import bcrypt
from pathlib import Path
from datetime import datetime

from django.conf import settings
from django.http import JsonResponse, FileResponse, HttpResponseNotFound, HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .services.video_processor import VideoProcessor


# 数据库连接配置
import pymysql
from dotenv import load_dotenv

load_dotenv()


# 全局任务状态存储（生产环境应使用数据库或 Redis）
task_status = {}
task_lock = threading.Lock()


# 线程标识辅助函数
def get_thread_prefix(task_id: str = None):
    """获取线程标识前缀，格式: [task_id|T线程ID] 或 [T线程ID]（带颜色）"""
    thread_id = f"T{threading.current_thread().ident}"
    # ANSI 颜色码
    BLUE = '\033[94m'      # 亮蓝色
    CYAN = '\033[96m'      # 青色
    RESET = '\033[0m'      # 重置颜色

    if task_id:
        return f"{BLUE}[{task_id}|{CYAN}{thread_id}{BLUE}]{RESET}"
    return f"{BLUE}[{CYAN}{thread_id}{BLUE}]{RESET}"


@api_view(['GET'])
def test_api(request):
    return Response({
        'message': 'Django + Vue 前后端分离项目已启动！',
        'status': 'success'
    }, status=status.HTTP_200_OK)


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

                    # 检查视频是否已存在（同一用户下视频名称唯一）
                    check_sql = "SELECT id, video_path FROM videos WHERE user_id = %s AND video_name = %s AND is_deleted = FALSE"
                    cursor.execute(check_sql, (user_id, video_file.name))
                    existing_video = cursor.fetchone()

                    if existing_video:
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
                    import cv2
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


class ProcessTaskView(APIView):
    """启动处理任务接口"""

    def post(self, request):
        try:
            data = json.loads(request.body)
            task_id = data.get('task_id')
            video_id = data.get('video_id')

            if not task_id:
                return Response(
                    {'error': '缺少 task_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not video_id:
                return Response(
                    {'error': '缺少 video_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 获取参数
            conf = data.get('conf', 0.3)
            imgsz = data.get('imgsz', 1024)
            fps = data.get('fps', 10)
            model_name = data.get('model_name', 'best_split.pt')
            username = data.get('username', '')

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
                    user_sql = "SELECT id, model_base_path, output_base_path FROM users WHERE username = %s AND is_deleted = FALSE"
                    cursor.execute(user_sql, (username,))
                    user = cursor.fetchone()

                    if not user:
                        return Response(
                            {'error': '用户不存在'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    user_id = user['id']
                    model_base_path = Path(user['model_base_path'])
                    output_base_path = Path(user['output_base_path'])

                    # 查询视频信息
                    video_sql = "SELECT video_name, video_path FROM videos WHERE id = %s AND user_id = %s AND is_deleted = FALSE"
                    cursor.execute(video_sql, (video_id, user_id))
                    video_record = cursor.fetchone()

                    if not video_record:
                        return Response(
                            {'error': f'视频不存在或无权访问'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    video_name = video_record['video_name']
                    video_path_relative = video_record['video_path']
                    video_path_full = output_base_path / video_path_relative

                    # 验证视频文件是否存在
                    if not video_path_full.exists():
                        return Response(
                            {'error': f'视频文件不存在: {video_path_full}'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    # 查询模型信息
                    model_sql = """
                    SELECT id, model_path
                    FROM models
                    WHERE user_id = %s AND model_name = %s AND is_deleted = FALSE
                    """
                    cursor.execute(model_sql, (user_id, model_name.rsplit('.', 1)[0]))
                    model_record = cursor.fetchone()

                    if not model_record:
                        return Response(
                            {'error': f'模型 {model_name} 不存在'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    model_id = model_record['id']
                    model_path_relative = model_record['model_path']
                    model_path_full = model_base_path / model_path_relative

                    # 验证模型文件是否存在
                    if not model_path_full.exists():
                        return Response(
                            {'error': f'模型文件不存在: {model_path_full}'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    # 创建 tasks 记录
                    task_name = video_name
                    annotated_video_name = "tracking_result.mp4"
                    insert_sql = """
                    INSERT INTO tasks (user_id, video_id, model_id, task_id, task_name, status, conf, imgsz, fps, annotated_video_name, created_at, updated_at, is_deleted, deleted_at)
                    VALUES (%s, %s, %s, %s, %s, 'pending', %s, %s, %s, %s, NOW(), NOW(), FALSE, NULL)
                    """
                    cursor.execute(insert_sql, (user_id, video_id, model_id, task_id, task_name, conf, imgsz, fps, annotated_video_name))
                    connection.commit()

                    # 创建 task_status 记录
                    status_insert_sql = """
                    INSERT INTO task_status (task_id, status, progress, stage, current_frame, total_frames, created_at, updated_at, is_deleted, deleted_at)
                    VALUES (%s, 'pending', 0, NULL, 0, 0, NOW(), NOW(), FALSE, NULL)
                    """
                    cursor.execute(status_insert_sql, (task_id,))
                    connection.commit()

                    # 创建任务目录
                    task_dir = output_base_path / 'tasks' / task_id
                    task_dir.mkdir(parents=True, exist_ok=True)

            finally:
                connection.close()

            # 在后台线程中处理视频
            thread = threading.Thread(
                target=self._process_video,
                args=(task_id, str(video_path_full), str(model_path_full), str(output_base_path), conf, imgsz, fps),
                daemon=True
            )
            thread.start()

            return Response({
                'task_id': task_id,
                'status': 'processing',
                'message': '任务已启动'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'启动任务失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _process_video(self, task_id: str, video_path: str, model_path: str, output_base_path: str, conf: float, imgsz: int, fps: int):
        """后台处理视频"""
        print(f"{get_thread_prefix(task_id)} 开始处理任务")
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

            # 更新任务状态为 processing
            with connection.cursor() as cursor:
                update_sql = "UPDATE tasks SET status = 'processing', updated_at = NOW() WHERE task_id = %s"
                cursor.execute(update_sql, (task_id,))
                connection.commit()

            print(f"{get_thread_prefix(task_id)} 获取视频处理器")

            # 创建视频处理器实例
            processor = VideoProcessor(str(model_path), str(output_base_path))

            # 进度回调函数
            def progress_callback(stage: str, progress: int, data: dict):
                with connection.cursor() as cursor:
                    # 先确保task_status记录存在
                    insert_sql = """
                    INSERT INTO task_status (task_id, status, progress, stage, current_frame, total_frames, created_at, updated_at, is_deleted, deleted_at)
                    VALUES (%s, 'processing', %s, %s, %s, %s, NOW(), NOW(), FALSE, NULL)
                    ON DUPLICATE KEY UPDATE
                        status = 'processing',
                        progress = %s,
                        stage = %s,
                        current_frame = %s,
                        total_frames = %s,
                        updated_at = NOW()
                    """
                    cursor.execute(insert_sql, (
                        task_id, progress, stage, data.get('current_frame', 0), data.get('total_frames', 0),
                        progress, stage, data.get('current_frame', 0), data.get('total_frames', 0)
                    ))
                    connection.commit()

            print(f"{get_thread_prefix(task_id)} 开始处理视频，参数: conf={conf}, imgsz={imgsz}, fps={fps}, model_path={model_path}")

            # 处理视频
            result = processor.process_video(
                video_path,
                task_id,
                conf=conf,
                imgsz=imgsz,
                fps=fps,
                model_path=model_path,
                progress_callback=progress_callback
            )

            print(f"{get_thread_prefix(task_id)} 视频处理完成")

            # 更新任务状态为 completed
            with connection.cursor() as cursor:
                update_sql = "UPDATE tasks SET status = 'completed', updated_at = NOW() WHERE task_id = %s"
                cursor.execute(update_sql, (task_id,))

                # 同时更新task_status表
                status_update_sql = "UPDATE task_status SET status = 'completed', progress = 100, updated_at = NOW() WHERE task_id = %s"
                cursor.execute(status_update_sql, (task_id,))

                connection.commit()

        except Exception as e:
            # 更新任务状态为失败
            print(f"{get_thread_prefix(task_id)} 处理失败: {str(e)}")
            try:
                with connection.cursor() as cursor:
                    update_sql = """
                    UPDATE tasks
                    SET status = 'failed', error_message = %s, updated_at = NOW()
                    WHERE task_id = %s
                    """
                    cursor.execute(update_sql, (str(e), task_id))

                    # 同时更新task_status表
                    status_update_sql = "UPDATE task_status SET status = 'failed', error_message = %s, updated_at = NOW() WHERE task_id = %s"
                    cursor.execute(status_update_sql, (str(e), task_id))

                    connection.commit()
            except Exception as db_error:
                print(f"{get_thread_prefix(task_id)} 更新失败状态时出错: {str(db_error)}")
            finally:
                if 'connection' in locals():
                    connection.close()


class TaskStatusView(APIView):
    """查询任务状态接口"""

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
                # 查询任务信息
                task_sql = """
                SELECT t.id, t.user_id, t.video_id, t.model_id, t.task_id, t.task_name, t.status,
                       ts.progress, ts.stage, ts.current_frame, ts.total_frames,
                       t.conf, t.imgsz, t.fps, t.annotated_video_name, t.error_message,
                       t.created_at, t.updated_at, u.output_base_path, v.video_name
                FROM tasks t
                JOIN users u ON t.user_id = u.id
                JOIN videos v ON t.video_id = v.id
                LEFT JOIN task_status ts ON t.task_id = ts.task_id
                WHERE t.task_id = %s AND t.is_deleted = FALSE AND u.is_deleted = FALSE AND v.is_deleted = FALSE
                """
                cursor.execute(task_sql, (task_id,))
                task_info = cursor.fetchone()

                if not task_info:
                    return Response(
                        {'error': '任务不存在'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # 如果任务完成，读取 JSON 结果
                if task_info['status'] == 'completed':
                    try:
                        output_base_path = Path(task_info['output_base_path'])
                        json_path = output_base_path / 'tasks' / task_id / 'result.json'
                        if json_path.exists():
                            with open(json_path, 'r', encoding='utf-8') as f:
                                task_info['result'] = json.load(f)
                    except Exception as e:
                        task_info['error'] = f'读取结果失败: {str(e)}'

                return Response(task_info, status=status.HTTP_200_OK)

        finally:
            connection.close()


class TaskResultView(APIView):
    """获取处理结果接口"""

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
                # 查询任务信息和用户的 output_base_path
                task_sql = """
                SELECT u.output_base_path, t.status
                FROM tasks t
                JOIN users u ON t.user_id = u.id
                WHERE t.task_id = %s AND t.is_deleted = FALSE AND u.is_deleted = FALSE
                """
                cursor.execute(task_sql, (task_id,))
                task_info = cursor.fetchone()

                if not task_info:
                    return Response(
                        {'error': '任务不存在'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                if task_info['status'] != 'completed':
                    return Response(
                        {'error': '任务尚未完成'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                output_base_path = Path(task_info['output_base_path'])
                json_path = output_base_path / 'tasks' / task_id / 'result.json'

                if not json_path.exists():
                    return Response(
                        {'error': '结果不存在'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                with open(json_path, 'r', encoding='utf-8') as f:
                    result = json.load(f)

                return Response(result, status=status.HTTP_200_OK)

        finally:
            connection.close()


class AnnotatedVideoView(APIView):
    """获取标注视频接口"""

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
                # 查询任务信息和用户的 output_base_path
                task_sql = """
                SELECT t.annotated_video_name, u.output_base_path
                FROM tasks t
                JOIN users u ON t.user_id = u.id
                WHERE t.task_id = %s AND t.is_deleted = FALSE AND u.is_deleted = FALSE
                """
                cursor.execute(task_sql, (task_id,))
                task_info = cursor.fetchone()

                if not task_info:
                    return HttpResponseNotFound('任务不存在')

                annotated_video_name = task_info['annotated_video_name']
                output_base_path = Path(task_info['output_base_path'])

                # 拼接完整路径
                video_path = output_base_path / 'tasks' / task_id / 'output' / annotated_video_name

                if not video_path.exists():
                    return HttpResponseNotFound('视频不存在')

                # 获取文件名
                filename = annotated_video_name

                # 返回视频文件
                return FileResponse(
                    open(video_path, 'rb'),
                    content_type='video/mp4',
                    as_attachment=True,
                    filename=filename
                )

        finally:
            connection.close()


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

                # 获取文件名
                filename = video_name

                # 返回视频文件
                return FileResponse(
                    open(video_path, 'rb'),
                    content_type='video/mp4',
                    as_attachment=True,
                    filename=filename
                )

        finally:
            connection.close()


class TaskListView(APIView):
    """获取所有任务列表接口"""

    def get(self, request):
        """获取所有任务（包括已完成和处理中）的列表"""
        username = request.GET.get('username')

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
                # 查询任务列表
                if username:
                    task_sql = """
                    SELECT t.id, t.user_id, t.video_id, t.model_id, t.task_id, t.task_name, t.status,
                           ts.progress, ts.stage, ts.current_frame, ts.total_frames,
                           t.conf, t.imgsz, t.fps, t.annotated_video_name, t.error_message,
                           t.created_at, t.updated_at, v.video_name, u.username, m.model_name as model_display_name
                    FROM tasks t
                    JOIN videos v ON t.video_id = v.id
                    JOIN users u ON t.user_id = u.id
                    LEFT JOIN models m ON t.model_id = m.id AND m.is_deleted = FALSE
                    LEFT JOIN task_status ts ON t.task_id = ts.task_id
                    WHERE u.username = %s AND t.is_deleted = FALSE AND u.is_deleted = FALSE AND v.is_deleted = FALSE
                    ORDER BY t.created_at DESC
                    """
                    cursor.execute(task_sql, (username,))
                else:
                    task_sql = """
                    SELECT t.id, t.user_id, t.video_id, t.model_id, t.task_id, t.task_name, t.status,
                           ts.progress, ts.stage, ts.current_frame, ts.total_frames,
                           t.conf, t.imgsz, t.fps, t.annotated_video_name, t.error_message,
                           t.created_at, t.updated_at, v.video_name, u.username, m.model_name as model_display_name
                    FROM tasks t
                    JOIN videos v ON t.video_id = v.id
                    JOIN users u ON t.user_id = u.id
                    LEFT JOIN models m ON t.model_id = m.id AND m.is_deleted = FALSE
                    LEFT JOIN task_status ts ON t.task_id = ts.task_id
                    WHERE t.is_deleted = FALSE AND u.is_deleted = FALSE AND v.is_deleted = FALSE
                    ORDER BY t.created_at DESC
                    """
                    cursor.execute(task_sql)

                tasks = cursor.fetchall()

                # 如果任务完成，读取 JSON 结果
                for task in tasks:
                    if task['status'] == 'completed':
                        try:
                            output_base_sql = "SELECT output_base_path FROM users WHERE id = %s AND is_deleted = FALSE"
                            cursor.execute(output_base_sql, (task['user_id'],))
                            user_info = cursor.fetchone()

                            if user_info:
                                output_base_path = Path(user_info['output_base_path'])
                                json_path = output_base_path / 'tasks' / task['task_id'] / 'result.json'
                                if json_path.exists():
                                    with open(json_path, 'r', encoding='utf-8') as f:
                                        task['result'] = json.load(f)
                        except Exception as e:
                            task['error'] = f'读取结果失败: {str(e)}'

                return Response({
                    'tasks': tasks,
                    'count': len(tasks)
                }, status=status.HTTP_200_OK)

        finally:
            connection.close()


class ModelListView(APIView):
    """获取可用模型列表接口"""

    def get(self, request):
        """从数据库获取用户的模型列表，并拼接完整路径"""
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
                user_sql = "SELECT id, model_base_path FROM users WHERE username = %s AND is_deleted = FALSE"
                cursor.execute(user_sql, (username,))
                user = cursor.fetchone()

                if not user:
                    return Response(
                        {'error': '用户不存在'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                user_id = user['id']
                model_base_path = user['model_base_path']

                # 查询用户的模型列表
                models_sql = """
                SELECT model_name, model_path
                FROM models
                WHERE user_id = %s AND is_deleted = FALSE
                ORDER BY created_at DESC
                """
                cursor.execute(models_sql, (user_id,))
                model_records = cursor.fetchall()

                # 构建模型列表，使用绝对路径
                models = []
                models_dir = Path(model_base_path)

                for record in model_records:
                    model_file = models_dir / record['model_path']
                    if model_file.exists():
                        models.append({
                            'name': record['model_name'],
                            'size_mb': round(model_file.stat().st_size / (1024 * 1024), 2),
                            'path': str(model_file.relative_to(models_dir))
                        })
                # 按名称排序
                models.sort(key=lambda x: x['name'])

                return Response({
                    'models': models,
                    'count': len(models),
                    'default': 'best_split.pt'
                }, status=status.HTTP_200_OK)

        finally:
            connection.close()


class DeleteModelView(APIView):
    """删除模型接口"""

    def delete(self, request):
        """删除指定的模型文件和数据库记录"""
        try:
            import os
            import shutil

            username = request.GET.get('username')
            model_name = request.GET.get('model_name')

            if not username:
                return Response(
                    {'error': '未提供用户名'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not model_name:
                return Response(
                    {'error': '未提供模型名称'},
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

                    # 查询用户信息和模型信息
                    user_model_sql = """
                    SELECT m.model_path, u.model_base_path
                    FROM models m
                    JOIN users u ON m.user_id = u.id
                    WHERE m.user_id = %s AND m.model_name = %s AND m.is_deleted = FALSE AND u.is_deleted = FALSE
                    """
                    cursor.execute(user_model_sql, (user_id, model_name))
                    model_record = cursor.fetchone()

                    if not model_record:
                        return Response(
                            {'error': f'模型 {model_name} 不存在'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    model_filename = model_record['model_path']
                    model_base_path = model_record['model_base_path']

                    # 删除数据库记录（软删除）
                    delete_sql = """
                    UPDATE models
                    SET is_deleted = TRUE, deleted_at = NOW()
                    WHERE user_id = %s AND model_name = %s AND is_deleted = FALSE
                    """
                    cursor.execute(delete_sql, (user_id, model_name))
                    connection.commit()

                # 删除本地文件（使用绝对路径）
                models_dir = Path(model_base_path)
                model_file = models_dir / model_filename

                if model_file.exists():
                    os.remove(model_file)
                else:
                    # 文件不存在但数据库有记录，只记录警告
                    print(f"警告：模型文件 {model_file} 不存在，但已从数据库删除记录")

                return Response({
                    'message': '模型已成功删除',
                    'model_name': model_name
                }, status=status.HTTP_200_OK)

            finally:
                connection.close()

        except Exception as e:
            return Response(
                {'error': f'删除模型失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RenameModelView(APIView):
    """修改模型名称接口"""

    def post(self, request):
        """修改模型的名称（只修改数据库中的model_name，不修改文件名）"""
        try:
            data = json.loads(request.body)
            username = data.get('username')
            old_model_name = data.get('old_model_name')
            new_model_name = data.get('new_model_name')

            if not username:
                return Response(
                    {'error': '未提供用户名'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not old_model_name:
                return Response(
                    {'error': '未提供原模型名称'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not new_model_name:
                return Response(
                    {'error': '未提供新模型名称'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 验证新名称不为空
            if not new_model_name.strip():
                return Response(
                    {'error': '新模型名称不能为空'},
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

                    # 查询原模型是否存在
                    check_old_sql = """
                    SELECT id, model_path FROM models
                    WHERE user_id = %s AND model_name = %s AND is_deleted = FALSE
                    """
                    cursor.execute(check_old_sql, (user_id, old_model_name))
                    old_model = cursor.fetchone()

                    if not old_model:
                        return Response(
                            {'error': f'模型 {old_model_name} 不存在'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    # 检查新名称是否已被其他模型使用（包括软删除的）
                    check_new_sql = """
                    SELECT id, model_path, is_deleted FROM models
                    WHERE user_id = %s AND model_name = %s
                    """
                    cursor.execute(check_new_sql, (user_id, new_model_name))
                    existing_models = cursor.fetchall()

                    for existing in existing_models:
                        # 如果新名称已被未删除的模型使用，不允许改名
                        if not existing['is_deleted']:
                            return Response(
                                {'error': f'模型名称 {new_model_name} 已存在'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        # 如果新名称已被软删除的模型使用，且路径相同，不允许改名（避免路径重复）
                        if existing['model_path'] == old_model['model_path']:
                            return Response(
                                {'error': f'无法改名为已删除的模型名称（路径冲突）'},
                                status=status.HTTP_400_BAD_REQUEST
                            )

                    # 更新模型名称
                    update_sql = """
                    UPDATE models
                    SET model_name = %s, updated_at = NOW()
                    WHERE user_id = %s AND model_name = %s AND is_deleted = FALSE
                    """
                    cursor.execute(update_sql, (new_model_name, user_id, old_model_name))
                    connection.commit()

                return Response({
                    'status': 'success',
                    'message': '模型名称修改成功',
                    'old_model_name': old_model_name,
                    'new_model_name': new_model_name
                }, status=status.HTTP_200_OK)

            finally:
                connection.close()

        except json.JSONDecodeError:
            return Response(
                {'error': '无效的 JSON 格式'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'修改模型名称失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DeleteTaskView(APIView):
    """删除任务接口"""

    def delete(self, request, task_id: str):
        """删除指定任务的所有数据"""
        try:
            import shutil

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
                # 查询任务信息
                task_sql = """
                SELECT t.id, t.status, u.output_base_path
                FROM tasks t
                JOIN users u ON t.user_id = u.id
                WHERE t.task_id = %s AND t.is_deleted = FALSE AND u.is_deleted = FALSE
                """
                cursor.execute(task_sql, (task_id,))
                task_info = cursor.fetchone()

                if not task_info:
                    return Response(
                        {'error': '任务不存在'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # 检查任务是否正在处理中
                if task_info['status'] == 'processing':
                    return Response(
                        {'error': '任务正在处理中，无法删除'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # 软删除任务
                update_sql = """
                UPDATE tasks
                SET is_deleted = TRUE, deleted_at = NOW()
                WHERE task_id = %s
                """
                cursor.execute(update_sql, (task_id,))
                connection.commit()

                # 删除任务目录
                output_base_path = Path(task_info['output_base_path'])
                task_dir = output_base_path / 'tasks' / task_id

                if task_dir.exists():
                    shutil.rmtree(task_dir)

                return Response({
                    'message': '任务已成功删除',
                    'task_id': task_id
                }, status=status.HTTP_200_OK)

        finally:
            connection.close()


class ExportDataView(APIView):
    """导出数据接口（CSV 或 JSON）"""

    def get(self, request, task_id: str):
        """导出任务数据为 CSV 或 JSON 格式"""
        try:
            import csv
            import io

            print(f"{get_thread_prefix(task_id)} ExportDataView called")
            print(f"{get_thread_prefix(task_id)} Request query params: {dict(request.GET)}")

            # 获取导出格式（使用 export_format 避免与 DRF 的 format 参数冲突）
            format_type = request.GET.get('export_format', 'csv').lower()
            print(f"{get_thread_prefix(task_id)} Format type: {format_type}")

            if format_type not in ['csv', 'json']:
                print(f"{get_thread_prefix(task_id)} Invalid format: {format_type}")
                return Response(
                    {'error': '不支持的格式，支持的格式: csv, json'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 从数据库查询任务信息和用户的 output_base_path
            connection = pymysql.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 3306)),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'cell_tracking'),
                cursorclass=pymysql.cursors.DictCursor
            )

            try:
                with connection.cursor() as cursor:
                    # 查询任务信息和用户的 output_base_path
                    task_sql = """
                    SELECT u.output_base_path, t.status
                    FROM tasks t
                    JOIN users u ON t.user_id = u.id
                    WHERE t.task_id = %s AND t.is_deleted = FALSE AND u.is_deleted = FALSE
                    """
                    cursor.execute(task_sql, (task_id,))
                    task_info = cursor.fetchone()

                    if not task_info:
                        return Response(
                            {'error': '任务不存在'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    if task_info['status'] != 'completed':
                        return Response(
                            {'error': '任务尚未完成'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    output_base_path = Path(task_info['output_base_path'])
                    json_path = output_base_path / 'tasks' / task_id / 'result.json'
                    print(f"{get_thread_prefix(task_id)} JSON path: {json_path}")
                    print(f"{get_thread_prefix(task_id)} JSON exists: {json_path.exists()}")

                    if not json_path.exists():
                        print(f"{get_thread_prefix(task_id)} JSON file not found at: {json_path}")
                        return Response(
                            {'error': '结果不存在'},
                            status=status.HTTP_404_NOT_FOUND
                        )
            finally:
                connection.close()

            with open(json_path, 'r', encoding='utf-8') as f:
                result = json.load(f)
            print(f"{get_thread_prefix(task_id)} Loaded result with {len(result.get('tracking_data', []))} tracking records")

            if format_type == 'json':
                print(f"{get_thread_prefix(task_id)} Exporting JSON")
                # 导出 JSON
                response = Response(
                    json.dumps(result, ensure_ascii=False, indent=2),
                    content_type='application/json'
                )
                response['Content-Disposition'] = f'attachment; filename="analysis_{task_id}.json"'
                return response

            elif format_type == 'csv':
                print(f"{get_thread_prefix(task_id)} Exporting CSV")
                # 导出 CSV
                output = io.StringIO()
                writer = csv.writer(output)

                # 写入表头
                writer.writerow([
                    'track_id',
                    'frame',
                    'bb_left',
                    'bb_top',
                    'bb_width',
                    'bb_height',
                    'conf',
                    'class',
                    'visibility'
                ])

                # 写入数据（使用实际的 tracking_data 结构）
                rows_written = 0
                for record in result.get('tracking_data', []):
                    writer.writerow([
                        record.get('track_id', ''),
                        record.get('frame', ''),
                        record.get('bb_left', ''),
                        record.get('bb_top', ''),
                        record.get('bb_width', ''),
                        record.get('bb_height', ''),
                        record.get('conf', ''),
                        record.get('class', ''),
                        record.get('visibility', '')
                    ])
                    rows_written += 1

                print(f"{get_thread_prefix(task_id)} CSV rows written: {rows_written}")

                # 创建响应
                csv_content = output.getvalue()
                print(f"{get_thread_prefix(task_id)} CSV content length: {len(csv_content)}")

                response = HttpResponse(
                    csv_content,
                    content_type='text/csv; charset=utf-8'
                )
                response['Content-Disposition'] = f'attachment; filename="analysis_{task_id}.csv"'
                return response

        except Exception as e:
            print(f"{get_thread_prefix(task_id)} Export error: {str(e)}")
            import traceback
            print(f"{get_thread_prefix(task_id)} Traceback: {traceback.format_exc()}")
            return Response(
                {'error': f'导出失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ModelUploadView(APIView):
    """上传模型接口"""

    def post(self, request):
        """上传模型文件到 models 目录"""
        try:
            model_file = request.FILES.get('model')
            username = request.POST.get('username')

            if not model_file:
                return Response(
                    {'error': '未找到模型文件'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not username:
                return Response(
                    {'error': '未提供用户名'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 验证文件类型
            if not model_file.name.endswith('.pt'):
                return Response(
                    {'error': '只支持 .pt 格式的模型文件'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 查询用户信息
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
                    # 查询用户
                    sql = "SELECT id, model_base_path FROM users WHERE username = %s AND is_deleted = FALSE"
                    cursor.execute(sql, (username,))
                    user = cursor.fetchone()

                    if not user:
                        return Response(
                            {'error': '用户不存在'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    user_id = user['id']
                    model_base_path = user['model_base_path']

                # 使用用户配置的绝对路径
                models_dir = Path(model_base_path)

                # 验证路径是否为绝对路径
                if not models_dir.is_absolute():
                    return Response(
                        {'error': f'模型路径必须是绝对路径，当前路径: {model_base_path}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # 确保目录存在
                try:
                    models_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    return Response(
                        {'error': f'无法创建模型目录 {model_base_path}: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                # 保存模型文件
                model_path = models_dir / model_file.name

                # 如果文件已存在，询问是否覆盖（这里简单处理为覆盖）
                with open(model_path, 'wb') as f:
                    for chunk in model_file.chunks():
                        f.write(chunk)

                # 插入或更新数据库记录
                with connection.cursor() as cursor:
                    model_name = model_file.name.rsplit('.', 1)[0]  # 去掉后缀名
                    
                    # 检查模型是否已存在
                    check_sql = """
                    SELECT id, is_deleted FROM models
                    WHERE user_id = %s AND model_name = %s
                    """
                    cursor.execute(check_sql, (user_id, model_name))
                    existing_model = cursor.fetchone()

                    if existing_model:
                        # 模型已存在
                        if existing_model['is_deleted']:
                            # 已软删除，恢复记录
                            update_sql = """
                            UPDATE models
                            SET model_path = %s, is_deleted = FALSE, updated_at = NOW()
                            WHERE id = %s
                            """
                            cursor.execute(update_sql, (model_file.name, existing_model['id']))
                            connection.commit()
                            message = '模型已恢复'
                        else:
                            # 未删除，返回错误
                            return Response(
                                {'error': f'模型 "{model_name}" 已存在，请先删除旧版本再上传'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    else:
                        # 模型不存在，插入新记录
                        insert_sql = """
                        INSERT INTO models (user_id, model_name, model_path, created_at, updated_at, is_deleted)
                        VALUES (%s, %s, %s, NOW(), NOW(), FALSE)
                        """
                        cursor.execute(insert_sql, (user_id, model_name, model_file.name))
                        connection.commit()
                        message = '模型上传成功'

                # 返回成功响应
                return Response({
                    'status': 'success',
                    'message': message,
                    'model_name': model_name,
                    'model_path': model_file.name,
                    'model_size_mb': round(model_file.size / (1024 * 1024), 2)
                }, status=status.HTTP_201_CREATED)

            finally:
                connection.close()

        except Exception as e:
            return Response(
                {'error': f'上传失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginView(APIView):
    """登录验证接口"""

    def post(self, request):
        """验证用户名和密码"""
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return Response(
                    {'error': '用户名和密码不能为空'},
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
                    # 查询用户
                    sql = "SELECT * FROM users WHERE username = %s AND is_deleted = FALSE"
                    cursor.execute(sql, (username,))
                    user = cursor.fetchone()

                    if not user:
                        return Response(
                            {'error': '用户名或密码错误'},
                            status=status.HTTP_401_UNAUTHORIZED
                        )

                    # 验证密码
                    password_bytes = password.encode('utf-8')
                    hashed_password = user['password_hash'].encode('utf-8')

                    if not bcrypt.checkpw(password_bytes, hashed_password):
                        return Response(
                            {'error': '用户名或密码错误'},
                            status=status.HTTP_401_UNAUTHORIZED
                        )

                    # 登录成功
                    return Response({
                        'status': 'success',
                        'message': '登录成功',
                        'user': {
                            'id': user['id'],
                            'username': user['username'],
                            'email': user['email'],
                            'dark_mode': user['dark_mode'],
                            'model_base_path': user['model_base_path'],
                            'output_base_path': user['output_base_path']
                        }
                    }, status=status.HTTP_200_OK)

            finally:
                connection.close()

        except json.JSONDecodeError:
            return Response(
                {'error': '无效的 JSON 格式'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'登录失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdateUserView(APIView):
    """更新用户信息接口"""

    def post(self, request):
        """更新用户信息（如 dark_mode）"""
        try:
            data = json.loads(request.body)
            username = data.get('username')
            dark_mode = data.get('dark_mode')

            if not username:
                return Response(
                    {'error': '用户名不能为空'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if dark_mode is None:
                return Response(
                    {'error': 'dark_mode 不能为空'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 导入 sql 模块
            import sys
            from pathlib import Path
            scripts_dir = Path(__file__).parent.parent / 'scripts'
            sys.path.insert(0, str(scripts_dir))
            from sql import DatabaseOperator

            with DatabaseOperator() as db:
                # 更新用户的 dark_mode
                update_sql = """
                UPDATE users
                SET dark_mode = %s, updated_at = NOW()
                WHERE username = %s AND is_deleted = FALSE
                """
                success = db.execute_update(update_sql, (dark_mode, username))

                if success:
                    return Response({
                        'status': 'success',
                        'message': '用户信息更新成功'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {'error': '更新失败，用户不存在'},
                        status=status.HTTP_404_NOT_FOUND
                    )

        except json.JSONDecodeError:
            return Response(
                {'error': '无效的 JSON 格式'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'更新用户信息失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdateUserPathsView(APIView):
    """更新用户路径配置接口"""

    def post(self, request):
        """更新用户的 model_base_path 和 output_base_path"""
        try:
            data = json.loads(request.body)
            username = data.get('username')
            model_base_path = data.get('model_base_path')
            output_base_path = data.get('output_base_path')

            if not username:
                return Response(
                    {'error': '用户名不能为空'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if model_base_path is None or output_base_path is None:
                return Response(
                    {'error': 'model_base_path 和 output_base_path 不能为空'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 导入 sql 模块
            import sys
            from pathlib import Path
            scripts_dir = Path(__file__).parent.parent / 'scripts'
            sys.path.insert(0, str(scripts_dir))
            from sql import DatabaseOperator

            with DatabaseOperator() as db:
                # 更新用户的路径配置
                update_sql = """
                UPDATE users
                SET model_base_path = %s, output_base_path = %s, updated_at = NOW()
                WHERE username = %s AND is_deleted = FALSE
                """
                success = db.execute_update(update_sql, (model_base_path, output_base_path, username))

                if success:
                    return Response({
                        'status': 'success',
                        'message': '路径配置更新成功'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {'error': '更新失败，用户不存在'},
                        status=status.HTTP_404_NOT_FOUND
                    )

        except json.JSONDecodeError:
            return Response(
                {'error': '无效的 JSON 格式'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'更新路径配置失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )