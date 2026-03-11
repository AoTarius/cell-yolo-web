#!/usr/bin/env python3
"""
MySQL 数据库初始化脚本
用于创建数据库、表结构以及初始数据
"""

import os
import sys
import pymysql
from dotenv import load_dotenv

# 加载环境变量（从上一级目录加载 .env）
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class DatabaseInitializer:
    """数据库初始化类"""

    def __init__(self):
        """初始化数据库连接参数"""
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'cell_tracking')
        self.connection = None

    def connect(self):
        """连接到 MySQL 服务器"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            print(f"✓ 成功连接到 MySQL 服务器 ({self.host}:{self.port})")
            return True
        except pymysql.Error as e:
            print(f"✗ 连接 MySQL 服务器失败: {e}")
            return False

    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            try:
                self.connection.close()
                print("✓ 数据库连接已关闭")
            except Exception as e:
                print(f"关闭连接时出错: {e}")

    def create_database(self):
        """创建数据库（如果不存在）"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✓ 数据库 '{self.database}' 创建成功或已存在")
            cursor.close()
            return True
        except pymysql.Error as e:
            print(f"✗ 创建数据库失败: {e}")
            return False

    def connect_to_database(self):
        """连接到指定数据库"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print(f"✓ 成功连接到数据库 '{self.database}'")
            return True
        except pymysql.Error as e:
            print(f"✗ 连接数据库失败: {e}")
            return False

    def create_tables(self):
        """创建表结构"""
        try:
            cursor = self.connection.cursor()

            # 用户表
            create_users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(255),
                password_hash VARCHAR(255) NOT NULL,
                dark_mode BOOLEAN NOT NULL DEFAULT TRUE,
                model_base_path VARCHAR(500) NOT NULL,
                output_base_path VARCHAR(500) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                deleted_at TIMESTAMP NULL,
                UNIQUE INDEX idx_username (username),
                INDEX idx_email (email),
                INDEX idx_deleted (is_deleted)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """

            # 视频表
            create_videos_table = """
            CREATE TABLE IF NOT EXISTS videos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                video_name VARCHAR(255) NOT NULL,
                video_path VARCHAR(255) NOT NULL,
                total_frames INT,
                video_duration FLOAT,
                file_size INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                deleted_at TIMESTAMP NULL,
                INDEX idx_user_id (user_id),
                INDEX idx_user_deleted (user_id, is_deleted),
                UNIQUE INDEX idx_user_video_name (user_id, video_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """

            # 模型表
            create_models_table = """
            CREATE TABLE IF NOT EXISTS models (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                model_name VARCHAR(100) NOT NULL,
                model_path VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                deleted_at TIMESTAMP NULL,
                INDEX idx_user_id (user_id),
                INDEX idx_user_deleted (user_id, is_deleted),
                UNIQUE INDEX idx_user_model_name (user_id, model_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """

            # 任务表
            create_tasks_table = """
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                video_id INT NOT NULL,
                model_id INT NOT NULL,
                task_id VARCHAR(36) NOT NULL UNIQUE,
                task_name VARCHAR(255) NOT NULL,
                status VARCHAR(20) NOT NULL,
                progress INT NOT NULL DEFAULT 0,
                conf FLOAT DEFAULT 0.3,
                imgsz INT DEFAULT 1024,
                fps INT DEFAULT 10,
                annotated_video_name VARCHAR(255),
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                deleted_at TIMESTAMP NULL,
                UNIQUE INDEX idx_task_id (task_id),
                INDEX idx_user_id (user_id),
                INDEX idx_user_status (user_id, status),
                INDEX idx_user_deleted (user_id, is_deleted),
                INDEX idx_video_id (video_id),
                INDEX idx_model_id (model_id),
                INDEX idx_created_at (created_at),
                INDEX idx_user_status_deleted (user_id, status, is_deleted)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """

            # 细胞表
            create_cells_table = """
            CREATE TABLE IF NOT EXISTS cells (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_id INT NOT NULL,
                frame INT NOT NULL,
                track_id INT NOT NULL,
                bb_left FLOAT NOT NULL,
                bb_top FLOAT NOT NULL,
                bb_width FLOAT NOT NULL,
                bb_height FLOAT NOT NULL,
                conf FLOAT NOT NULL,
                class INT NOT NULL DEFAULT 0,
                visibility FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                deleted_at TIMESTAMP NULL,
                INDEX idx_task_id (task_id),
                INDEX idx_task_frame_track (task_id, frame, track_id),
                INDEX idx_task_track (task_id, track_id),
                INDEX idx_task_frame (task_id, frame),
                INDEX idx_task_deleted (task_id, is_deleted)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """

            # 执行表创建
            tables = [
                (create_users_table, "users"),
                (create_videos_table, "videos"),
                (create_models_table, "models"),
                (create_tasks_table, "tasks"),
                (create_cells_table, "cells")
            ]

            for table_sql, table_name in tables:
                cursor.execute(table_sql)
                print(f"✓ 表 '{table_name}' 创建成功或已存在")

            cursor.close()
            return True
        except pymysql.Error as e:
            print(f"✗ 创建表失败: {e}")
            return False

    def insert_initial_data(self):
        """插入初始数据（可选）"""
        try:
            cursor = self.connection.cursor()

            # 示例：创建一个测试用户（密码需要哈希处理）
            # 注意：实际使用时应该使用 bcrypt 或类似库处理密码
            insert_user = """
            INSERT IGNORE INTO users (username, email, password_hash, dark_mode, model_base_path, output_base_path)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_user, ('admin', 'admin@example.com', 'placeholder_hash', True, '/tmp/models', '/tmp/output'))

            print("✓ 初始数据插入成功")
            cursor.close()
            return True
        except pymysql.Error as e:
            print(f"✗ 插入初始数据失败: {e}")
            return False

    def initialize(self):
        """执行完整的初始化流程"""
        print("=" * 50)
        print("开始初始化 MySQL 数据库")
        print("=" * 50)

        # 步骤 1: 连接到 MySQL 服务器
        if not self.connect():
            sys.exit(1)

        # 步骤 2: 创建数据库
        if not self.create_database():
            self.disconnect()
            sys.exit(1)

        # 步骤 3: 断开连接并重新连接到目标数据库
        self.disconnect()
        if not self.connect_to_database():
            sys.exit(1)

        # 步骤 4: 创建表结构
        if not self.create_tables():
            self.disconnect()
            sys.exit(1)

        # 步骤 5: 插入初始数据（可选）
        # self.insert_initial_data()

        # 步骤 6: 关闭连接
        self.disconnect()

        print("=" * 50)
        print("✓ 数据库初始化完成！")
        print("=" * 50)


def main():
    """主函数"""
    initializer = DatabaseInitializer()
    initializer.initialize()


if __name__ == "__main__":
    main()