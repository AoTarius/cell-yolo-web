# CellTrack Web

细胞分割与追踪系统的 Web 应用，基于 YOLOv8 和 DeepSORT 实现。

## ✨ 功能特性

- **视频上传**: 支持 MP4、AVI、MOV 等格式的视频上传
- **细胞检测**: 使用 YOLOv8 进行细胞分割检测
- **细胞追踪**: 基于 DeepSORT 算法实现细胞轨迹追踪
- **参数自定义**: 支持调整置信度阈值、图像尺寸、输出帧率等参数
- **实时进度**: 通过 WebSocket 实时推送处理进度
- **结果展示**: 标注视频播放、细胞统计、轨迹数据查看
- **数据导出**: 支持 CSV 和 JSON 格式数据导出
- **视频下载**: 下载标注后的视频文件

## 🏗️ 项目结构

```
web/
├── backend/                 # Django 后端
│   ├── api/                # API 应用
│   │   ├── services/       # 业务逻辑服务
│   │   │   ├── video_processor.py  # 视频处理服务
│   │   │   └── convert_results.py  # YOLO 追踪结果转换
│   │   ├── views.py        # API 视图
│   │   ├── urls.py         # API 路由
│   │   ├── websocket.py    # WebSocket 消费者
│   │   └── routing.py      # WebSocket 路由
│   ├── backend/            # Django 配置
│   │   ├── settings.py     # 设置文件（已配置 sys.path）
│   │   ├── urls.py         # 主路由
│   │   └── asgi.py         # ASGI 配置（WebSocket）
│   ├── models/             # YOLO 模型文件
│   ├── media/              # 媒体文件存储
│   │   └── tasks/          # 任务数据
│   ├── requirements.txt    # Python 依赖
│   └── manage.py           # Django 管理脚本
├── libs/                   # 本地库文件
│   ├── ultralytics/        # YOLOv8 和 DeepSORT 库
│   │   ├── yolo/           # YOLO 核心模块
│   │   │   └── v8/segment/deep_sort_pytorch/  # DeepSORT 追踪
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
│   │   │   ├── UploadPanel.vue      # 上传组件
│   │   │   ├── ResultPanel.vue      # 结果展示组件
│   │   │   ├── CellDetailPanel.vue  # 细胞详情组件
│   │   │   └── ...
│   │   ├── composables/    # 组合式函数
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── views/          # 页面视图
│   │   └── router/         # 路由配置
│   └── package.json        # Node 依赖
├── docs/                   # 项目文档
└── .vscode/                # VSCode 配置
    └── settings.json       # Python 路径配置
```

## 📚 技术栈

### 前端
- Vue 3 (Composition API)
- TypeScript
- Vite
- TailwindCSS v4
- Vue Router
- Pinia
- Axios
- VueUse
- Lucide Icons

### 后端
- Django 5.1+
- Django REST Framework
- Channels (WebSocket)
- OpenCV (cv2)
- NumPy
- django-cors-headers
- python-dotenv
- SQLite

### AI 模型
- **ultralytics 8.0.3** (本地库，位于 `web/libs/ultralytics`)
  - YOLOv8 (细胞分割)
  - DeepSORT (目标追踪)
- PyTorch 2.4.1+
- torchvision 0.19.1+

### 依赖说明
项目使用本地化的 ultralytics 库，通过以下方式配置：
1. `web/libs/ultralytics/` - 本地 ultralytics 源码
2. `.pth` 文件 - 自动将 web/libs 目录添加到 Python 路径
3. `backend/settings.py` - Django 配置中自动添加路径

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

### TIF 转 MP4 工具

位置: `web/libs/tif-mp4/`

将图像序列（如 tif、png、jpg 等）组合成 MP4 视频文件。

**使用方法:**
```bash
cd web/libs/tif-mp4
python3 convert.py --input /path/to/images --fps 10
```

详细说明见: [web/libs/tif-mp4/README.md](./libs/tif-mp4/README.md)

## 🚀 快速开始

详细的安装和启动步骤请参考: [QUICK-START.md](./QUICK-START.md)

## 📖 文档

- [软件需求分析文档](./docs/软件需求分析文档_v1.md)
- [项目日志](./docs/项目日志.md)
- [原型设计文档](./docs/原型设计文档.md)

## ⚠️ 注意事项

1. **YOLO 模型**: 确保 `web/backend/models/` 目录下有 `yolov8s-seg.pt` 模型文件
2. **依赖安装**:
   - 需要安装 OpenCV 和 Channels 支持 WebSocket
   - 需要安装 PyTorch 和 torchvision
   - ultralytics 和 deep_sort_pytorch 使用本地库（`web/libs/ultralytics`）
3. **Python 路径配置**:
   - 项目自动通过 `.pth` 文件和 `settings.py` 配置 Python 路径
   - VSCode 用户：已配置 `.vscode/settings.json`，可能需要重新加载窗口
4. **Conda 环境**: 推荐使用 Conda 虚拟环境，便于管理依赖
5. **内存要求**: 视频处理需要较多内存，建议 8GB+ RAM
6. **处理时间**: 视频处理可能需要几分钟到几十分钟

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
