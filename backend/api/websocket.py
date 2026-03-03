"""
WebSocket 消费者
用于实时推送任务进度
"""

import json
import asyncio
import threading
from typing import Dict, Set
from threading import Thread, Lock

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer


# 全局 WebSocket 连接管理
connections: Dict[str, Set[AsyncWebsocketConsumer]] = {}
connections_lock = Lock()


# 线程标识辅助函数
def get_thread_prefix(task_id: str = None):
    """获取线程标识前缀，格式: [task_id|T线程ID] 或 [T线程ID]（带颜色）"""
    thread_id = f"T{threading.current_thread().ident}"
    # ANSI 颜色码
    BLUE = '\033[94m'      # 亮蓝色
    CYAN = '\033[96m'      # 青色
    RESET = '\033[0m'      # 重置颜色

    if task_id:
        return f"{BLUE}[{task_id}|{CYAN}{thread_id}{BLUE}]{RESET}"
    return f"{BLUE}[{CYAN}{thread_id}{BLUE}]{RESET}"


class TaskProgressConsumer(AsyncWebsocketConsumer):
    """任务进度 WebSocket 消费者"""

    async def connect(self):
        """连接建立"""
        await self.accept()

        # 获取任务ID（从 URL 参数）
        self.task_id = self.scope['url_route']['kwargs'].get('task_id')

        # 将连接添加到任务订阅列表
        if self.task_id:
            with connections_lock:
                if self.task_id not in connections:
                    connections[self.task_id] = set()
                connections[self.task_id].add(self)

        print(f"{get_thread_prefix(self.task_id)} WebSocket connected")

    async def disconnect(self, close_code):
        """连接断开"""
        if self.task_id:
            with connections_lock:
                if self.task_id in connections:
                    connections[self.task_id].discard(self)
                    if not connections[self.task_id]:
                        del connections[self.task_id]

        print(f"{get_thread_prefix(self.task_id)} WebSocket disconnected")

    async def receive(self, text_data):
        """接收消息"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'subscribe':
                # 订阅任务进度
                self.task_id = data.get('task_id')
                if self.task_id:
                    with connections_lock:
                        if self.task_id not in connections:
                            connections[self.task_id] = set()
                        connections[self.task_id].add(self)

                    # 发送确认消息
                    await self.send(json.dumps({
                        'type': 'subscribed',
                        'task_id': self.task_id,
                        'message': f'已订阅任务 {self.task_id} 的进度更新'
                    }))

            elif message_type == 'unsubscribe':
                # 取消订阅
                if self.task_id:
                    with connections_lock:
                        if self.task_id in connections:
                            connections[self.task_id].discard(self)

                    await self.send(json.dumps({
                        'type': 'unsubscribed',
                        'task_id': self.task_id,
                        'message': f'已取消订阅任务 {self.task_id}'
                    }))

        except json.JSONDecodeError:
            await self.send(json.dumps({
                'type': 'error',
                'message': '无效的 JSON 格式'
            }))


# 进度推送函数（从外部调用）
def broadcast_progress(task_id: str, stage: str, progress: int, data: dict = None):
    """
    向所有订阅该任务的连接广播进度更新

    Args:
        task_id: 任务ID
        stage: 处理阶段
        progress: 进度百分比
        data: 额外数据
    """
    message = {
        'type': 'progress',
        'task_id': task_id,
        'stage': stage,
        'progress': progress,
        'data': data or {}
    }

    # 获取所有订阅该任务的连接
    with connections_lock:
        task_connections = connections.get(task_id, set()).copy()

    # 异步发送消息
    async def send_to_connections():
        channel_layer = get_channel_layer()
        for connection in task_connections:
            try:
                await connection.send(json.dumps(message))
            except Exception as e:
                print(f"{get_thread_prefix(task_id)} 发送消息失败: {e}")

    # 在事件循环中执行
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        asyncio.create_task(send_to_connections())
    else:
        loop.run_until_complete(send_to_connections())


def broadcast_status(task_id: str, status: str, message: str = None):
    """
    广播任务状态更新

    Args:
        task_id: 任务ID
        status: 任务状态
        message: 状态消息
    """
    broadcast_progress(
        task_id,
        'status',
        0,
        {
            'status': status,
            'message': message
        }
    )


def broadcast_error(task_id: str, error: str):
    """
    广播错误信息

    Args:
        task_id: 任务ID
        error: 错误信息
    """
    broadcast_progress(
        task_id,
        'error',
        0,
        {
            'error': error
        }
    )


def broadcast_complete(task_id: str):
    """
    广播任务完成

    Args:
        task_id: 任务ID
    """
    broadcast_progress(
        task_id,
        'complete',
        100,
        {
            'message': '任务完成'
        }
    )