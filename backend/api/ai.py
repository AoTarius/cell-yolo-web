"""
AI对话接口
提供流式AI对话功能
"""
import os
import json
from typing import Generator

from django.conf import settings
from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests


# AI角色配置
AI_ROLES = {
    'cell-analyst': {
        'name': '细胞分析专家',
        'system_prompt': '''你是一位专业的细胞分析专家，精通YOLO目标检测、视频分析、细胞特征提取等技术。

你的专长包括：
- 细胞检测与分割技术
- YOLO模型训练与优化
- 视频逐帧分析方法
- 细胞特征值提取与解读
- 数据分析与可视化

请用专业但易懂的语言回答用户关于细胞分析的问题，并提供实用的建议。'''
    }
}


def get_system_prompt(role: str) -> str:
    """获取AI角色的系统提示词"""
    if role not in AI_ROLES:
        role = 'cell-analyst'
    return AI_ROLES[role]['system_prompt']


def generate_ai_response_stream(message: str, role: str) -> Generator[str, None, None]:
    """
    生成AI响应流
    
    Args:
        message: 用户消息
        role: AI角色ID
        
    Yields:
        SSE格式的数据块
    """
    # 获取系统提示词
    system_prompt = get_system_prompt(role)
    
    # 构建DeepSeek API请求
    api_base = getattr(settings, 'DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1')
    api_url = f"{api_base}/chat/completions"
    api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
    
    if not api_key:
        yield 'data: {"error": "DeepSeek API Key未配置"}\n\n'
        return
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "temperature": 0.7,
        "stream": True
    }
    
    try:
        # 发送请求到DeepSeek API
        response = requests.post(api_url, headers=headers, json=payload, stream=True, timeout=30)
        response.raise_for_status()
        
        # 流式处理响应
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                
                if line_str.startswith('data: '):
                    data = line_str[6:]
                    
                    if data == '[DONE]':
                        yield 'data: [DONE]\n\n'
                    else:
                        try:
                            parsed = json.loads(data)
                            content = parsed.get('choices', [{}])[0].get('delta', {}).get('content', '')
                            if content:
                                yield f'data: {json.dumps({"content": content})}\n\n'
                        except json.JSONDecodeError:
                            # 忽略解析错误
                            pass
                            
    except requests.exceptions.RequestException as e:
        error_msg = f"请求DeepSeek API失败: {str(e)}"
        yield f'data: {json.dumps({"error": error_msg})}\n\n'
    except Exception as e:
        error_msg = f"处理请求时发生错误: {str(e)}"
        yield f'data: {json.dumps({"error": error_msg})}\n\n'


@api_view(['POST'])
def chat_stream(request):
    """
    流式AI对话接口
    
    POST /api/ai/chat/stream
    Body: {
        "message": "用户消息",
        "role": "AI角色ID"
    }
    
    Returns: SSE流式响应
    """
    try:
        # 解析请求数据
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        role = data.get('role', 'general')
        
        # 验证消息
        if not message:
            return Response(
                {'error': '消息内容不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 验证角色
        if role not in AI_ROLES:
            role = 'general'
        
        # 返回流式响应
        response = StreamingHttpResponse(
            generate_ai_response_stream(message, role),
            content_type='text/event-stream'
        )

        # 设置SSE响应头
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'  # 禁用nginx缓冲（生产环境有效）

        return response
        
    except json.JSONDecodeError:
        return Response(
            {'error': '无效的JSON数据'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'服务器错误: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_ai_roles(request):
    """
    获取所有可用的AI角色

    GET /api/ai/roles

    Returns: {
        "roles": [
            {
                "id": "general",
                "name": "通用大模型"
            },
            ...
        ]
    }
    """
    roles = [
        {
            'id': role_id,
            'name': role_data['name']
        }
        for role_id, role_data in AI_ROLES.items()
    ]

    return Response({
        'roles': roles
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def check_api_config(request):
    """
    检查 AI API 配置是否有效

    GET /api/ai/check-config

    Returns: {
        "configured": bool,
        "message": str
    }
    """
    api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')

    # 检查 API KEY 是否配置
    if not api_key:
        return Response({
            'configured': False,
            'message': 'API Key 未配置'
        }, status=status.HTTP_200_OK)

    # 检查是否是默认值
    default_keys = [
        'your_deepseek_api_key',
        'your_api_key',
        'your-deepseek-api-key',
        'sk-your_deepseek_api_key',
    ]

    if api_key.lower() in [key.lower() for key in default_keys]:
        return Response({
            'configured': False,
            'message': 'API Key 未设置（使用默认值）'
        }, status=status.HTTP_200_OK)

    # 检查是否以 sk- 开头（DeepSeek API Key 格式）
    if not api_key.startswith('sk-'):
        return Response({
            'configured': False,
            'message': 'API Key 格式无效'
        }, status=status.HTTP_200_OK)

    # 检查长度（DeepSeek API Key 通常较长）
    if len(api_key) < 20:
        return Response({
            'configured': False,
            'message': 'API Key 长度无效'
        }, status=status.HTTP_200_OK)

    # 配置有效
    return Response({
        'configured': True,
        'message': 'API Key 配置有效'
    }, status=status.HTTP_200_OK)
