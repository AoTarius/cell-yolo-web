"""
自由绘图相关视图

提供 Python 代码在线执行、环境预热、示例模板浏览等功能。
"""

import json
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView

from ..models import Task, Cell, User
from ..services.free_plot_executor import (
    ALLOWED_IMPORT_MODULES,
    execute_plot_code,
    warmup_plot_worker,
    validate_plot_code,
)


class FreePlotRunView(APIView):
    """自由绘图执行接口（MVP 安全版）"""

    MAX_ROWS = 20000

    def _build_task_data(self, task_obj: Task) -> dict:
        cells_qs = (
            Cell.objects.filter(task=task_obj.id, is_deleted=False)
            .order_by('frame', 'track_id')[: self.MAX_ROWS]
        )

        rows = []
        for cell in cells_qs:
            center = (cell.metrics_json or {}).get('center') or {}
            shape = (cell.metrics_json or {}).get('shape') or {}
            motion = (cell.metrics_json or {}).get('motion') or {}
            rows.append({
                'frame': int(cell.frame),
                'track_id': int(cell.track_id),
                'area': float(cell.area or 0),
                'speed': float(cell.speed or 0),
                'bb_left': float(cell.bb_left or 0),
                'bb_top': float(cell.bb_top or 0),
                'bb_width': float(cell.bb_width or 0),
                'bb_height': float(cell.bb_height or 0),
                'center_x': float(center.get('cx') or 0),
                'center_y': float(center.get('cy') or 0),
                'perimeter': float(shape.get('perimeter') or 0),
                'circularity': float(shape.get('circularity') or 0),
                'aspect_ratio': float(shape.get('aspect_ratio') or 0),
                'distance': float(motion.get('distance') or 0),
                'migration_speed': float(motion.get('migration_speed') or 0),
                'mean_square_displacement': float(motion.get('mean_square_displacement') or 0),
            })

        return {
            'task_id': task_obj.task_id,
            'task_name': task_obj.task_name,
            'video_name': task_obj.video.video_name if task_obj.video_id else '',
            'row_count': len(rows),
            'truncated': len(rows) >= self.MAX_ROWS,
            'rows': rows,
        }

    def post(self, request):
        try:
            data = json.loads(request.body or '{}')
            username = str(data.get('username') or '').strip()
            task_id = str(data.get('task_id') or '').strip()
            code = str(data.get('code') or '')

            if not username:
                return JsonResponse({'success': False, 'error': '缺少用户名'}, status=400)
            if not task_id:
                return JsonResponse({'success': False, 'error': '缺少 task_id'}, status=400)

            task_obj = (
                Task.objects
                .select_related('video', 'user')
                .filter(task_id=task_id, is_deleted=False, user__username=username, user__is_deleted=False)
                .first()
            )
            if not task_obj:
                return JsonResponse({'success': False, 'error': '任务不存在或无权限访问'}, status=404)

            validation_errors = validate_plot_code(code)
            if validation_errors:
                return JsonResponse(
                    {
                        'success': False,
                        'error': '代码未通过安全检查',
                        'validation_errors': validation_errors,
                        'whitelist': sorted(ALLOWED_IMPORT_MODULES),
                    },
                    status=400,
                )

            task_data = self._build_task_data(task_obj)
            result = execute_plot_code(code, task_data)

            if not result.get('success'):
                return JsonResponse(
                    {
                        'success': False,
                        'error': result.get('error') or '执行失败',
                        'logs': result.get('logs', ''),
                        'whitelist': sorted(ALLOWED_IMPORT_MODULES),
                    },
                    status=400,
                )

            return JsonResponse(
                {
                    'success': True,
                    'image_base64': result.get('image_base64', ''),
                    'logs': result.get('logs', ''),
                    'task_data_meta': {
                        'task_id': task_data['task_id'],
                        'row_count': task_data['row_count'],
                        'truncated': task_data['truncated'],
                    },
                    'whitelist': sorted(ALLOWED_IMPORT_MODULES),
                },
                status=200,
            )
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': '无效的 JSON 请求体'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class FreePlotWarmupView(APIView):
    """自由绘图环境预热接口"""

    def post(self, request):
        try:
            data = json.loads(request.body or '{}')
            username = str(data.get('username') or '').strip()
            if not username:
                return JsonResponse({'success': False, 'error': '缺少用户名'}, status=400)

            # 仅允许已存在用户触发预热，避免匿名滥用
            user_exists = Task.objects.filter(user__username=username, user__is_deleted=False).exists()
            if not user_exists:
                return JsonResponse({'success': False, 'error': '用户不存在或无权限'}, status=403)

            result = warmup_plot_worker()
            if not result.get('success'):
                return JsonResponse(
                    {
                        'success': False,
                        'error': result.get('error', '预热失败'),
                        'whitelist': sorted(ALLOWED_IMPORT_MODULES),
                    },
                    status=400,
                )

            return JsonResponse(
                {
                    'success': True,
                    'message': '绘图环境已预热。',
                    'whitelist': sorted(ALLOWED_IMPORT_MODULES),
                },
                status=200,
            )
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': '无效的 JSON 请求体'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class FreePlotExamplesView(APIView):
    """自由绘图模板列表与内容读取接口"""

    @staticmethod
    def _examples_dir() -> Path:
        # backend/backend/settings.py 的 BASE_DIR 指向 backend 目录，这里回到项目根目录
        return Path(settings.BASE_DIR).parent / 'docs' / 'examples'

    @staticmethod
    def _is_safe_example_name(name: str) -> bool:
        if not name or '/' in name or '\\' in name:
            return False
        if not name.endswith('.py'):
            return False
        allowed = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-')
        return all(ch in allowed for ch in name)

    def get(self, request, example_name=None):
        username = str(request.GET.get('username') or '').strip()
        if not username:
            return JsonResponse({'success': False, 'error': '缺少用户名'}, status=400)

        user_exists = User.objects.filter(username=username, is_deleted=False).exists()
        if not user_exists:
            return JsonResponse({'success': False, 'error': '用户不存在或无权限'}, status=403)

        examples_dir = self._examples_dir()
        if not examples_dir.exists() or not examples_dir.is_dir():
            return JsonResponse({'success': False, 'error': '案例目录不存在'}, status=404)

        if not example_name:
            files = sorted([p.name for p in examples_dir.glob('*.py') if p.is_file()])
            return JsonResponse({'success': True, 'examples': files}, status=200)

        if not self._is_safe_example_name(example_name):
            return JsonResponse({'success': False, 'error': '非法案例名称'}, status=400)

        target = examples_dir / example_name
        if not target.exists() or not target.is_file():
            return JsonResponse({'success': False, 'error': '案例不存在'}, status=404)

        try:
            content = target.read_text(encoding='utf-8')
        except Exception:
            return JsonResponse({'success': False, 'error': '案例读取失败'}, status=500)

        return JsonResponse(
            {
                'success': True,
                'name': example_name,
                'content': content,
            },
            status=200,
        )
