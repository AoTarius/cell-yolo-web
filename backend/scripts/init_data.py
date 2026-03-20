#!/usr/bin/env python3
"""
数据初始化脚本
用于初始化数据库中的初始数据，并检查表结构是否与 models.py 定义一致
"""

import sys
from datetime import datetime
import bcrypt
import os

# 添加 scripts 目录到路径，以便导入 sql 模块
sys.path.insert(0, os.path.dirname(__file__))

from sql import DatabaseOperator


def hash_password(password: str) -> str:
    """
    对密码进行哈希处理

    Args:
        password: 明文密码

    Returns:
        哈希后的密码字符串
    """
    # 将密码转换为字节，生成哈希
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # 返回字符串格式
    return hashed.decode('utf-8')


def check_and_fix_table_structure():
    """
    检查数据库表结构是否与 models.py 定义一致，并修复问题
    """
    print("=" * 50)
    print("检查数据库表结构")
    print("=" * 50)

    with DatabaseOperator() as db:
        # 定义需要检查的表和字段
        expected_tables = {
            "users": {
                "username": "VARCHAR(100) NOT NULL",
                "email": "VARCHAR(255)",
                "password_hash": "VARCHAR(255) NOT NULL",
                "dark_mode": "TINYINT(1) DEFAULT 1",
                "model_base_path": "VARCHAR(500) NOT NULL",
                "output_base_path": "VARCHAR(500) NOT NULL",
            },
            "videos": {
                "user_id": "BIGINT NOT NULL",
                "video_name": "VARCHAR(255) NOT NULL",
                "video_path": "VARCHAR(255) NOT NULL",
                "total_frames": "INT",
                "video_duration": "FLOAT",
                "file_size": "BIGINT",
            },
            "models": {
                "user_id": "BIGINT NOT NULL",
                "model_name": "VARCHAR(100) NOT NULL",
                "model_path": "VARCHAR(255) NOT NULL",
            },
            "tasks": {
                "user_id": "BIGINT NOT NULL",
                "video_id": "BIGINT NOT NULL",
                "model_id": "BIGINT NOT NULL",
                "task_id": "VARCHAR(36) NOT NULL",
                "task_name": "VARCHAR(255) NOT NULL",
                "status": "VARCHAR(20) DEFAULT 'pending'",
                "total_frames": "INT DEFAULT 0",
                "conf": "DOUBLE DEFAULT 0.3",
                "imgsz": "INT DEFAULT 1024",
                "fps": "INT DEFAULT 10",
                "annotated_video_name": "VARCHAR(255)",
            },
            "cells": {
                "task_id": "BIGINT NOT NULL",
                "frame": "INT NOT NULL",
                "track_id": "INT NOT NULL",
                "bb_left": "FLOAT NOT NULL",
                "bb_top": "FLOAT NOT NULL",
                "bb_width": "FLOAT NOT NULL",
                "bb_height": "FLOAT NOT NULL",
                "conf": "FLOAT NOT NULL",
                "class_id": "INT DEFAULT 0",
                "visibility": "FLOAT",
                "area": "FLOAT DEFAULT 0.0",
                "speed": "FLOAT DEFAULT 0.0",
                "tracking_persistence": "FLOAT DEFAULT 0.0",
                "metrics_json": "JSON DEFAULT '{\"bbox\": {\"left\": 0.0, \"top\": 0.0, \"width\": 0.0, \"height\": 0.0}, \"center\": {\"cx\": 0.0, \"cy\": 0.0}, \"shape\": {\"perimeter\": 0.0, \"circularity\": 0.0, \"circularity_increment\": 0.0, \"aspect_ratio\": 0.0, \"shape_change_rate\": 0.0, \"spreading_index\": 0.0, \"protrusion_activity_index\": 0.0}, \"motion\": {\"vx\": 0.0, \"vy\": 0.0, \"distance\": 0.0, \"migration_speed\": 0.0, \"mean_square_displacement\": 0.0, \"turning_angle\": 0.0, \"persistence_index\": 0.0}, \"visibility\": 1.0, \"cell_class\": 0, \"confidence\": 1.0}'",
            },
            "task_status": {
                "task_id": "VARCHAR(36) NOT NULL",
                "status": "VARCHAR(20) DEFAULT 'pending'",
                "progress": "INT DEFAULT 0",
                "stage": "VARCHAR(50)",
                "current_frame": "INT DEFAULT 0",
                "total_frames": "INT DEFAULT 0",
                "error_message": "TEXT",
            },
        }

        for table, fields in expected_tables.items():
            print(f"检查表: {table}")
            for field, expected_definition in fields.items():
                # 查询字段定义
                check_sql = f"SHOW COLUMNS FROM {table} WHERE Field = %s"
                result = db.execute_query(check_sql, (field,))

                if not result:
                    print(f"✗ 字段缺失: {field} (表: {table})")
                    # 添加缺失字段
                    alter_sql = f"ALTER TABLE {table} ADD COLUMN {field} {expected_definition}"
                    db.execute(alter_sql)
                    print(f"✓ 添加字段: {field} -> {expected_definition}")
                    continue

                actual_definition = result[0]["Type"]
                if "DEFAULT" in expected_definition:
                    actual_default = "DEFAULT" in result[0]["Extra"]
                    if not actual_default:
                        print(f"✗ 字段 {field} 默认值不匹配 (表: {table})")
                        # 修复字段默认值
                        alter_sql = f"ALTER TABLE {table} MODIFY {field} {expected_definition}"
                        db.execute(alter_sql)
                        print(f"✓ 修复字段默认值: {field} -> {expected_definition}")

                print(f"✓ 字段检查通过: {field}")

        print("=" * 50)
        print("✓ 表结构检查完成")
        print("=" * 50)


