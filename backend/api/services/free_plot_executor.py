import ast
import base64
import contextlib
import io
import math
import multiprocessing
import statistics
import threading
import traceback
import uuid
from typing import Any, Dict, List


MAX_CODE_CHARS = 12000
EXEC_TIMEOUT_SECONDS = 30
WARMUP_TIMEOUT_SECONDS = 90

ALLOWED_IMPORT_MODULES = {
    'math',
    'statistics',
    'numpy',
    'matplotlib',
    'matplotlib.pyplot',
    'scipy',
    'scipy.stats',
}

BLOCKED_NAME_PREFIXES = (
    '__',
)

BLOCKED_CALL_NAMES = {
    'eval',
    'exec',
    'compile',
    'open',
    'input',
    '__import__',
    'globals',
    'locals',
    'vars',
    'getattr',
    'setattr',
    'delattr',
    'help',
    'exit',
    'quit',
}

BLOCKED_ROOT_NAMES = {
    'os',
    'sys',
    'subprocess',
    'socket',
    'pathlib',
    'shutil',
    'requests',
    'builtins',
    'importlib',
}


_worker_lock = threading.Lock()
_execute_lock = threading.Lock()
_worker_process = None
_worker_request_queue = None
_worker_response_queue = None


class PlotCodeValidator(ast.NodeVisitor):
    def __init__(self) -> None:
        self.errors: List[str] = []

    def _module_allowed(self, module_name: str) -> bool:
        if module_name in ALLOWED_IMPORT_MODULES:
            return True
        return any(module_name.startswith(f'{m}.') for m in ALLOWED_IMPORT_MODULES)

    def _root_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return self._root_name(node.value)
        return ''

    def visit_Import(self, node: ast.Import) -> Any:
        for alias in node.names:
            if not self._module_allowed(alias.name):
                self.errors.append(f'不允许导入模块: {alias.name}')
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        if node.level and node.level > 0:
            self.errors.append('不允许相对导入')
            return
        module_name = node.module or ''
        if not self._module_allowed(module_name):
            self.errors.append(f'不允许导入模块: {module_name}')
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
        root_name = self._root_name(node.func)
        if root_name in BLOCKED_CALL_NAMES or root_name in BLOCKED_ROOT_NAMES:
            self.errors.append(f'检测到危险调用: {root_name}')
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> Any:
        if any(node.id.startswith(p) for p in BLOCKED_NAME_PREFIXES):
            self.errors.append(f'不允许使用名称: {node.id}')
        if node.id in BLOCKED_ROOT_NAMES:
            self.errors.append(f'不允许使用模块或对象: {node.id}')
        self.generic_visit(node)


def validate_plot_code(code: str) -> List[str]:
    if not code or not code.strip():
        return ['代码不能为空']

    if len(code) > MAX_CODE_CHARS:
        return [f'代码过长，最多 {MAX_CODE_CHARS} 字符']

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f'语法错误: {e}']

    validator = PlotCodeValidator()
    validator.visit(tree)
    # 去重，保留顺序
    seen = set()
    unique_errors = []
    for err in validator.errors:
        if err not in seen:
            seen.add(err)
            unique_errors.append(err)
    return unique_errors


def _safe_import(name: str, globals=None, locals=None, fromlist=(), level=0):
    if level and level > 0:
        raise ImportError('不允许相对导入')

    if name in ALLOWED_IMPORT_MODULES or any(name.startswith(f'{m}.') for m in ALLOWED_IMPORT_MODULES):
        return __import__(name, globals, locals, fromlist, level)
    raise ImportError(f'模块 {name} 不在白名单中')


def _execute_user_code(code: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
    import matplotlib.pyplot as plt
    import numpy as np
    import scipy

    safe_builtins = {
        'abs': abs,
        'all': all,
        'any': any,
        'bool': bool,
        'dict': dict,
        'enumerate': enumerate,
        'float': float,
        'int': int,
        'len': len,
        'list': list,
        'max': max,
        'min': min,
        'pow': pow,
        'print': print,
        'range': range,
        'round': round,
        'set': set,
        'sorted': sorted,
        'str': str,
        'sum': sum,
        'tuple': tuple,
        'zip': zip,
        '__import__': _safe_import,
    }

    globals_scope = {
        '__builtins__': safe_builtins,
        'task_data': task_data,
        'np': np,
        'plt': plt,
        'math': math,
        'statistics': statistics,
        'scipy': scipy,
    }
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
        compiled = compile(code, '<free-plot>', 'exec')
        # Use a single shared scope. With separate locals/globals, list comprehensions
        # may fail to resolve loop variables in some exec contexts.
        exec(compiled, globals_scope, globals_scope)

    fig = globals_scope.get('fig')
    if fig is None:
        fig = plt.gcf()

    if not getattr(fig, 'axes', None):
        raise RuntimeError('未检测到图像输出，请确认脚本包含 matplotlib 绘图语句。')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=160, facecolor='white', bbox_inches='tight')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    logs = stdout_buffer.getvalue().strip()
    errors = stderr_buffer.getvalue().strip()
    merged_logs = '\n'.join([s for s in [logs, errors] if s]).strip()

    return {
        'success': True,
        'image_base64': image_base64,
        'logs': merged_logs or '脚本执行成功。',
    }


