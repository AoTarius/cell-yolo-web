"""
用户认证相关视图

提供注册、登录、用户信息修改、用户删除等功能。
密码使用 bcrypt 哈希存储。
"""

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Optional

import bcrypt
import pymysql
from dotenv import load_dotenv
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

load_dotenv()


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


class RegisterView(APIView):
    """用户注册接口"""

    @staticmethod
    def _resolve_storage_paths(username: str, model_base_path: Optional[str], output_base_path: Optional[str]):
        project_root = Path(__file__).resolve().parents[2]
        default_user_root = project_root / '.user-storage' / username

        final_model_path = (model_base_path or '').strip() or str(default_user_root / 'models')
        final_output_path = (output_base_path or '').strip() or str(default_user_root / 'outputs')

        return final_model_path, final_output_path

    @staticmethod
    def _ensure_storage_dirs(model_base_path: str, output_base_path: str):
        os.makedirs(model_base_path, exist_ok=True)
        os.makedirs(output_base_path, exist_ok=True)

    def post(self, request):
        """创建新用户"""
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            model_base_path = data.get('model_base_path')
            output_base_path = data.get('output_base_path')

            # 验证必填字段
            if not username or not password:
                return Response(
                    {'error': '用户名和密码不能为空'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            model_base_path, output_base_path = self._resolve_storage_paths(
                username,
                model_base_path,
                output_base_path,
            )

            try:
                self._ensure_storage_dirs(model_base_path, output_base_path)
            except Exception as e:
                return Response(
                    {'error': f'创建默认存储目录失败: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
                    # 检查用户名记录（包含软删除用户）
                    check_sql = "SELECT id, is_deleted FROM users WHERE username = %s"
                    cursor.execute(check_sql, (username,))
                    existing_user = cursor.fetchone()

                    if existing_user and not existing_user['is_deleted']:
                        return Response(
                            {'error': '用户名已存在'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # 使用 bcrypt 哈希密码
                    password_bytes = password.encode('utf-8')
                    salt = bcrypt.gensalt()
                    hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

                    if existing_user and existing_user['is_deleted']:
                        # 用户曾被软删除，允许同名重新注册（恢复账号）
                        restore_sql = """
                        UPDATE users
                        SET password_hash = %s,
                            model_base_path = %s,
                            output_base_path = %s,
                            dark_mode = TRUE,
                            is_deleted = FALSE,
                            deleted_at = NULL,
                            updated_at = NOW()
                        WHERE id = %s
                        """
                        cursor.execute(restore_sql, (hashed_password, model_base_path, output_base_path, existing_user['id']))
                        connection.commit()
                        user_id = existing_user['id']
                        message = '注册成功（已恢复历史账号）'
                        response_status = status.HTTP_200_OK
                    else:
                        # 创建新用户
                        insert_sql = """
                        INSERT INTO users (username, password_hash, model_base_path, output_base_path, dark_mode, created_at, updated_at, is_deleted, deleted_at)
                        VALUES (%s, %s, %s, %s, TRUE, NOW(), NOW(), FALSE, NULL)
                        """
                        cursor.execute(insert_sql, (username, hashed_password, model_base_path, output_base_path))
                        connection.commit()
                        user_id = cursor.lastrowid
                        message = '注册成功'
                        response_status = status.HTTP_201_CREATED

                    # 获取最终用户信息
                    select_sql = "SELECT * FROM users WHERE id = %s"
                    cursor.execute(select_sql, (user_id,))
                    new_user = cursor.fetchone()

                    return Response({
                        'status': 'success',
                        'message': message,
                        'user': {
                            'id': new_user['id'],
                            'username': new_user['username'],
                            'email': new_user['email'],
                            'dark_mode': new_user['dark_mode'],
                            'model_base_path': new_user['model_base_path'],
                            'output_base_path': new_user['output_base_path']
                        }
                    }, status=response_status)

            finally:
                connection.close()

        except json.JSONDecodeError:
            return Response(
                {'error': '无效的 JSON 格式'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except pymysql.IntegrityError as e:
            if e.args and e.args[0] == 1062:
                return Response(
                    {'error': '用户名已存在'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'error': f'注册失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {'error': f'注册失败: {str(e)}'},
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


class DeleteUserView(APIView):
    """删除用户接口"""

    def delete(self, request):
        """删除指定用户及其相关数据"""
        try:
            username = request.GET.get('username')

            if not username:
                return Response(
                    {'error': '未提供用户名'},
                    status=status.HTTP_400_BAD_REQUEST
                )

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
                    user_sql = """
                    SELECT id, model_base_path, output_base_path
                    FROM users
                    WHERE username = %s
                    """
                    cursor.execute(user_sql, (username,))
                    user = cursor.fetchone()

                    if not user:
                        return Response(
                            {'error': '用户不存在'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    user_id = user['id']
                    model_base_path = user['model_base_path']
                    output_base_path = user['output_base_path']

                    # 先删除用户相关的任务状态和细胞数据
                    delete_cells_sql = """
                    DELETE c
                    FROM cells c
                    JOIN tasks t ON c.task_id = t.id
                    WHERE t.user_id = %s
                    """
                    cursor.execute(delete_cells_sql, (user_id,))

                    delete_task_status_sql = """
                    DELETE ts
                    FROM task_status ts
                    JOIN tasks t ON ts.task_id = t.task_id
                    WHERE t.user_id = %s
                    """
                    cursor.execute(delete_task_status_sql, (user_id,))

                    # 再删除任务、视频、模型
                    delete_tasks_sql = "DELETE FROM tasks WHERE user_id = %s"
                    cursor.execute(delete_tasks_sql, (user_id,))

                    delete_videos_sql = "DELETE FROM videos WHERE user_id = %s"
                    cursor.execute(delete_videos_sql, (user_id,))

                    delete_models_sql = "DELETE FROM models WHERE user_id = %s"
                    cursor.execute(delete_models_sql, (user_id,))

                    # 最后删除用户本身
                    delete_user_sql = "DELETE FROM users WHERE id = %s"
                    cursor.execute(delete_user_sql, (user_id,))

                    connection.commit()

                # 删除用户目录（数据库已提交后再清理文件）
                for path_str in [model_base_path, output_base_path]:
                    if not path_str:
                        continue
                    path_obj = Path(path_str)
                    if path_obj.exists() and path_obj.is_dir():
                        shutil.rmtree(path_obj)

                return Response(
                    {
                        'status': 'success',
                        'message': '用户及其相关数据已删除',
                        'username': username,
                    },
                    status=status.HTTP_200_OK
                )

            finally:
                connection.close()

        except Exception as e:
            return Response(
                {'error': f'删除用户失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
