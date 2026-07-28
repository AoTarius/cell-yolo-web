"""
views 包公共工具

提供线程标识辅助函数，供各视图模块使用。
"""

import threading


def get_thread_prefix(task_id: str = None):
    """获取线程标识前缀，格式: [task_id|T线程ID] 或 [T线程ID]（带 ANSI 颜色）"""
    thread_id = f"T{threading.current_thread().ident}"
    BLUE = '\033[94m'       # 亮蓝色
    CYAN = '\033[96m'       # 青色
    RESET = '\033[0m'       # 重置颜色

    if task_id:
        return f"{BLUE}[{task_id}|{CYAN}{thread_id}{BLUE}]{RESET}"
    return f"{BLUE}[{CYAN}{thread_id}{BLUE}]{RESET}"
