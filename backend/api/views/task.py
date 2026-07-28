"""
任务处理相关视图

提供视频处理任务的创建、状态查询、结果获取、列表、重命名、删除等功能。
核心处理逻辑委托给 VideoProcessor，通过后台线程异步执行。
"""

import json
import os
import shutil
import threading
from pathlib import Path

import pymysql
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ._helpers import get_thread_prefix
from ..services.video_processor import VideoProcessor

load_dotenv()


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


class TaskListView(APIView):
    """获取所有任务列表接口"""

    def get(self, request):
        """获取所有任务（包括已完成和处理中）的列表"""
        username = request.GET.get('username')

        # 获取排序参数
        sort_by = request.GET.get('sort_by', '[]')
        try:
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
                    raw_model_name = str(task.get('model_display_name') or '').strip()
                    if raw_model_name:
                        model_file_name = raw_model_name.replace('\\', '/').split('/')[-1]
                        normalized_model_name = Path(model_file_name).stem or model_file_name
                        task['model_display_name'] = normalized_model_name

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
                    update_cells_sql = """
                    UPDATE cells
                    SET is_deleted = TRUE, deleted_at = NOW()
                    WHERE task_id = %s AND is_deleted = FALSE
                    """
                    cursor.execute(update_cells_sql, (task_info['id'],))

                    # 软删除任务状态
                    update_status_sql = """
                    UPDATE task_status
                    SET is_deleted = TRUE, deleted_at = NOW()
                    WHERE task_id = %s AND is_deleted = FALSE
                    """
                    cursor.execute(update_status_sql, (task_id,))

                    # 软删除任务（最后删除主表）
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
