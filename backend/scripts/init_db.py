#!/usr/bin/env python3
"""
MySQL 数据库初始化脚本
用于创建数据库
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

        # 步骤 3: 关闭连接
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