"""
数据访问与可视化视图

提供标注视频访问、帧图片获取、数据导出/导入、细胞数据查询、3D轨迹图生成等功能。
"""

import csv
import io
import json
import os
import shutil
import tempfile
import uuid
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pymysql
from dotenv import load_dotenv
from django.http import FileResponse, HttpResponse, HttpResponseNotFound, JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Cell, Task

load_dotenv()


@api_view(['GET'])
def test_api(request):
    """测试接口"""
    return Response({
        'message': 'Django + Vue 前后端分离项目已启动！',
        'status': 'success'
    }, status=status.HTTP_200_OK)


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

                task_root = output_base_path / 'tasks' / task_id

                def build_candidates(num: int):
                    filename = f"t{num:04d}.png"
                    return [
                        task_root / 'output' / filename,
                        task_root / 'frames' / filename,
                    ]

                candidate_paths = build_candidates(frame_number)
                # 兼容部分进度计数与文件命名存在 1 帧偏差的情况
                if frame_number > 0:
                    candidate_paths.extend(build_candidates(frame_number - 1))

                frame_path = next((p for p in candidate_paths if p.exists()), None)

                if frame_path is None:
                    return HttpResponseNotFound(f'帧 {frame_number} 不存在')

                # 返回图片文件
                return FileResponse(
                    open(frame_path, 'rb'),
                    content_type='image/png',
                    as_attachment=False
                )

        finally:
            connection.close()


class ExportDataView(APIView):
    """导出数据接口（CSV 或 JSON）"""

    def get(self, request, task_id: str):
        """导出任务数据为 CSV 或 JSON 格式"""
        try:
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


class ExportTaskDataView(APIView):
    """导出任务数据包接口"""

    def get(self, request, task_id):
        """将 task_id 对应的文件夹打包成 zip 并下载"""
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

                # 16. 根据数据包中的模型名称查找或创建模型记录
                raw_model_name = str(result_data.get('model_name') or '').strip()
                raw_model_path = str(result_data.get('model_path') or '').strip()
                model_name_source = raw_model_name or raw_model_path
                model_file_name = model_name_source.replace('\\', '/').split('/')[-1] if model_name_source else ''
                imported_model_name = Path(model_file_name).stem if model_file_name else ''
                imported_model_name = imported_model_name or '导入模型'
                imported_model_path = raw_model_path or model_file_name or imported_model_name

                with connection.cursor() as cursor:
                    model_sql = """
                    SELECT id, is_deleted FROM models
                    WHERE user_id = %s AND model_name = %s
                    LIMIT 1
                    """
                    cursor.execute(model_sql, (user_id, imported_model_name))
                    existing_model = cursor.fetchone()

                    if existing_model:
                        model_id = existing_model['id']
                        if existing_model.get('is_deleted'):
                            revive_sql = """
                            UPDATE models
                            SET is_deleted = FALSE, deleted_at = NULL, model_path = %s, updated_at = NOW()
                            WHERE id = %s
                            """
                            cursor.execute(revive_sql, (imported_model_path, model_id))
                            connection.commit()
                    else:
                        insert_model_sql = """
                        INSERT INTO models (user_id, model_name, model_path, created_at, updated_at, is_deleted, deleted_at)
                        VALUES (%s, %s, %s, NOW(), NOW(), FALSE, NULL)
                        """
                        cursor.execute(insert_model_sql, (user_id, imported_model_name, imported_model_path))
                        connection.commit()
                        model_id = cursor.lastrowid

                # 17. 插入tasks表
                with connection.cursor() as cursor:
                    insert_task_sql = """
                    INSERT INTO tasks (user_id, video_id, model_id, task_id, task_name, status, conf, imgsz, fps, annotated_video_name, error_message, created_at, updated_at, is_deleted, deleted_at)
                    VALUES (%s, %s, %s, %s, '新 导入任务', 'completed', 0.3, 1024, %s, 'tracking_result.mp4', '', NOW(), NOW(), FALSE, NULL)
                    """
                    cursor.execute(insert_task_sql, (user_id, new_video_id, model_id, new_task_id, fps))
                    connection.commit()

                # 18. 使用process_and_save方法导入Cell数据
                from ..services.preprocess_data import process_and_save
                process_and_save(new_task_dir / 'result.json', new_task_id)

                # 19. 创建TaskStatus记录
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
