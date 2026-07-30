# CellTrack Web

细胞分割与追踪系统的 Web 应用，基于 YOLOv8 和 DeepSORT 实现。

## ✨ 功能特性

- **视频上传**: 支持 MP4、AVI、MOV 等格式的视频上传
- **细胞检测**: 使用 YOLOv8 进行细胞分割检测
- **细胞追踪**: 基于 DeepSORT 算法实现细胞轨迹追踪
- **参数自定义**: 支持调整置信度阈值、图像尺寸、输出帧率等参数
- **实时进度**: 通过 WebSocket 实时推送处理进度
- **结果展示**: 标注视频播放、细胞统计、轨迹数据查看
- **自由绘图**: 支持自定义 Python 代码分析细胞追踪数据
  - 在线 Python 代码编辑器（基于 CodeMirror）
  - 内置 10+ 数据分析示例模板
  - 支持多种可视化类型（折线图、散点图、热力图、3D 图等）
  - 实时代码预览和执行
- **视频播放器功能**:
  - 双视频对比播放（原始视频 vs 标注视频）
  - 支持并排/上下布局切换
  - 播放速率调整（0.25x, 0.5x, 0.75x, 1x, 1.5x, 2x）
  - 精确帧控制（前进/后退一帧）
  - 同步播放/暂停控制
- **视图模式**: 整体视图/细化视图切换
  - 整体视图：展示完整的统计卡片、视频播放器、群体图表和细胞列表
  - 细化视图：左侧标注视频播放器 + 逐帧分析控制，右侧详细数据分析
- **数据导出**: 支持 CSV 和 JSON 格式数据导出
- **视频下载**: 下载标注后的视频文件

## 🏗️ 项目结构

```
web/
├── backend/                 # Django 后端
│   ├── .user-storage/      # 默认用户信息存储文件夹
│   ├── api/                # API 应用
│   │   ├── services/       # 业务逻辑服务
│   │   │   └── video_processor.py  # 视频处理服务
│   │   ├── management/     # Django 管理命令
│   │   │   └── commands/
│   │   │       └── purge_soft_deleted.py  # 软删除数据清理
│   │   ├── migrations/     # 数据库迁移
│   │   ├── views/           # API 视图包（按功能拆分）
│   │   │   ├── __init__.py      # 包初始化，重导出所有视图
│   │   │   ├── _helpers.py      # 公共工具函数
│   │   │   ├── auth.py          # 用户认证视图
│   │   │   ├── video.py         # 视频管理视图
│   │   │   ├── task.py          # 任务处理视图
│   │   │   ├── model.py         # 模型管理视图
│   │   │   ├── data.py          # 数据访问与可视化视图
│   │   │   └── free_plot.py     # 自由绘图视图
│   │   ├── urls.py         # API 路由
│   │   ├── websocket.py    # WebSocket 消费者
│   │   ├── routing.py      # WebSocket 路由
│   │   └── ai.py           # AI 相关接口
│   ├── backend/            # Django 配置
│   │   ├── settings.py     # 设置文件（已配置 sys.path）
│   │   ├── urls.py         # 主路由
│   │   └── asgi.py         # ASGI 配置（WebSocket）
│   ├── scripts/            # 数据库初始化脚本
│   │   ├── init_db.py      # 数据库初始化
│   │   ├── init_data.py    # 初始数据导入
│   │   └── rebuild_db.py   # 数据库重建
│   ├── runs/               # 模型训练输出
│   ├── media/              # 媒体文件存储
│   │   └── tasks/          # 任务数据
│   ├── requirements.txt    # Python 依赖
│   └── manage.py           # Django 管理脚本
├── libs/                   # 本地库文件
│   ├── ultralytics/        # YOLOv8 和 DeepSORT 库
│   │   ├── yolo/           # YOLO 核心模块
│   │   ├── hub/            # HUB 模块
│   │   ├── models/         # 模型定义
│   │   ├── nn/             # 神经网络模块
│   │   ├── setup.py        # 安装配置
│   │   └── __init__.py     # 包初始化
│   └── tif-mp4/           # 图像转视频工具
│       ├── convert.py      # 转换脚本
│       ├── README.md       # 工具说明
│       └── output/         # 输出目录
├── frontend/               # Vue 前端
│   ├── src/
│   │   ├── api/            # API 服务层
│   │   ├── components/     # Vue 组件
│   │   │   ├── analysis/   # 分析结果组件
│   │   │   │   ├── cell-details/    # 细胞详情
│   │   │   │   ├── chart-drawing/   # 图表绘制
│   │   │   │   ├── frame-analysis/  # 帧分析
│   │   │   │   ├── layout/          # 布局组件
│   │   │   │   └── video-comparison/# 视频对比
│   │   │   ├── ai/             # AI 相关组件
│   │   │   ├── common/         # 通用组件
│   │   │   └── compare/        # 对比组件
│   │   ├── composables/    # 组合式函数
│   │   ├── lib/            # 工具库
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── types/          # TypeScript 类型定义
│   │   ├── utils/          # 工具函数
│   │   ├── views/          # 页面视图
│   │   │   ├── analysis/   # 分析相关页面
│   │   │   │   ├── FreePlotView.vue    # 自由绘图
│   │   │   │   ├── ProgressView.vue    # 进度展示
│   │   │   │   └── UploadView.vue      # 上传页面
│   │   │   ├── auth/       # 认证相关页面
│   │   │   ├── compare/    # 对比相关页面
│   │   │   ├── home/       # 首页
│   │   │   ├── import/     # 导入相关页面
│   │   │   └── resource/   # 资源相关页面
│   │   ├── router/         # 路由配置
│   │   ├── App.vue         # 根组件
│   │   └── main.ts         # 入口文件
│   ├── docs/               # 前端文档
│   │   ├── API-INTEGRATION.md
│   │   ├── colors-analysis.md
│   │   └── DEVELOPMENT.md
│   └── package.json        # Node 依赖
├── docs/                   # 项目文档
│   ├── examples/          # 数据分析示例代码
│   │   ├── case01_data_structure_and_basics.py
│   │   ├── case02_histogram_speed_distribution.py
│   │   ├── case03_scatter_multiframe_positions.py
│   │   ├── case04_heatmap_density_multiframe.py
│   │   ├── case05_normalized_trajectories.py
│   │   ├── case06_multi_metric_timeseries.py
│   │   ├── case07_distribution_panels.py
│   │   ├── case08_trajectory_3d_lines.py
│   │   ├── case09_histogram_3d_multiframe.py
│   │   └── case10_shape_activity_dashboard.py
│   ├── 软件需求分析文档_v1.md
│   ├── 项目日志.md
│   ├── 原型设计文档.md
│   └── 自由绘图MVP设计说明.md
├── .gitignore
├── QUICK-START.md
└── README.md
```

