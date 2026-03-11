#!/usr/bin/env python3
"""
数据库操作工具模块
提供执行 SQL 语句的函数
"""

import os
import sys
import pymysql
from dotenv import load_dotenv
from typing import Any, Optional, List, Dict, Tuple

# 加载环境变量（从上一级目录加载 .env）
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class DatabaseOperator:
    """数据库操作类"""

    def __init__(self):
        """初始化数据库连接参数"""
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'cell_tracking')
        self.connection = None

    def connect(self) -> bool:
        """连接到数据库"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                cursorclass=pymysql.cursors.DictCursor
            )
            return True
        except pymysql.Error as e:
            print(f"✗ 连接数据库失败: {e}")
            return False

    def disconnect(self) -> None:
        """断开数据库连接"""
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                print(f"关闭连接时出错: {e}")

    def execute_query(self, sql: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        执行查询语句

        Args:
            sql: SQL 查询语句
            params: 查询参数（可选）

        Returns:
            查询结果列表，每行是一个字典
        """
        if not self.connection:
            if not self.connect():
                return []

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params or ())
                result = cursor.fetchall()
            self.connection.commit()
            return result
        except pymysql.Error as e:
            print(f"✗ 执行查询失败: {e}")
            return []

    def execute_insert(self, sql: str, params: Optional[Tuple] = None) -> Optional[int]:
        """
        执行插入语句

        Args:
            sql: SQL 插入语句
            params: 插入参数（可选）

        Returns:
            插入的记录 ID，失败返回 None
        """
        if not self.connection:
            if not self.connect():
                return None

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params or ())
                insert_id = cursor.lastrowid
            self.connection.commit()
            return insert_id
        except pymysql.Error as e:
            print(f"✗ 执行插入失败: {e}")
            return None

    def execute_update(self, sql: str, params: Optional[Tuple] = None) -> bool:
        """
        执行更新语句

        Args:
            sql: SQL 更新语句
            params: 更新参数（可选）

        Returns:
            是否成功
        """
        if not self.connection:
            if not self.connect():
                return False

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params or ())
                affected_rows = cursor.rowcount
            self.connection.commit()
            return affected_rows > 0
        except pymysql.Error as e:
            print(f"✗ 执行更新失败: {e}")
            return False

    def execute_delete(self, sql: str, params: Optional[Tuple] = None) -> bool:
        """
        执行删除语句

        Args:
            sql: SQL 删除语句
            params: 删除参数（可选）

        Returns:
            是否成功
        """
        if not self.connection:
            if not self.connect():
                return False

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params or ())
                affected_rows = cursor.rowcount
            self.connection.commit()
            return affected_rows > 0
        except pymysql.Error as e:
            print(f"✗ 执行删除失败: {e}")
            return False

    def execute_raw(self, sql: str, params: Optional[Tuple] = None) -> bool:
        """
        执行任意 SQL 语句

        Args:
            sql: SQL 语句
            params: 参数（可选）

        Returns:
            是否成功
        """
        if not self.connection:
            if not self.connect():
                return False

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params or ())
            self.connection.commit()
            return True
        except pymysql.Error as e:
            print(f"✗ 执行 SQL 失败: {e}")
            return False

    def __enter__(self):
        """支持上下文管理器"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持上下文管理器"""
        self.disconnect()