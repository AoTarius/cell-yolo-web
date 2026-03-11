#!/usr/bin/env python3
"""
数据初始化脚本
用于初始化数据库中的初始数据
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


def main():
    """主函数"""
    success = init_root_user()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()