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

from .services.video_processor import get_video_processor


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
        print(f"{get_thread_prefix(task_id)} 开始处理任务")
        try:
            # 获取任务信息
            with task_lock:
                task_info = task_status[task_id]
                video_path = task_info['video_path']

            print(f"{get_thread_prefix(task_id)} 获取视频处理器")

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

            print(f"{get_thread_prefix(task_id)} 开始处理视频，参数: conf={conf}, imgsz={imgsz}, fps={fps}, model={model_name}")

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

            print(f"{get_thread_prefix(task_id)} 视频处理完成")

            # 更新任务状态
            with task_lock:
                if task_id in task_status:
                    task_status[task_id]['status'] = 'completed'
                    task_status[task_id]['progress'] = 100
                    task_status[task_id]['result'] = result
                    task_status[task_id]['completed_at'] = datetime.now().isoformat()

        except Exception as e:
            # 更新任务状态为失败
            print(f"{get_thread_prefix(task_id)} 处理失败: {str(e)}")
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


class OriginalVideoView(APIView):
    """获取原始视频接口"""

    def get(self, request, task_id):
        media_root = Path(settings.MEDIA_ROOT)
        original_dir = media_root / 'tasks' / task_id / 'original'

        # 查找original目录下的视频文件
        video_files = list(original_dir.glob('*.mp4')) + list(original_dir.glob('*.avi')) + list(original_dir.glob('*.mov'))

        if not video_files:
            return HttpResponseNotFound('原始视频不存在')

        # 取第一个找到的视频文件
        video_path = video_files[0]

        # 获取文件名
        filename = video_path.name

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
        """获取所有任务（包括已完成和处理中）的列表"""
        media_root = Path(settings.MEDIA_ROOT)
        tasks_dir = media_root / 'tasks'

        if not tasks_dir.exists():
            return Response({'tasks': [], 'count': 0}, status=status.HTTP_200_OK)

        tasks = []

        # 遍历所有任务目录
        for task_dir in tasks_dir.iterdir():
            if not task_dir.is_dir():
                continue

            task_id = task_dir.name

            # 优先读取 result.json（已完成任务）
            json_path = task_dir / 'result.json'
            if json_path.exists():
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        result = json.load(f)
                        # 确保包含 task_id
                        result['task_id'] = task_id
                        # 如果任务在 task_status 中且不是 completed，更新状态
                        with task_lock:
                            if task_id in task_status and task_status[task_id]['status'] != 'completed':
                                # 修正状态
                                task_status[task_id]['status'] = 'completed'
                        tasks.append(result)
                except Exception as e:
                    print(f"{get_thread_prefix()} 读取任务 {task_id} 结果失败: {e}")
                    continue
            else:
                # 检查任务是否真的在处理中
                with task_lock:
                    if task_id in task_status:
                        task_info = task_status[task_id]
                        if task_info['status'] == 'processing':
                            # 真正在处理中
                            tasks.append({
                                'task_id': task_id,
                                'original_video_path': task_info.get('video_path', ''),
                                'video_name': task_info.get('video_name', 'Unknown'),
                                'status': 'processing',
                                'progress': task_info.get('progress', 0),
                                'created_at': task_info.get('created_at', datetime.now().isoformat()),
                            })
                        elif task_info['status'] == 'failed':
                            # 任务失败，但不返回（或者可以标记为失败）
                            pass
                    else:
                        # 任务不在 task_status 中，说明是遗留任务
                        # 查找原始视频文件
                        original_dir = task_dir / 'original'
                        if original_dir.exists():
                            video_files = list(original_dir.glob('*.mp4')) + \
                                          list(original_dir.glob('*.avi')) + \
                                          list(original_dir.glob('*.mov'))

                            if video_files:
                                # 这是遗留任务，视为失败，不返回
                                # 或者可以返回一个标记为 failed 的任务
                                pass

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

            # 读取 JSON 结果
            media_root = Path(settings.MEDIA_ROOT)
            json_path = media_root / 'tasks' / task_id / 'result.json'
            print(f"{get_thread_prefix(task_id)} JSON path: {json_path}")
            print(f"{get_thread_prefix(task_id)} JSON exists: {json_path.exists()}")

            if not json_path.exists():
                print(f"{get_thread_prefix(task_id)} JSON file not found at: {json_path}")
                return Response(
                    {'error': '结果不存在'},
                    status=status.HTTP_404_NOT_FOUND
                )

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
            if not model_file:
                return Response(
                    {'error': '未找到模型文件'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 验证文件类型
            if not model_file.name.endswith('.pt'):
                return Response(
                    {'error': '只支持 .pt 格式的模型文件'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 获取 models 目录路径
            backend_dir = Path(settings.BASE_DIR).parent
            models_dir = backend_dir / 'backend' / 'models'

            # 确保目录存在
            models_dir.mkdir(parents=True, exist_ok=True)

            # 保存模型文件
            model_path = models_dir / model_file.name
            
            # 如果文件已存在，询问是否覆盖（这里简单处理为覆盖）
            with open(model_path, 'wb') as f:
                for chunk in model_file.chunks():
                    f.write(chunk)

            # 返回成功响应
            return Response({
                'status': 'success',
                'message': '模型上传成功',
                'model_name': model_file.name,
                'model_size_mb': round(model_file.size / (1024 * 1024), 2)
            }, status=status.HTTP_201_CREATED)

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