## 📚 技术栈

### 前端
- Vue 3.5.27 (Composition API)
- TypeScript 5.9.3
- Vite 7.3.1
- TailwindCSS 4.1.18
- Vue Router 5.0.1
- Pinia 3.0.4
- Axios 1.13.5
- VueUse 14.2.1
- Lucide Icons 0.563.0
- ECharts 5.6.0 (数据可视化)
- ECharts GL 2.0.9 (3D 可视化)
- @codemirror/lang-python (代码编辑器)
- highlight.js (代码高亮)
- marked (Markdown 渲染)
- jszip (ZIP 文件处理)
- Node.js 版本要求: ^20.19.0 || >=22.12.0

### 后端
- Django 4.2.28
- Django REST Framework 3.15.2
- Channels 4.2.2 (WebSocket)
- OpenCV 4.13.0.92
- NumPy 1.24.4
- SciPy 1.10.1
- Pandas 2.0.3
- Polars 1.8.2
- django-cors-headers 4.4.0
- python-dotenv 1.0.1
- PyMySQL 1.1.2
- MySQL

### AI 模型

#### 当前启用（默认追踪引擎）
- **ultralytics 8.4.21** (本地库，位于 `web/libs/ultralytics`)
  - YOLOv8 (细胞分割/检测)
- **deep-sort-realtime 1.3.2** (目标追踪)
- PyTorch 2.4.1
- torchvision 0.19.1

#### 已实现，待条件成熟后启用
- **HFM-Tracker** (Hybrid Feature Matching Tracker)
  - 专为细胞追踪设计的检测+跟踪一体化算法
  - 核心模块：Contour Attention (CA) 轮廓检测 + Adaptive Confusion Matrix (ACM) 自适应匹配
  - 暂未启用的原因：C 扩展编译复杂、硬件要求较高（推荐 32GB RAM），与项目"科研人员便捷可用"理念暂有冲突
  - 详见：[`docs/v2/HFMTracker技术笔记.md`](./docs/v2/HFMTracker技术笔记.md)

### 依赖说明
项目使用本地化的 ultralytics 库，通过以下方式配置：
1. `web/libs/ultralytics/` - 本地 ultralytics 源码
2. `.pth` 文件 - 自动将 web/libs 目录添加到 Python 路径
3. `backend/settings.py` - Django 配置中自动添加路径

**Python 版本要求**: 推荐使用 Python 3.8
**Node.js 版本要求**: ^20.19.0 || >=22.12.0

