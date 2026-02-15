import os
import json
import uuid
import threading
from pathlib import Path
from datetime import datetime

from django.conf import settings
from django.http import JsonResponse, FileResponse, HttpResponseNotFound
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .services.video_processor import get_video_processor


# 全局任务状态存储（生产环境应使用数据库或 Redis）
task_status = {}
task_lock = threading.Lock()


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

            # 生成任务ID
            task_id = str(uuid.uuid4())

            # 创建任务目录
            media_root = Path(settings.MEDIA_ROOT)
            task_dir = media_root / 'tasks' / task_id
            task_dir.mkdir(parents=True, exist_ok=True)

            # 保存视频文件
            video_path = task_dir / 'original' / video_file.name
            video_path.parent.mkdir(parents=True, exist_ok=True)

            with open(video_path, 'wb') as f:
                for chunk in video_file.chunks():
                    f.write(chunk)

            # 初始化任务状态
            with task_lock:
                task_status[task_id] = {
                    'task_id': task_id,
                    'video_name': video_file.name,
                    'video_path': str(video_path),
                    'status': 'uploaded',
                    'progress': 0,
                    'created_at': datetime.now().isoformat(),
                    'error': None
                }

            return Response({
                'task_id': task_id,
                'video_name': video_file.name,
                'status': 'uploaded',
                'message': '视频上传成功'
            }, status=status.HTTP_201_CREATED)

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

            if not task_id:
                return Response(
                    {'error': '缺少 task_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 获取参数
            conf = data.get('conf', 0.3)
            imgsz = data.get('imgsz', 1024)
            fps = data.get('fps', 10)
            model_name = data.get('model_name', 'best_split.pt')

            # 检查任务是否存在
            with task_lock:
                if task_id not in task_status:
                    return Response(
                        {'error': '任务不存在'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # 检查任务状态
                if task_status[task_id]['status'] == 'processing':
                    return Response(
                        {'error': '任务正在处理中'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # 更新任务状态
                task_status[task_id]['status'] = 'processing'
                task_status[task_id]['progress'] = 0
                task_status[task_id]['params'] = {
                    'conf': conf,
                    'imgsz': imgsz,
                    'fps': fps,
                    'model_name': model_name
                }

            # 在后台线程中处理视频
            thread = threading.Thread(
                target=self._process_video,
                args=(task_id, conf, imgsz, fps, model_name),
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

    def _process_video(self, task_id: str, conf: float, imgsz: int, fps: int, model_name: str):
        """后台处理视频"""
        try:
            # 获取任务信息
            with task_lock:
                task_info = task_status[task_id]
                video_path = task_info['video_path']

            # 获取视频处理器
            processor = get_video_processor()

            # 进度回调函数
            def progress_callback(stage: str, progress: int, data: dict):
                with task_lock:
                    if task_id in task_status:
                        task_status[task_id]['progress'] = progress
                        task_status[task_id]['stage'] = stage
                        task_status[task_id]['message'] = data.get('message', '')
                        task_status[task_id]['current_frame'] = data.get('current_frame')
                        task_status[task_id]['total_frames'] = data.get('total_frames')

            # 处理视频
            result = processor.process_video(
                video_path,
                task_id,
                conf=conf,
                imgsz=imgsz,
                fps=fps,
                model_name=model_name,
                progress_callback=progress_callback
            )

            # 更新任务状态
            with task_lock:
                if task_id in task_status:
                    task_status[task_id]['status'] = 'completed'
                    task_status[task_id]['progress'] = 100
                    task_status[task_id]['result'] = result
                    task_status[task_id]['completed_at'] = datetime.now().isoformat()

        except Exception as e:
            # 更新任务状态为失败
            with task_lock:
                if task_id in task_status:
                    task_status[task_id]['status'] = 'failed'
                    task_status[task_id]['error'] = str(e)
                    task_status[task_id]['failed_at'] = datetime.now().isoformat()


class TaskStatusView(APIView):
    """查询任务状态接口"""

    def get(self, request, task_id):
        with task_lock:
            if task_id not in task_status:
                return Response(
                    {'error': '任务不存在'},
                    status=status.HTTP_404_NOT_FOUND
                )

            task_info = task_status[task_id].copy()

            # 如果任务完成，读取 JSON 结果
            if task_info['status'] == 'completed' and 'result' not in task_info:
                try:
                    media_root = Path(settings.MEDIA_ROOT)
                    json_path = media_root / 'tasks' / task_id / 'result.json'
                    if json_path.exists():
                        with open(json_path, 'r', encoding='utf-8') as f:
                            task_info['result'] = json.load(f)
                except Exception as e:
                    task_info['error'] = f'读取结果失败: {str(e)}'

            return Response(task_info, status=status.HTTP_200_OK)


class TaskResultView(APIView):
    """获取处理结果接口"""

    def get(self, request, task_id):
        media_root = Path(settings.MEDIA_ROOT)
        json_path = media_root / 'tasks' / task_id / 'result.json'

        if not json_path.exists():
            return Response(
                {'error': '结果不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        with open(json_path, 'r', encoding='utf-8') as f:
            result = json.load(f)

        return Response(result, status=status.HTTP_200_OK)


class AnnotatedVideoView(APIView):
    """获取标注视频接口"""

    def get(self, request, task_id):
        media_root = Path(settings.MEDIA_ROOT)
        video_path = media_root / 'tasks' / task_id / 'output' / 'tracking_result.mp4'

        if not video_path.exists():
            return HttpResponseNotFound('视频不存在')

        # 获取文件名
        filename = f"{task_id}_annotated.mp4"

        # 返回视频文件
        return FileResponse(
            open(video_path, 'rb'),
            content_type='video/mp4',
            as_attachment=True,
            filename=filename
        )


class TaskListView(APIView):
    """获取所有任务列表接口"""

    def get(self, request):
        """获取所有已完成任务的结果列表"""
        media_root = Path(settings.MEDIA_ROOT)
        tasks_dir = media_root / 'tasks'

        if not tasks_dir.exists():
            return Response({'tasks': [], 'count': 0}, status=status.HTTP_200_OK)

        tasks = []
        
        # 遍历所有任务目录
        for task_dir in tasks_dir.iterdir():
            if not task_dir.is_dir():
                continue

            # 读取 result.json
            json_path = task_dir / 'result.json'
            if json_path.exists():
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        result = json.load(f)
                        tasks.append(result)
                except Exception as e:
                    print(f"读取任务 {task_dir.name} 结果失败: {e}")
                    continue

        # 按创建时间排序（最新的在前）
        tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return Response({
            'tasks': tasks,
            'count': len(tasks)
        }, status=status.HTTP_200_OK)


class ModelListView(APIView):
    """获取可用模型列表接口"""

    def get(self, request):
        """获取 models 目录下所有 .pt 模型文件"""
        backend_dir = Path(settings.BASE_DIR).parent
        models_dir = backend_dir / 'backend' / 'models'

        if not models_dir.exists():
            return Response({'models': [], 'count': 0}, status=status.HTTP_200_OK)

        models = []
        
        # 遍历所有 .pt 文件
        for model_file in models_dir.glob('*.pt'):
            models.append({
                'name': model_file.name,
                'size_mb': round(model_file.stat().st_size / (1024 * 1024), 2),
                'path': str(model_file.relative_to(backend_dir))
            })

        # 按名称排序
        models.sort(key=lambda x: x['name'])

        return Response({
            'models': models,
            'count': len(models),
            'default': 'best_split.pt'
        }, status=status.HTTP_200_OK)


class DeleteTaskView(APIView):
    """删除任务接口"""

    def delete(self, request, task_id: str):
        """删除指定任务的所有数据"""
        try:
            import shutil

            media_root = Path(settings.MEDIA_ROOT)
            task_dir = media_root / 'tasks' / task_id

            # 检查任务是否存在
            if not task_dir.exists():
                return Response(
                    {'error': '任务不存在'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 检查任务是否正在处理中
            with task_lock:
                if task_id in task_status and task_status[task_id]['status'] == 'processing':
                    return Response(
                        {'error': '任务正在处理中，无法删除'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # 从内存中移除任务状态
                if task_id in task_status:
                    del task_status[task_id]

            # 删除任务目录及其所有内容
            shutil.rmtree(task_dir)

            return Response({
                'message': '任务已成功删除',
                'task_id': task_id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'删除任务失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
