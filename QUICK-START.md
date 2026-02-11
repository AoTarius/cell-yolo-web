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