## 🔌 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/test/` | 测试接口 |
| POST | `/api/upload/` | 上传视频 |
| POST | `/api/process/` | 启动处理任务 |
| GET | `/api/status/:task_id/` | 查询任务状态 |
| GET | `/api/result/:task_id/` | 获取处理结果 |
| GET | `/api/video/:task_id/` | 获取标注视频 |
| WS | `/ws/task/:task_id/` | WebSocket 实时进度 |

## 🛠️ 工具

### 自由绘图功能

位置: `web/docs/examples/`

提供 10+ 个数据分析示例模板，支持用户使用 Python 代码自定义分析细胞追踪数据。

**可用的数据变量**：
- `task_data`: 包含完整的任务追踪数据，包括 frame、track_id、area、speed、position 等字段

**示例模板**：
- `case01_data_structure_and_basics.py` - 数据结构展示和基础处理
- `case02_histogram_speed_distribution.py` - 速度分布直方图
- `case03_scatter_multiframe_positions.py` - 多帧位置散点图
- `case04_heatmap_density_multiframe.py` - 多帧密度热力图
- `case05_normalized_trajectories.py` - 归一化轨迹分析
- `case06_multi_metric_timeseries.py` - 多指标时间序列
- `case07_distribution_panels.py` - 分布面板图
- `case08_trajectory_3d_lines.py` - 3D 轨迹线
- `case09_histogram_3d_multiframe.py` - 3D 直方图
- `case10_shape_activity_dashboard.py` - 形状与活动仪表板

**使用方法**：
1. 在分析结果页面点击"自由绘图"按钮
2. 从模板列表中选择一个示例或编写自定义代码
3. 点击"运行"按钮执行代码
4. 查看生成的可视化结果

### TIF 转 MP4 工具

位置: `web/libs/tif-mp4/`

将图像序列（如 tif、png、jpg 等）组合成 MP4 视频文件。

**使用方法:**
```bash
cd web/libs/tif-mp4
python3 convert.py --input /path/to/images --fps 10
```

详细说明见: [web/libs/tif-mp4/README.md](./libs/tif-mp4/README.md)

### 软删除数据清理命令

位置: `web/backend/api/management/commands/purge_soft_deleted.py`

清理数据库中已软删除但超过保留期的数据，避免数据无限增长。

**使用方法:**
```bash
cd web/backend
python manage.py purge_soft_deleted [选项]
```

**选项说明:**
- `--days N`: 保留天数，默认为30天（只删除N天前的软删除数据）
- `--dry-run`: 只显示将要删除的记录，不实际删除
- `--force`: 强制删除所有软删除记录，不考虑时间限制

**使用示例:**
```bash
# 删除30天前的软删除数据
python manage.py purge_soft_deleted --days 30

# 测试运行（不实际删除）
python manage.py purge_soft_deleted --days 30 --dry-run

# 强制删除所有软删除记录
python manage.py purge_soft_deleted --force

# 查看所有软删除记录（不删除）
python manage.py purge_soft_deleted --force --dry-run
```

**定时任务配置:**
建议配置定时任务定期清理软删除数据：

```bash
# 使用 crontab 每天凌晨2点执行
0 2 * * * cd /path/to/cell-yolo/web/backend && python manage.py purge_soft_deleted --days 30 >> /var/log/cell_yolo_cleanup.log 2>&1
```

## 🚀 快速开始

详细的安装和启动步骤请参考: [QUICK-START.md](./QUICK-START.md)

## ⚠️ 注意事项

1. **版本要求**:
   - Python: 推荐 3.10-3.12（当前环境 3.13.11 也可使用）
   - Node.js: ^20.19.0 || >=22.12.0
2. **MySQL 数据库**:
   - 需要先安装并启动 MySQL 服务
   - macOS: `brew install mysql && brew services start mysql`
   - Windows: 下载 MySQL Installer 并安装
   - 配置 `.env` 文件中的数据库连接信息
   - 运行 `scripts/init_db.py` 初始化数据库表结构
3. **依赖安装**:
   - 需要安装 PyMySQL 和 python-dotenv
   - 需要安装 OpenCV 和 Channels 支持 WebSocket
   - 需要安装 PyTorch 和 torchvision
   - ultralytics 使用本地库（`web/libs/ultralytics`）或通过 pip 安装 ultralytics==8.4.21
   - deep-sort-realtime==1.3.2
4. **Python 路径配置**:
   - 项目自动通过 `.pth` 文件和 `settings.py` 配置 Python 路径
   - VSCode 用户：已配置 `.vscode/settings.json`，可能需要重新加载窗口
5. **Conda 环境**: 推荐使用 Conda 虚拟环境，便于管理依赖
6. **内存要求**: 视频处理需要较多内存，建议 8GB+ RAM
7. **处理时间**: 视频处理可能需要几分钟到几十分钟

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
