"""
WebSocket 路由配置
"""

from django.urls import re_path
from . import websocket

websocket_urlpatterns = [
    re_path(r'ws/task/(?P<task_id>\w+)/$', websocket.TaskProgressConsumer.as_asgi()),
]