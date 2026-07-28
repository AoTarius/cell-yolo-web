"""
api.views 包

将原本单文件 views.py (~3452 行) 按功能领域拆分为独立模块：

    _helpers.py   — 公共工具函数（get_thread_prefix）
    auth.py       — 用户认证（登录/注册/信息修改/删除）
    video.py      — 视频管理（上传/列表/原始视频/删除/重命名）
    task.py       — 任务处理（创建/状态/结果/列表/重命名/删除）
    model.py      — 模型管理（列表/上传/删除/重命名）
    data.py       — 数据访问（标注视频/帧图片/导出/导入/细胞/3D轨迹）
    free_plot.py  — 自由绘图（代码执行/预热/示例模板）

所有视图通过本 __init__.py 重新导出，
保持 api/urls.py 中 `from . import views` 导入方式不变。
"""

# ── 公共工具 ──────────────────────────────────────────────
from ._helpers import get_thread_prefix  # noqa: F401

# ── 基础接口 ──────────────────────────────────────────────
from .data import test_api  # noqa: F401

# ── 用户认证 ──────────────────────────────────────────────
from .auth import (  # noqa: F401
    LoginView,
    RegisterView,
    UpdateUserView,
    UpdateUserPathsView,
    DeleteUserView,
)

# ── 视频管理 ──────────────────────────────────────────────
from .video import (  # noqa: F401
    UploadVideoView,
    OriginalVideoView,
    VideoListView,
    DeleteVideoView,
    RenameVideoView,
)

# ── 任务处理 ──────────────────────────────────────────────
from .task import (  # noqa: F401
    ProcessTaskView,
    TaskStatusView,
    TaskResultView,
    TaskListView,
    RenameTaskView,
    DeleteTaskView,
)

# ── 模型管理 ──────────────────────────────────────────────
from .model import (  # noqa: F401
    ModelListView,
    ModelUploadView,
    DeleteModelView,
    RenameModelView,
)

# ── 数据访问与可视化 ─────────────────────────────────────────
from .data import (  # noqa: F401
    AnnotatedVideoView,
    FrameImageView,
    ExportDataView,
    ExportTaskDataView,
    ImportDataPackageView,
    Trajectory3DImageView,
    get_cells_by_task,
    get_cell_detail,
)

# ── 自由绘图 ──────────────────────────────────────────────
from .free_plot import (  # noqa: F401
    FreePlotRunView,
    FreePlotWarmupView,
    FreePlotExamplesView,
)
