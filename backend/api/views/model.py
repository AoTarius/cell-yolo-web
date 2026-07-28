"""
模型管理相关视图

提供模型的列表查询、上传、删除、重命名等功能。
仅支持 .pt 格式的 YOLO 模型文件。
"""

import json
import os
import shutil
from pathlib import Path

import pymysql
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

load_dotenv()


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

                # 构建模型列表：优先匹配真实文件；即便文件暂不可达，也保留数据库记录避免前端误显示"暂无模型"
                models = []
                models_dir = Path(model_base_path)

                for record in model_records:
                    model_name = (record.get('model_name') or '').strip()
                    raw_model_path = str(record.get('model_path') or '').strip()

                    candidate_paths = []
                    if raw_model_path:
                        raw_path = Path(raw_model_path)
                        if raw_path.is_absolute():
                            candidate_paths.append(raw_path)
                        else:
                            candidate_paths.append(models_dir / raw_path)

                    if model_name:
                        candidate_paths.append(models_dir / f"{model_name}.pt")
                        candidate_paths.append(models_dir / model_name)

                    matched_file = next((p for p in candidate_paths if p.exists() and p.is_file()), None)

                    if matched_file:
                        try:
                            relative_path = str(matched_file.relative_to(models_dir))
                        except Exception:
                            relative_path = str(matched_file)

                        models.append({
                            'name': model_name or matched_file.stem,
                            'size_mb': round(matched_file.stat().st_size / (1024 * 1024), 2),
                            'path': relative_path
                        })
                    else:
                        # 回退：文件不存在或路径不一致时，仍返回记录，前端可见模型名称
                        fallback_path = raw_model_path or (f"{model_name}.pt" if model_name else '')
                        models.append({
                            'name': model_name or Path(fallback_path).stem or '未命名模型',
                            'size_mb': 0,
                            'path': fallback_path
                        })

                # 兜底：若数据库记录无法构成可见列表，则扫描模型目录中的 .pt 文件
                if not models and models_dir.exists() and models_dir.is_dir():
                    for model_file in models_dir.glob('*.pt'):
                        if not model_file.is_file():
                            continue
                        models.append({
                            'name': model_file.stem,
                            'size_mb': round(model_file.stat().st_size / (1024 * 1024), 2),
                            'path': str(model_file.name)
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
