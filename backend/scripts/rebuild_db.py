#!/usr/bin/env python3
"""
数据库重建脚本
删除旧数据库并重新创建
"""

import os
import sys
import pymysql
from dotenv import load_dotenv

# 加载环境变量（从上一级目录加载 .env）
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class DatabaseRebuilder:
    """数据库重建类"""

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

    def drop_database(self):
        """删除数据库（如果存在）"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"DROP DATABASE IF EXISTS {self.database}")
            print(f"✓ 数据库 '{self.database}' 已删除")
            cursor.close()
            return True
        except pymysql.Error as e:
            print(f"✗ 删除数据库失败: {e}")
            return False

    def rebuild(self):
        """执行完整的重建流程"""
        print("=" * 50)
        print("开始重建数据库")
        print("=" * 50)

        # 步骤 1: 连接到 MySQL 服务器
        if not self.connect():
            sys.exit(1)

        # 步骤 2: 删除旧数据库
        if not self.drop_database():
            self.disconnect()
            sys.exit(1)

        # 步骤 3: 断开连接
        self.disconnect()

        # 步骤 4: 运行 init_db.py 创建新数据库
        print("=" * 50)
        print("运行 init_db.py 创建新数据库...")
        print("=" * 50)

        try:
            # 导入并运行 init_db
            from init_db import DatabaseInitializer
            initializer = DatabaseInitializer()
            initializer.initialize()
        except Exception as e:
            print(f"✗ 运行 init_db.py 失败: {e}")
            sys.exit(1)

        print("=" * 50)
        print("✓ 数据库重建完成！")
        print("=" * 50)


def main():
    """主函数"""
    # 确认操作
    print("⚠️  警告：此操作将删除整个数据库及其所有数据！")
    print(f"数据库名称: {os.getenv('DB_NAME', 'cell_tracking')}")
    
    response = input("确认继续？(yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("操作已取消")
        sys.exit(0)

    rebuilder = DatabaseRebuilder()
    rebuilder.rebuild()


if __name__ == "__main__":
    main()