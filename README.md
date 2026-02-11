# CellTrack Web 快速启动指南

## 📋 前置准备

在开始之前，请确保已安装以下软件：

- **Node.js**: v20.19.0+ 或 v22.12.0+
- **Python**: 3.11+
- **Conda**: Anaconda 或 Miniconda（推荐）
- **Git**: 用于版本控制（可选）

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

### 第三步：安装前端 npm 包

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

### 第四步：初始化数据库

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


## 🌐 访问应用

启动成功后，可以通过以下地址访问：

- **前端应用**: http://localhost:5173
- **后端 API**: http://localhost:8000/api/test/
- **Django 管理后台**: http://localhost:8000/admin/

## 🛤️ 现有路由

前端当前配置了以下路由：

| 路径 | 名称 | 组件 | 说明 |
|------|------|------|------|
| `/` | cellTracking | CellTrackingView | 细胞追踪主页面 |
| `/test` | test | HomeView | 测试页面，用于测试前后端连接 |

## ✅ 验证前后端连接

访问测试页面验证前后端是否正常连接：

1. 在浏览器中打开 http://localhost:5173/test
2. 点击页面上的"测试后端连接"按钮
3. 如果看到绿色成功消息，说明前后端连接正常

你也可以直接访问后端 API 测试端点：
- http://localhost:8000/api/test/

应该返回 JSON 响应：
```json
{
  "message": "Django + Vue 前后端分离项目已启动！",
  "status": "success"
}
```

## 🛠️ 常用开发命令

### 前端开发

```bash
cd frontend

# 启动开发服务器（热重载）
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview

# 代码检查和修复
npm run lint
```

### 后端开发

```bash
cd backend

# 确保激活了虚拟环境
conda activate cell-yolo

# 启动开发服务器
python manage.py runserver

# 创建数据库迁移文件
python manage.py makemigrations

# 执行数据库迁移
python manage.py migrate

# 进入 Django Shell
python manage.py shell

# 创建新的 Django 应用
python manage.py startapp app_name
```

## ⚠️ 常见问题

### Q1: npm install 失败

**解决方案：**
```bash
# 清除 npm 缓存
npm cache clean --force

# 删除 node_modules 和 package-lock.json
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

### Q2: Python 依赖安装失败

**解决方案：**
```bash
# 确保虚拟环境已激活
conda activate cell-yolo

# 升级 pip
pip install --upgrade pip

# 重新安装依赖
pip install -r requirements.txt
```

### Q3: 端口被占用

**后端 (8000)：**
```bash
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**前端 (5173)：**
```bash
# Linux/Mac
lsof -ti:5173 | xargs kill -9

# Windows
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

### Q4: CORS 错误

确保 Django 的 CORS 设置正确（backend/backend/settings.py）：
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]
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
- django-cors-headers
- python-dotenv
- SQLite
