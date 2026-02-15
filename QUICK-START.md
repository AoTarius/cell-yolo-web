## 🚀 快速开始

### 第一步：创建并激活 Python 虚拟环境

使用 Conda 创建名为 `cell-yolo` 的虚拟环境：

```bash
# 创建虚拟环境（指定 Python 版本）
conda create -n cell-yolo python=3.8 -y

# 激活虚拟环境
conda activate cell-yolo
```

### 第二步：安装 Python 依赖

进入 backend 目录并安装所需的 Python 库：

```bash
cd backend
pip install -r requirements.txt
```

需要安装的主要依赖包括：
- Django >= 4.2.28
- djangorestframework >= 3.15.0
- django-cors-headers >= 4.4.0
- python-dotenv >= 1.0.0
- **channels >= 4.0.0** (WebSocket 支持)
- **opencv-python >= 4.8.0** (视频处理)
- **numpy >= 1.24.0** (数值计算)
- **torch >= 1.7.0** (PyTorch)
- **torchvision >= 0.8.1** (PyTorch 视觉库)
- **psutil** (系统工具)
- **tqdm** (进度条)
- **scipy** (科学计算)
- **PyYAML** (配置解析)
- **requests** (HTTP 请求)
- **Pillow** (图像处理)
- **matplotlib** (绘图)

**注意**: ultralytics 和 deep_sort_pytorch 已作为本地库包含在 `web/libs/ultralytics` 目录中，无需额外安装。项目会自动通过以下方式配置 Python 路径：
1. `.pth` 文件（在 Conda 环境的 site-packages 中）
2. `backend/settings.py` 中的 sys.path 配置
3. VSCode 的 `.vscode/settings.json` 配置

### 第三步：配置 YOLO 模型

确保 YOLO 模型文件已放置在正确位置：

```bash
# 检查模型文件是否存在
ls backend/models/yolov8s-seg.pt
```

如果模型文件不存在，需要从项目根目录复制：

```bash
# 从项目根目录的 models 文件夹复制
cp models/yolov8s-seg.pt backend/models/
```

### 第三步（可选）：验证 ultralytics 本地库

项目使用本地化的 ultralytics 库，可以通过以下命令验证：

```bash
# 在 conda 环境中测试
python -c "import ultralytics; print(f'ultralytics 版本: {ultralytics.__version__}')"
python -c "from ultralytics import YOLO; print('✓ YOLO 导入成功')"
python -c "from deep_sort_pytorch.deep_sort import DeepSort; print('✓ DeepSORT 导入成功')"
```

如果遇到导入错误，请检查：
1. 确认已激活 conda 环境：`conda activate cell-yolo`
2. 检查 `.pth` 文件是否存在：`ls ~/miniconda3/envs/cell-yolo/lib/python3.8/site-packages/ultralytics_local.pth`
3. 如果使用 VSCode，重新加载窗口：`Cmd + Shift + P` → "Reload Window"

### 第四步：安装前端 npm 包

进入 frontend 目录并安装 Node.js 依赖：

```bash
cd ../frontend
npm install
```

主要依赖包括：
- Vue 3.5.27
- TypeScript 5.9.3
- Vite 7.3.1
- TailwindCSS 4.1.18
- Vue Router 5.0.1
- Pinia 3.0.4
- Axios 1.13.5

### 第五步：初始化数据库

返回 backend 目录并执行数据库迁移：

```bash
cd ../backend
python manage.py migrate
```

（可选）创建超级用户以访问 Django 管理后台：

```bash
python manage.py createsuperuser
```

## ▶️ 启动前后端服务

### 方式一：同时启动（推荐）

在 web 目录下，打开两个终端：

**终端 1 - 启动后端：**
```bash
cd backend
conda activate cell-yolo
python manage.py runserver
```

后端将运行在: http://localhost:8000

**终端 2 - 启动前端：**
```bash
cd frontend
npm run dev
```

前端将运行在: http://localhost:5173

## 🌐 计问应用

启动成功后，可以通过以下地址访问：

- **前端应用**: http://localhost:5173
- **后端 API**: http://localhost:8000/api/test/
- **Django 管理后台**: http://localhost:8000/admin/

## 📋 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/test/` | 测试接口 |
| POST | `/api/upload/` | 上传视频 |
| POST | `/api/process/` | 启动处理任务 |
| GET | `/api/status/:task_id/` | 查询任务状态 |
| GET | `/api/result/:task_id/` | 获取处理结果 |
| GET | `/api/video/:task_id/` | 获取标注视频 |
| WS | `/ws/task/:task_id/` | WebSocket 实时进度 |

## 🛠️ 工具使用

### TIF 转 MP4 工具

将图像序列转换为视频文件，用于测试系统。

**使用方法:**
```bash
cd web/tools/tif-mp4
python3 convert.py --input /path/to/images --fps 10
```

**示例:**
```bash
# 转换指定目录的图片
python3 convert.py --input /path/to/images

# 设置帧率为 15
python3 convert.py --input /path/to/images --fps 15

# 指定输出文件名
python3 convert.py --input /path/to/images --output my_video.mp4
```

详细说明见: [web/tools/tif-mp4/README.md](./tools/tif-mp4/README.md)