def _plot_worker_loop(request_queue: Any, response_queue: Any):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        import scipy

        # 首次加载重库，后续请求复用该进程。
        _ = (plt, np, scipy)
        response_queue.put({'type': 'ready', 'success': True})
    except Exception:
        response_queue.put({'type': 'ready', 'success': False, 'error': traceback.format_exc(limit=2)})
        return

    while True:
        job = request_queue.get()
        if job is None:
            break

        job_id = job.get('job_id')
        job_type = job.get('type')

        try:
            if job_type == 'warmup':
                response_queue.put({'type': 'result', 'job_id': job_id, 'success': True, 'logs': '绘图环境预热完成。'})
                continue

            if job_type == 'run':
                result = _execute_user_code(job.get('code', ''), job.get('task_data', {}))
                response_queue.put({'type': 'result', 'job_id': job_id, **result})
                try:
                    import matplotlib.pyplot as plt
                    plt.close('all')
                except Exception:
                    pass
                continue

            response_queue.put({'type': 'result', 'job_id': job_id, 'success': False, 'error': f'未知任务类型: {job_type}'})
        except Exception:
            response_queue.put({
                'type': 'result',
                'job_id': job_id,
                'success': False,
                'error': traceback.format_exc(limit=3),
            })


def _stop_worker() -> None:
    global _worker_process, _worker_request_queue, _worker_response_queue
    if _worker_process is not None:
        try:
            if _worker_process.is_alive() and _worker_request_queue is not None:
                _worker_request_queue.put(None)
        except Exception:
            pass

        try:
            _worker_process.join(1)
        except Exception:
            pass

        if _worker_process.is_alive():
            _worker_process.terminate()
            _worker_process.join(1)

    _worker_process = None
    _worker_request_queue = None
    _worker_response_queue = None


def _ensure_worker() -> Dict[str, Any]:
    global _worker_process, _worker_request_queue, _worker_response_queue

    with _worker_lock:
        if _worker_process is not None and _worker_process.is_alive():
            return {'success': True}

        _stop_worker()
        ctx = multiprocessing.get_context('spawn')
        _worker_request_queue = ctx.Queue()
        _worker_response_queue = ctx.Queue()
        _worker_process = ctx.Process(target=_plot_worker_loop, args=(_worker_request_queue, _worker_response_queue), daemon=True)
        _worker_process.start()

        try:
            ready = _worker_response_queue.get(timeout=WARMUP_TIMEOUT_SECONDS)
        except Exception:
            _stop_worker()
            return {'success': False, 'error': '绘图环境启动超时，请稍后重试。'}

        if not ready.get('success'):
            _stop_worker()
            return {'success': False, 'error': ready.get('error', '绘图环境启动失败。')}

        return {'success': True}


def _run_worker_job(job_type: str, code: str = '', task_data: Dict[str, Any] = None, timeout: int = EXEC_TIMEOUT_SECONDS) -> Dict[str, Any]:
    task_data = task_data or {}

    ready = _ensure_worker()
    if not ready.get('success'):
        return {'success': False, 'error': ready.get('error', '绘图环境不可用。')}

    with _execute_lock:
        job_id = str(uuid.uuid4())
        _worker_request_queue.put({
            'type': job_type,
            'job_id': job_id,
            'code': code,
            'task_data': task_data,
        })

        try:
            result = _worker_response_queue.get(timeout=timeout)
        except Exception:
            _stop_worker()
            return {'success': False, 'error': f'执行超时（>{timeout}s），请简化脚本逻辑。'}

        if result.get('job_id') != job_id:
            return {'success': False, 'error': '执行结果不匹配，请重试。'}

        return result


def warmup_plot_worker() -> Dict[str, Any]:
    return _run_worker_job(job_type='warmup', timeout=WARMUP_TIMEOUT_SECONDS)


def execute_plot_code(code: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
    return _run_worker_job(job_type='run', code=code, task_data=task_data, timeout=EXEC_TIMEOUT_SECONDS)
