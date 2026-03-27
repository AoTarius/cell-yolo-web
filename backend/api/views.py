import os
import json
import uuid
import threading
import bcrypt
import io
from pathlib import Path
from datetime import datetime

from django.conf import settings
from django.http import JsonResponse, FileResponse, HttpResponseNotFound, HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.db import models
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from .models import Cell, Task, User
from django.http import JsonResponse
from rest_framework.decorators import api_view

from .services.video_processor import VideoProcessor
from .services.free_plot_executor import (
    ALLOWED_IMPORT_MODULES,
    execute_plot_code,
    warmup_plot_worker,
    validate_plot_code,
)


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
                    cursor.execute(model_sql, (user_id, model_name))
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
                    as_attachment=False
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
                    as_attachment=False
                )

        finally:
            connection.close()


class FrameImageView(APIView):
    """获取指定帧的图片接口"""

    def get(self, request, task_id, frame_number):
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
                SELECT u.output_base_path
                FROM tasks t
                JOIN users u ON t.user_id = u.id
                WHERE t.task_id = %s AND t.is_deleted = FALSE AND u.is_deleted = FALSE
                """
                cursor.execute(task_sql, (task_id,))
                task_info = cursor.fetchone()

                if not task_info:
                    return HttpResponseNotFound('任务不存在')

                output_base_path = Path(task_info['output_base_path'])

                # 构建帧图片路径：{output_base_path}/tasks/{task_id}/output/t{frame_number:04d}.png
                frame_filename = f"t{frame_number:04d}.png"
                frame_path = output_base_path / 'tasks' / task_id / 'output' / frame_filename

                if not frame_path.exists():
                    return HttpResponseNotFound(f'帧 {frame_number} 不存在')

                # 返回图片文件
                return FileResponse(
                    open(frame_path, 'rb'),
                    content_type='image/png',
                    as_attachment=False
                )

        finally:
            connection.close()


class TaskListView(APIView):
    """获取所有任务列表接口"""

    def get(self, request):
        """获取所有任务（包括已完成和处理中）的列表"""
        username = request.GET.get('username')

        # 获取排序参数
        sort_by = request.GET.get('sort_by', '[]')
        try:
            import json
            sort_conditions = json.loads(sort_by)
            if not isinstance(sort_conditions, list):
                sort_conditions = []
        except (json.JSONDecodeError, ValueError):
            sort_conditions = []

        # 构建排序字段映射
        field_mapping = {
            'createdAt': 't.created_at',
            'updatedAt': 't.updated_at',
            'taskName': 't.task_name',
            'modelName': 'm.model_name'
        }

        # 构建 ORDER BY 子句
        order_by_clauses = []
        for condition in sort_conditions:
            field = condition.get('field')
            direction = condition.get('direction', 'desc')

            if field in field_mapping:
                db_field = field_mapping[field]
                direction_upper = direction.upper()
                order_by_clauses.append(f"{db_field} {direction_upper}")

        # 默认排序（如果没有提供排序条件）
        if not order_by_clauses:
            order_by_clauses.append('t.created_at DESC')

        order_by_sql = ', '.join(order_by_clauses)

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
                    task_sql = f"""
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
                    ORDER BY {order_by_sql}
                    """
                    cursor.execute(task_sql, (username,))
                else:
                    task_sql = f"""
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
                    ORDER BY {order_by_sql}
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
                    'default': 'best_split'
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

                    # 检查是否有任务正在使用该模型
                    check_tasks_sql = """
                    SELECT COUNT(*) as task_count
                    FROM tasks t
                    WHERE t.model_id = (
                        SELECT id FROM models WHERE user_id = %s AND model_name = %s AND is_deleted = FALSE
                    ) AND t.is_deleted = FALSE AND t.status IN ('pending', 'processing')
                    """
                    cursor.execute(check_tasks_sql, (user_id, model_name))
                    task_count = cursor.fetchone()

                    if task_count['task_count'] > 0:
                        return Response(
                            {'error': f'无法删除：有 {task_count["task_count"]} 个任务正在使用该模型'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

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


class RenameTaskView(APIView):
    """修改任务名称接口"""

    def post(self, request):
        """修改任务的名称（只修改数据库中的task_name）"""
        try:
            data = json.loads(request.body)
            username = data.get('username')
            task_id = data.get('task_id')
            new_task_name = data.get('new_task_name')

            if not username:
                return Response(
                    {'error': '未提供用户名'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not task_id:
                return Response(
                    {'error': '未提供任务ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not new_task_name:
                return Response(
                    {'error': '未提供新任务名称'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 验证新名称不为空
            if not new_task_name.strip():
                return Response(
                    {'error': '新任务名称不能为空'},
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

                    # 查询原任务是否存在
                    check_old_sql = """
                    SELECT id, task_name FROM tasks
                    WHERE user_id = %s AND task_id = %s AND is_deleted = FALSE
                    """
                    cursor.execute(check_old_sql, (user_id, task_id))
                    old_task = cursor.fetchone()

                    if not old_task:
                        return Response(
                            {'error': f'任务 {task_id} 不存在'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    # 更新任务名称
                    update_sql = """
                    UPDATE tasks
                    SET task_name = %s, updated_at = NOW()
                    WHERE user_id = %s AND task_id = %s AND is_deleted = FALSE
                    """
                    cursor.execute(update_sql, (new_task_name, user_id, task_id))
                    connection.commit()

                return Response({
                    'status': 'success',
                    'message': '任务名称修改成功',
                    'task_id': task_id,
                    'old_task_name': old_task['task_name'],
                    'new_task_name': new_task_name
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
                {'error': f'修改任务名称失败: {str(e)}'},
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

                    # 软删除任务关联的细胞数据（先删除子表）
                    # 注意：cells.task_id 是外键，指向 tasks.id (INTEGER)
                    update_cells_sql = """
                    UPDATE cells
                    SET is_deleted = TRUE, deleted_at = NOW()
                    WHERE task_id = %s AND is_deleted = FALSE
                    """
                    cursor.execute(update_cells_sql, (task_info['id'],))

                    # 软删除任务状态
                    # 注意：task_status.task_id 是外键，指向 tasks.task_id (UUID字符串)
                    update_status_sql = """
                    UPDATE task_status
                    SET is_deleted = TRUE, deleted_at = NOW()
                    WHERE task_id = %s AND is_deleted = FALSE
                    """
                    cursor.execute(update_status_sql, (task_id,))

                    # 软删除任务（最后删除主表）
                    # 注意：tasks.task_id 是 UUID 字符串
                    update_task_sql = """
                    UPDATE tasks
                    SET is_deleted = TRUE, deleted_at = NOW()
                    WHERE task_id = %s AND is_deleted = FALSE
                    """
                    cursor.execute(update_task_sql, (task_id,))

                    # 提交事务
                    connection.commit()

                    # 删除任务目录
                    output_base_path = Path(task_info['output_base_path'])
                    task_dir = output_base_path / 'tasks' / task_id

                    if task_dir.exists():
                        shutil.rmtree(task_dir)

                return Response({
                    'status': 'success',
                    'message': '任务已删除',
                    'task_id': task_id
                }, status=status.HTTP_200_OK)

            finally:
                connection.close()

        except pymysql.Error as e:
            return Response(
                {'error': f'数据库连接失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExportDataView(APIView):
    """导出数据接口（CSV 或 JSON）"""

    def get(self, request, task_id: str):
        """导出任务数据为 CSV 或 JSON 格式"""
        try:
            import csv
            import io

            # 获取导出格式（使用 export_format 避免与 DRF 的 format 参数冲突）
            format_type = request.GET.get('export_format', 'csv').lower()

            if format_type not in ['csv', 'json']:
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
                    task_dir = output_base_path / 'tasks' / task_id

                    if format_type == 'csv':
                        # CSV 格式：直接返回 processed_cells 文件
                        csv_filename = f"processed_cells_{task_id}.csv"
                        csv_path = task_dir / csv_filename

                        if not csv_path.exists():
                            return Response(
                                {'error': f'CSV 文件不存在: {csv_filename}'},
                                status=status.HTTP_404_NOT_FOUND
                            )

                        # 返回 CSV 文件
                        with open(csv_path, 'rb') as f:
                            response = HttpResponse(
                                f.read(),
                                content_type='text/csv; charset=utf-8'
                            )
                            response['Content-Disposition'] = f'attachment; filename="{csv_filename}"'
                            return response

                    elif format_type == 'json':
                        # JSON 格式：读取 result.json 并返回
                        json_path = task_dir / 'result.json'

                        if not json_path.exists():
                            return Response(
                                {'error': '结果文件不存在'},
                                status=status.HTTP_404_NOT_FOUND
                            )

                        with open(json_path, 'r', encoding='utf-8') as f:
                            result = json.load(f)

                        response = Response(
                            json.dumps(result, ensure_ascii=False, indent=2),
                            content_type='application/json'
                        )
                        response['Content-Disposition'] = f'attachment; filename="analysis_{task_id}.json"'
                        return response

            finally:
                connection.close()

        except Exception as e:
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

                    # 检查模型是否已存在（包括软删除的记录）
                    check_sql = """
                    SELECT id, is_deleted, model_path FROM models
                    WHERE user_id = %s AND model_name = %s
                    """
                    cursor.execute(check_sql, (user_id, model_name))
                    existing_model = cursor.fetchone()

                    if existing_model:
                        # 模型已存在
                        if existing_model['is_deleted']:
                            # 已软删除，检查路径是否相同
                            if existing_model['model_path'] == model_file.name:
                                # 路径相同，恢复记录
                                update_sql = """
                                UPDATE models
                                SET is_deleted = FALSE, updated_at = NOW(), model_name = %s
                                WHERE id = %s
                                """
                                cursor.execute(update_sql, (model_name, existing_model['id']))
                                connection.commit()
                                message = '模型已恢复'
                            else:
                                # 路径不同，创建新记录
                                insert_sql = """
                                INSERT INTO models (user_id, model_name, model_path, created_at, updated_at, is_deleted)
                                VALUES (%s, %s, %s, NOW(), NOW(), FALSE)
                                """
                                cursor.execute(insert_sql, (user_id, model_name, model_file.name))
                                connection.commit()
                                message = '模型上传成功'
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


class RegisterView(APIView):
    """用户注册接口"""

    def post(self, request):
        """创建新用户"""
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            model_base_path = data.get('model_base_path')
            output_base_path = data.get('output_base_path')

            # 验证必填字段
            if not username or not password or not model_base_path or not output_base_path:
                return Response(
                    {'error': '用户名、密码、模型存储路径和任务存储路径不能为空'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 验证密码长度
            if len(password) < 6:
                return Response(
                    {'error': '密码长度至少为6位'},
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
                    # 检查用户名是否已存在
                    check_sql = "SELECT id FROM users WHERE username = %s AND is_deleted = FALSE"
                    cursor.execute(check_sql, (username,))
                    existing_user = cursor.fetchone()

                    if existing_user:
                        return Response(
                            {'error': '用户名已存在'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # 使用 bcrypt 哈希密码
                    password_bytes = password.encode('utf-8')
                    salt = bcrypt.gensalt()
                    hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

                    # 创建新用户
                    insert_sql = """
                    INSERT INTO users (username, password_hash, model_base_path, output_base_path, dark_mode, created_at, updated_at, is_deleted, deleted_at)
                    VALUES (%s, %s, %s, %s, TRUE, NOW(), NOW(), FALSE, NULL)
                    """
                    cursor.execute(insert_sql, (username, hashed_password, model_base_path, output_base_path))
                    connection.commit()

                    # 获取新创建的用户信息
                    user_id = cursor.lastrowid
                    select_sql = "SELECT * FROM users WHERE id = %s"
                    cursor.execute(select_sql, (user_id,))
                    new_user = cursor.fetchone()

                    return Response({
                        'status': 'success',
                        'message': '注册成功',
                        'user': {
                            'id': new_user['id'],
                            'username': new_user['username'],
                            'email': new_user['email'],
                            'dark_mode': new_user['dark_mode'],
                            'model_base_path': new_user['model_base_path'],
                            'output_base_path': new_user['output_base_path']
                        }
                    }, status=status.HTTP_201_CREATED)

            finally:
                connection.close()

        except json.JSONDecodeError:
            return Response(
                {'error': '无效的 JSON 格式'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'注册失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
# 获取细胞数据接口
@api_view(['GET'])
def get_cells_by_task(request, task_id):
    """
    根据 task_id 查询 cells 表中的所有数据。
    """
    try:
        # 先根据 task_id 查找 Task 对象
        # Task 模型的主键是整数 id，task_id 是字符串
        task_obj = Task.objects.filter(task_id=task_id, is_deleted=False).first()
        
        if not task_obj:
            return JsonResponse({"success": False, "error": "Task not found"}, status=404)
        
        # 使用 Task 对象的主键来查询 Cell 数据
        cells = Cell.objects.filter(task=task_obj.id, is_deleted=False)
        
        # 序列化数据
        data = [
            {
                "frame": cell.frame,
                "track_id": cell.track_id,
                "bb_left": cell.bb_left,
                "bb_top": cell.bb_top,
                "bb_width": cell.bb_width,
                "bb_height": cell.bb_height,
                "conf": cell.conf,
                "class_id": cell.class_id,
                "visibility": cell.visibility,
                "area": cell.area,
                "speed": cell.speed,
                "tracking_persistence": cell.tracking_persistence,
                "metrics_json": cell.metrics_json,
            }
            for cell in cells
        ]

        return JsonResponse({"success": True, "data": data}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


class Trajectory3DImageView(APIView):
    """使用后端 Python 生成 3D 轨迹图（PNG）"""

    def get(self, request, task_id):
        try:
            task_obj = Task.objects.filter(task_id=task_id, is_deleted=False).first()
            if not task_obj:
                return JsonResponse({"success": False, "error": "Task not found"}, status=404)

            track_ids_param = (request.GET.get('track_ids') or '').strip()
            track_ids = []
            if track_ids_param:
                for token in track_ids_param.split(','):
                    token = token.strip()
                    if token.isdigit():
                        track_ids.append(int(token))

            cells_qs = Cell.objects.filter(task=task_obj.id, is_deleted=False)
            if track_ids:
                cells_qs = cells_qs.filter(track_id__in=track_ids)
            cells_qs = cells_qs.order_by('track_id', 'frame')

            grouped_tracks = defaultdict(list)
            for cell in cells_qs:
                metrics = cell.metrics_json or {}
                center = metrics.get('center') or {}
                cx = center.get('cx')
                cy = center.get('cy')

                x = float(cx) if cx is not None else float(cell.bb_left + cell.bb_width / 2)
                y = float(cy) if cy is not None else float(cell.bb_top + cell.bb_height / 2)
                z = float(cell.frame)
                grouped_tracks[int(cell.track_id)].append((x, y, z))

            if not grouped_tracks:
                return JsonResponse({"success": False, "error": "No trajectory data"}, status=404)

            fig = plt.figure(figsize=(10, 7), dpi=160)
            ax = fig.add_subplot(111, projection='3d')
            fig.patch.set_facecolor('white')

            max_tracks = 80
            sorted_items = sorted(grouped_tracks.items(), key=lambda kv: len(kv[1]), reverse=True)[:max_tracks]
            colors = plt.cm.tab20(np.linspace(0, 1, max(2, len(sorted_items))))

            for idx, (track_id, points) in enumerate(sorted_items):
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                zs = [p[2] for p in points]
                ax.plot(xs, ys, zs, color=colors[idx % len(colors)], linewidth=1.2, alpha=0.9)

            ax.set_title('3D Cell Trajectories', fontsize=12)
            ax.set_xlabel('X Position (μm)', fontsize=10, labelpad=8)
            ax.set_ylabel('Y Position (μm)', fontsize=10, labelpad=8)
            ax.set_zlabel('Time (frame)', fontsize=10, labelpad=8)

            ax.grid(True, linestyle='--', linewidth=0.6, alpha=0.35)
            ax.xaxis.pane.set_facecolor((1, 1, 1, 1))
            ax.yaxis.pane.set_facecolor((1, 1, 1, 1))
            ax.zaxis.pane.set_facecolor((1, 1, 1, 1))

            plt.tight_layout()

            # 同时落盘保存一份，便于后续复用/审计
            output_base_path = Path(task_obj.user.output_base_path)
            plot_dir = output_base_path / 'tasks' / task_id / 'plots'
            plot_dir.mkdir(parents=True, exist_ok=True)
            saved_png_path = plot_dir / 'trajectory_3d.png'
            fig.savefig(saved_png_path, format='png', facecolor='white', bbox_inches='tight')

            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', facecolor='white', bbox_inches='tight')
            plt.close(fig)
            buffer.seek(0)

            response = HttpResponse(buffer.getvalue(), content_type='image/png')
            response['Cache-Control'] = 'no-store, max-age=0'
            response['X-Trajectory-Image-Path'] = str(saved_png_path)
            return response

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


class FreePlotRunView(APIView):
    """自由绘图执行接口（MVP 安全版）"""

    MAX_ROWS = 20000

    def _build_task_data(self, task_obj: Task) -> dict:
        cells_qs = (
            Cell.objects.filter(task=task_obj.id, is_deleted=False)
            .order_by('frame', 'track_id')[: self.MAX_ROWS]
        )

        rows = []
        for cell in cells_qs:
            center = (cell.metrics_json or {}).get('center') or {}
            shape = (cell.metrics_json or {}).get('shape') or {}
            motion = (cell.metrics_json or {}).get('motion') or {}
            rows.append({
                'frame': int(cell.frame),
                'track_id': int(cell.track_id),
                'area': float(cell.area or 0),
                'speed': float(cell.speed or 0),
                'bb_left': float(cell.bb_left or 0),
                'bb_top': float(cell.bb_top or 0),
                'bb_width': float(cell.bb_width or 0),
                'bb_height': float(cell.bb_height or 0),
                'center_x': float(center.get('cx') or 0),
                'center_y': float(center.get('cy') or 0),
                'perimeter': float(shape.get('perimeter') or 0),
                'circularity': float(shape.get('circularity') or 0),
                'aspect_ratio': float(shape.get('aspect_ratio') or 0),
                'distance': float(motion.get('distance') or 0),
                'migration_speed': float(motion.get('migration_speed') or 0),
                'mean_square_displacement': float(motion.get('mean_square_displacement') or 0),
            })

        return {
            'task_id': task_obj.task_id,
            'task_name': task_obj.task_name,
            'video_name': task_obj.video.video_name if task_obj.video_id else '',
            'row_count': len(rows),
            'truncated': len(rows) >= self.MAX_ROWS,
            'rows': rows,
        }

    def post(self, request):
        try:
            data = json.loads(request.body or '{}')
            username = str(data.get('username') or '').strip()
            task_id = str(data.get('task_id') or '').strip()
            code = str(data.get('code') or '')

            if not username:
                return JsonResponse({'success': False, 'error': '缺少用户名'}, status=400)
            if not task_id:
                return JsonResponse({'success': False, 'error': '缺少 task_id'}, status=400)

            task_obj = (
                Task.objects
                .select_related('video', 'user')
                .filter(task_id=task_id, is_deleted=False, user__username=username, user__is_deleted=False)
                .first()
            )
            if not task_obj:
                return JsonResponse({'success': False, 'error': '任务不存在或无权限访问'}, status=404)

            validation_errors = validate_plot_code(code)
            if validation_errors:
                return JsonResponse(
                    {
                        'success': False,
                        'error': '代码未通过安全检查',
                        'validation_errors': validation_errors,
                        'whitelist': sorted(ALLOWED_IMPORT_MODULES),
                    },
                    status=400,
                )

            task_data = self._build_task_data(task_obj)
            result = execute_plot_code(code, task_data)

            if not result.get('success'):
                return JsonResponse(
                    {
                        'success': False,
                        'error': result.get('error') or '执行失败',
                        'logs': result.get('logs', ''),
                        'whitelist': sorted(ALLOWED_IMPORT_MODULES),
                    },
                    status=400,
                )

            return JsonResponse(
                {
                    'success': True,
                    'image_base64': result.get('image_base64', ''),
                    'logs': result.get('logs', ''),
                    'task_data_meta': {
                        'task_id': task_data['task_id'],
                        'row_count': task_data['row_count'],
                        'truncated': task_data['truncated'],
                    },
                    'whitelist': sorted(ALLOWED_IMPORT_MODULES),
                },
                status=200,
            )
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': '无效的 JSON 请求体'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class FreePlotWarmupView(APIView):
    """自由绘图环境预热接口"""

    def post(self, request):
        try:
            data = json.loads(request.body or '{}')
            username = str(data.get('username') or '').strip()
            if not username:
                return JsonResponse({'success': False, 'error': '缺少用户名'}, status=400)

            # 仅允许已存在用户触发预热，避免匿名滥用
            user_exists = Task.objects.filter(user__username=username, user__is_deleted=False).exists()
            if not user_exists:
                return JsonResponse({'success': False, 'error': '用户不存在或无权限'}, status=403)

            result = warmup_plot_worker()
            if not result.get('success'):
                return JsonResponse(
                    {
                        'success': False,
                        'error': result.get('error', '预热失败'),
                        'whitelist': sorted(ALLOWED_IMPORT_MODULES),
                    },
                    status=400,
                )

            return JsonResponse(
                {
                    'success': True,
                    'message': '绘图环境已预热。',
                    'whitelist': sorted(ALLOWED_IMPORT_MODULES),
                },
                status=200,
            )
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': '无效的 JSON 请求体'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class FreePlotExamplesView(APIView):
    """自由绘图案例列表与内容读取接口"""

    @staticmethod
    def _examples_dir() -> Path:
        # backend/backend/settings.py 的 BASE_DIR 指向 backend 目录，这里回到项目根目录
        return Path(settings.BASE_DIR).parent / 'docs' / 'examples'

    @staticmethod
    def _is_safe_example_name(name: str) -> bool:
        if not name or '/' in name or '\\' in name:
            return False
        if not name.endswith('.py'):
            return False
        allowed = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-')
        return all(ch in allowed for ch in name)

    def get(self, request, example_name=None):
        username = str(request.GET.get('username') or '').strip()
        if not username:
            return JsonResponse({'success': False, 'error': '缺少用户名'}, status=400)

        user_exists = User.objects.filter(username=username, is_deleted=False).exists()
        if not user_exists:
            return JsonResponse({'success': False, 'error': '用户不存在或无权限'}, status=403)

        examples_dir = self._examples_dir()
        if not examples_dir.exists() or not examples_dir.is_dir():
            return JsonResponse({'success': False, 'error': '案例目录不存在'}, status=404)

        if not example_name:
            files = sorted([p.name for p in examples_dir.glob('*.py') if p.is_file()])
            return JsonResponse({'success': True, 'examples': files}, status=200)

        if not self._is_safe_example_name(example_name):
            return JsonResponse({'success': False, 'error': '非法案例名称'}, status=400)

        target = examples_dir / example_name
        if not target.exists() or not target.is_file():
            return JsonResponse({'success': False, 'error': '案例不存在'}, status=404)

        try:
            content = target.read_text(encoding='utf-8')
        except Exception:
            return JsonResponse({'success': False, 'error': '案例读取失败'}, status=500)

        return JsonResponse(
            {
                'success': True,
                'name': example_name,
                'content': content,
            },
            status=200,
        )


# 获取单个细胞详细数据接口
@api_view(['GET'])
def get_cell_detail(request, task_id, track_id):
    """
    根据 task_id 和 track_id 查询指定细胞的详细数据（所有帧）。
    """
    try:
        # 先根据 task_id 查找 Task 对象
        task_obj = Task.objects.filter(task_id=task_id, is_deleted=False).first()
        
        if not task_obj:
            return JsonResponse({"success": False, "error": "Task not found"}, status=404)
        
        # 查询指定细胞的每一帧数据
        cells = Cell.objects.filter(task=task_obj.id, track_id=track_id, is_deleted=False).order_by('frame')

        if not cells.exists():
            return JsonResponse({"success": False, "error": "Cell not found"}, status=404)

        # 序列化数据
        data = [
            {
                "frame": cell.frame,
                "track_id": cell.track_id,
                "bb_left": cell.bb_left,
                "bb_top": cell.bb_top,
                "bb_width": cell.bb_width,
                "bb_height": cell.bb_height,
                "conf": cell.conf,
                "class_id": cell.class_id,
                "visibility": cell.visibility,
                "area": cell.area,
                "speed": cell.speed,
                "tracking_persistence": cell.tracking_persistence,
                "metrics_json": cell.metrics_json,
            }
            for cell in cells
        ]

        return JsonResponse({"success": True, "data": data}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


class ExportTaskDataView(APIView):
    """导出任务数据包接口"""

    def get(self, request, task_id):
        """将 task_id 对应的文件夹打包成 zip 并下载"""
        try:
            import zipfile
            import io

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
                # 查询任务信息和用户的 output_base_path，以及video_id和video_name
                task_sql = """
                SELECT u.output_base_path, t.status, t.task_name, t.video_id, v.video_name, v.video_path
                FROM tasks t
                JOIN users u ON t.user_id = u.id
                JOIN videos v ON t.video_id = v.id
                WHERE t.task_id = %s AND t.is_deleted = FALSE AND u.is_deleted = FALSE AND v.is_deleted = FALSE
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
                        {'error': '任务尚未完成，无法导出'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                output_base_path = Path(task_info['output_base_path'])
                task_dir = output_base_path / 'tasks' / task_id

                if not task_dir.exists():
                    return Response(
                        {'error': f'任务文件夹不存在: {task_dir}'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # 创建内存中的 zip 文件
                zip_buffer = io.BytesIO()

                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # 遍历任务文件夹中的所有文件和子文件夹
                    for root, dirs, files in os.walk(task_dir):
                        for file in files:
                            file_path = Path(root) / file
                            # 计算相对路径，去掉 tasks/{task_id} 层级
                            arcname = file_path.relative_to(task_dir)
                            zip_file.write(file_path, arcname)

                    # 添加原视频到 original/ 文件夹
                    video_path_relative = task_info['video_path']
                    if video_path_relative:
                        original_video_path = output_base_path / video_path_relative
                        if original_video_path.exists():
                            # 将原视频放到 original/ 目录下
                            original_arcname = f"original/{task_info['video_name']}"
                            zip_file.write(original_video_path, original_arcname)

                # 重置指针到文件开头
                zip_buffer.seek(0)

                # 生成文件名
                task_name = task_info['task_name'] or task_id
                safe_task_name = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in task_name)
                filename = f"{safe_task_name}_data_package.zip"

                # 返回 zip 文件
                response = HttpResponse(zip_buffer.read(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response

        except Exception as e:
            return Response(
                {'error': f'导出数据包失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        finally:
            connection.close()


class ImportDataPackageView(APIView):
    """导入数据包接口"""

    def post(self, request):
        """
        导入ZIP格式的分析数据包

        请求体格式: multipart/form-data
        - file: ZIP文件
        - username: 用户名
        """
        try:
            # 获取ZIP文件
            zip_file = request.FILES.get('file')
            if not zip_file:
                return Response(
                    {'error': '未找到ZIP文件'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 验证文件类型
            if not zip_file.name.endswith('.zip'):
                return Response(
                    {'error': '只支持ZIP格式的数据包'},
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

            # 用于回滚的变量
            temp_extract_dir = None
            new_task_dir = None
            new_video_id = None

            try:
                import zipfile
                import tempfile
                import shutil
                from pathlib import Path

                # 1. 查询用户信息，获取output_base_path和model_base_path
                with connection.cursor() as cursor:
                    user_sql = "SELECT id, output_base_path, model_base_path FROM users WHERE username = %s AND is_deleted = FALSE"
                    cursor.execute(user_sql, (username,))
                    user = cursor.fetchone()

                    if not user:
                        return Response(
                            {'error': '用户不存在'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    user_id = user['id']
                    output_base_path = Path(user['output_base_path'])
                    model_base_path = Path(user['model_base_path'])

                # 2. 生成新的task_id
                new_task_id = str(uuid.uuid4())

                # 3. 解压ZIP文件到临时目录
                temp_extract_dir = Path(tempfile.mkdtemp())

                # 保存上传的ZIP文件
                zip_temp_path = temp_extract_dir / 'uploaded.zip'
                with open(zip_temp_path, 'wb') as f:
                    for chunk in zip_file.chunks():
                        f.write(chunk)

                # 解压ZIP文件
                with zipfile.ZipFile(zip_temp_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_extract_dir)

                # 获取解压后的根目录（应该是唯一的子目录）
                extracted_dirs = [d for d in temp_extract_dir.iterdir() if d.is_dir()]
                if len(extracted_dirs) != 1:
                    # 如果解压后没有子目录，直接使用temp_extract_dir
                    extracted_root = temp_extract_dir
                else:
                    extracted_root = extracted_dirs[0]

                # 4. 验证数据包完整性
                required_items = ['original', 'frames', 'output', 'result.json']
                missing_items = []
                for item in required_items:
                    item_path = extracted_root / item
                    if not item_path.exists():
                        missing_items.append(item)

                # 检查CSV文件（可能包含task_id）
                csv_files = list(extracted_root.glob('processed_cells_*.csv'))
                if not csv_files:
                    missing_items.append('processed_cells_*.csv')

                if missing_items:
                    return Response(
                        {'error': f'数据包不完整，缺少: {", ".join(missing_items)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # 5. 读取result.json
                result_json_path = extracted_root / 'result.json'
                with open(result_json_path, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)

                # 6. 创建新的任务目录
                new_task_dir = output_base_path / 'tasks' / new_task_id
                new_task_dir.mkdir(parents=True, exist_ok=True)

                # 7. 复制解压后的文件到新目录
                for item in extracted_root.iterdir():
                    if item.is_file() and item.name != 'uploaded.zip':
                        dest = new_task_dir / item.name
                        shutil.copy2(item, dest)
                    elif item.is_dir() and item.name != 'original':
                        dest = new_task_dir / item.name
                        shutil.copytree(item, dest)

                # 8. 重命名CSV文件
                old_csv = csv_files[0]
                new_csv_name = f"processed_cells_{new_task_id}.csv"
                new_csv_path = new_task_dir / new_csv_name
                shutil.move(new_task_dir / old_csv.name, new_csv_path)

                # 9. 修改result.json
                old_task_id = result_data.get('task_id', '')
                result_data['task_id'] = new_task_id
                result_data['created_at'] = datetime.now().isoformat()

                # 更新annotated_video_path
                if 'annotated_video_path' in result_data:
                    result_data['annotated_video_path'] = str(new_task_dir / 'output' / 'tracking_result.mp4')

                # 更新annotated_video_url
                if 'annotated_video_url' in result_data:
                    result_data['annotated_video_url'] = f'/api/video/{new_task_id}'

                # 保存修改后的result.json
                with open(new_task_dir / 'result.json', 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)

                # 10. 获取original文件夹中的视频文件
                original_dir = extracted_root / 'original'
                video_files = list(original_dir.glob('*.mp4'))
                if not video_files:
                    video_files = list(original_dir.glob('*.avi'))
                if not video_files:
                    video_files = list(original_dir.glob('*.mov'))
                if not video_files:
                    video_files = list(original_dir.glob('*.mkv'))

                if not video_files:
                    return Response(
                        {'error': 'original文件夹中没有找到视频文件'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                video_file = video_files[0]
                video_name = video_file.name
                video_size = video_file.stat().st_size

                # 11. 插入videos表（先检查是否已存在同名视频）
                existing_video = None
                with connection.cursor() as cursor:
                    # 检查是否已存在同名视频
                    check_video_sql = """
                    SELECT id, video_path FROM videos 
                    WHERE user_id = %s AND video_name = %s AND is_deleted = FALSE
                    """
                    cursor.execute(check_video_sql, (user_id, video_name))
                    existing_video = cursor.fetchone()

                    if existing_video:
                        # 使用现有的视频记录
                        new_video_id = existing_video['id']
                        video_path = existing_video['video_path']
                        print(f"使用已存在的视频记录: {new_video_id}, 路径: {video_path}")
                    else:
                        # 插入新的视频记录
                        insert_video_sql = """
                        INSERT INTO videos (user_id, video_name, video_path, total_frames, video_duration, file_size, created_at, updated_at, is_deleted, deleted_at)
                        VALUES (%s, %s, '', %s, %s, %s, NOW(), NOW(), FALSE, NULL)
                        """
                        cursor.execute(insert_video_sql, (
                            user_id,
                            video_name,
                            result_data.get('total_frames', 0),
                            result_data.get('video_duration', 0),
                            video_size
                        ))
                        connection.commit()
                        new_video_id = cursor.lastrowid

                        # 更新video_path
                        video_path = f"videos/{new_video_id}/{video_name}"
                        update_video_sql = "UPDATE videos SET video_path = %s WHERE id = %s"
                        cursor.execute(update_video_sql, (video_path, new_video_id))
                        connection.commit()

                # 12. 移动视频文件到videos目录（只有新插入视频时才需要移动）
                if not existing_video:
                    videos_dir = output_base_path / 'videos' / str(new_video_id)
                    videos_dir.mkdir(parents=True, exist_ok=True)
                    video_dest_path = videos_dir / video_name
                    shutil.move(str(video_file), str(video_dest_path))
                else:
                    # 使用现有视频，从数据库获取完整路径
                    video_dest_path = output_base_path / video_path

                # 13. 更新result.json中的original_video_path
                if 'original_video_path' in result_data:
                    result_data['original_video_path'] = str(video_dest_path)
                    with open(new_task_dir / 'result.json', 'w', encoding='utf-8') as f:
                        json.dump(result_data, f, ensure_ascii=False, indent=2)

                # 14. 删除original文件夹
                original_dir_new = new_task_dir / 'original'
                if original_dir_new.exists():
                    shutil.rmtree(original_dir_new)

                # 15. 计算fps
                video_duration = result_data.get('video_duration', 0)
                total_frames = result_data.get('total_frames', 0)
                if video_duration > 0:
                    fps = int(total_frames / video_duration)
                else:
                    fps = 10

                # 16. 插入tasks表
                with connection.cursor() as cursor:
                    insert_task_sql = """
                    INSERT INTO tasks (user_id, video_id, model_id, task_id, task_name, status, conf, imgsz, fps, annotated_video_name, error_message, created_at, updated_at, is_deleted, deleted_at)
                    VALUES (%s, %s, 1, %s, '新 导入任务', 'completed', 0.3, 1024, %s, 'tracking_result.mp4', '', NOW(), NOW(), FALSE, NULL)
                    """
                    cursor.execute(insert_task_sql, (user_id, new_video_id, new_task_id, fps))
                    connection.commit()

                # 17. 使用process_and_save方法导入Cell数据
                from .services.preprocess_data import process_and_save
                process_and_save(new_task_dir / 'result.json', new_task_id)

                # 18. 创建TaskStatus记录
                with connection.cursor() as cursor:
                    insert_status_sql = """
                    INSERT INTO task_status (task_id, status, progress, stage, current_frame, total_frames, error_message, created_at, updated_at, is_deleted, deleted_at)
                    VALUES (%s, 'completed', 100, 'data_processing', 0, 0, '', NOW(), NOW(), FALSE, NULL)
                    """
                    cursor.execute(insert_status_sql, (new_task_id,))
                    connection.commit()

                # 清理临时目录
                if temp_extract_dir and temp_extract_dir.exists():
                    shutil.rmtree(temp_extract_dir)

                return Response({
                    'message': '数据包导入成功',
                    'task_id': new_task_id,
                    'status': 'completed'
                }, status=status.HTTP_200_OK)

            except Exception as e:
                # 回滚：删除已创建的目录和文件
                try:
                    if new_task_dir and new_task_dir.exists():
                        shutil.rmtree(new_task_dir)
                    if new_video_id:
                        videos_dir = output_base_path / 'videos' / str(new_video_id)
                        if videos_dir.exists():
                            shutil.rmtree(videos_dir)
                    if temp_extract_dir and temp_extract_dir.exists():
                        shutil.rmtree(temp_extract_dir)
                except Exception as rollback_error:
                    print(f"回滚失败: {rollback_error}")

                # 如果已插入数据库记录，需要删除（软删除）
                try:
                    with connection.cursor() as cursor:
                        if new_task_id:
                            cursor.execute("UPDATE tasks SET is_deleted = TRUE, deleted_at = NOW() WHERE task_id = %s", (new_task_id,))
                        if new_task_id:
                            cursor.execute("UPDATE task_status SET is_deleted = TRUE, deleted_at = NOW() WHERE task_id = %s", (new_task_id,))
                        if new_video_id:
                            cursor.execute("UPDATE videos SET is_deleted = TRUE, deleted_at = NOW() WHERE id = %s", (new_video_id,))
                        connection.commit()
                except Exception as db_rollback_error:
                    print(f"数据库回滚失败: {db_rollback_error}")

                return Response(
                    {'error': f'导入数据包失败: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        finally:
            connection.close()