def init_root_user() -> bool:
    """
    初始化 root 用户

    用户信息：
    - username: root
    - password: password
    - email: NULL
    - dark_mode: False
    - model_base_path: models
    - output_base_path: output
    - created_at: 当前时间
    - updated_at: 当前时间
    - is_deleted: False
    - deleted_at: NULL

    Returns:
        是否成功
    """
    print("=" * 50)
    print("初始化 root 用户")
    print("=" * 50)

    # 检查 root 用户是否已存在
    with DatabaseOperator() as db:
        # 查询是否已存在 root 用户
        check_sql = "SELECT id FROM users WHERE username = %s AND is_deleted = FALSE"
        existing_user = db.execute_query(check_sql, ('root',))

        if existing_user:
            print(f"✗ root 用户已存在 (ID: {existing_user[0]['id']})")
            print("如需重新创建，请先删除现有用户")
            return False

        # 哈希密码
        password_hash = hash_password('password')
        print(f"✓ 密码哈希完成")

        # 准备插入数据
        current_time = datetime.now()

        insert_sql = """
        INSERT INTO users (
            username, email, password_hash, dark_mode,
            model_base_path, output_base_path,
            created_at, updated_at, is_deleted, deleted_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        params = (
            'root',                    # username
            None,                      # email (NULL)
            password_hash,             # password_hash
            False,                     # dark_mode
            'models',                  # model_base_path
            'output',                  # output_base_path
            current_time,              # created_at
            current_time,              # updated_at
            False,                     # is_deleted
            None                       # deleted_at (NULL)
        )

        # 插入用户
        user_id = db.execute_insert(insert_sql, params)

        if user_id:
            print(f"✓ root 用户创建成功 (ID: {user_id})")
            print(f"  用户名: root")
            print(f"  密码: password")
            print(f"  邮箱: 未设置")
            print(f"  暗色模式: False")
            print(f"  模型路径: models")
            print(f"  输出路径: output")
            print("=" * 50)
            print("✓ 初始化完成！")
            print("=" * 50)
            return True
        else:
            print("✗ 创建 root 用户失败")
            return False
        
def init_import_model() -> bool:
    """
    初始化 导入model 

    用户信息：
    - model_name: 非本地模型
    - model_path: 非本地模型路径
    - user_id: 1，表示该模型属于 root 用户，实际使用时一般用户需要注册账号使用，不会暴露给用户
    - created_at: 当前时间
    - updated_at: 当前时间
    - is_deleted: False
    - deleted_at: NULL

    Returns:
        是否成功
    """
    print("=" * 50)
    print("初始化 导入model")
    print("=" * 50)

    # 检查 导入model 是否已存在
    with DatabaseOperator() as db:
        # 查询是否已存在 导入model
        check_sql = "SELECT id FROM models WHERE model_name = %s AND is_deleted = FALSE"
        existing_model = db.execute_query(check_sql, ('非本地模型',))

        if existing_model:
            print(f"✗ 导入model 已存在 (ID: {existing_model[0]['id']})")
            print("如需重新创建，请先删除现有model")
            return False

        # 准备插入数据
        current_time = datetime.now()

        insert_sql = """
        INSERT INTO models (
            model_name, model_path, user_id,
            created_at, updated_at, is_deleted, deleted_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        params = (
            '非本地模型',                  # model_name
            '非本地模型路径',                # model_path
            1,                        # user_id
            current_time,              # created_at
            current_time,              # updated_at
            False,                     # is_deleted
            None                       # deleted_at (NULL)
        )

        # 插入模型
        model = db.execute_insert(insert_sql, params)

        if model:
            print(f"✓ 导入model 创建成功 (ID: {model})")
            print("=" * 50)
            print("✓ 初始化完成！")
            print("=" * 50)
            return True
        else:
            print("✗ 创建 导入model 失败")
            return False


def main():
    """主函数"""
    check_and_fix_table_structure()
    success = init_root_user()
    success = success and init_import_model()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()