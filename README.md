# Vue 3 + Django 全栈项目

现代化前后端分离架构，基于 Vite + Vue 3 + Django REST Framework。

## 环境要求

- **Node.js**: v20.19.0+ 或 v22.12.0+（推荐）
  - 当前 WSL 环境使用 v18.19.1，构建时会有问题
  - 建议在 Windows 环境下使用更新的 Node.js 版本
- **Python**: 3.11+
- **npm**: 9.0+

## 项目结构

```
web/
├── frontend/          # Vue 3 前端项目
│   ├── src/
│   │   ├── assets/    # 静态资源
│   │   ├── components/# 组件
│   │   ├── router/    # 路由
│   │   ├── stores/    # Pinia 状态管理
│   │   └── views/     # 页面视图
│   ├── vite.config.ts # Vite 配置
│   └── package.json
├── backend/           # Django 后端项目
│   ├── backend/       # Django 主配置
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── api/           # API 应用
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── models.py
│   ├── manage.py
│   └── requirements.txt
└── venv/              # Python 虚拟环境
```

## 技术栈

### 前端
- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全
- **Vite** - 下一代前端构建工具
- **TailwindCSS v4** - 原子化 CSS 框架
- **Pinia** - Vue 官方状态管理
- **Vue Router** - 官方路由管理器
- **Axios** - HTTP 客户端
- **VueUse** - Vue 组合式函数集合
- **Lucide Vue** - 图标库

### 后端
- **Django 5.1+** - Python Web 框架
- **Django REST Framework** - RESTful API 工具包
- **django-cors-headers** - CORS 跨域支持
- **python-dotenv** - 环境变量管理
- **SQLite** - 开发数据库

## 安装和运行

### ⚠️ 重要提示：WSL 环境限制

由于 WSL 和 Windows 的 Python/Conda 环境不互通，需要在 Windows 环境下完成 Python 依赖安装。

### 在 Windows 环境下完成以下步骤：

#### 1. 安装 Python 依赖

打开 Windows PowerShell 或命令提示符，进入项目目录：

```powershell
# 进入项目目录
cd D:\VSCode_Data\Project\cellTrack\web

# 创建虚拟环境（如果使用 conda 环境 cell-yolo，跳过这一步）
python -m venv venv

# 激活虚拟环境
# 如果使用 venv：
venv\Scripts\activate
# 如果使用 conda：
conda activate cell-yolo

# 安装 Django 依赖
cd backend
pip install -r requirements.txt

# 初始化数据库
python manage.py migrate

# 创建超级用户（可选）
python manage.py createsuperuser
```

#### 2. 启动开发服务器

**方式一：使用启动脚本（推荐）**

```powershell
# 在 web 目录下运行
start-dev.bat
```

**方式二：手动启动**

打开两个终端：

终端 1 - 启动 Django 后端：
```powershell
cd D:\VSCode_Data\Project\cellTrack\web\backend
# 激活环境（venv 或 conda）
venv\Scripts\activate  # 或 conda activate cell-yolo
python manage.py runserver
```

终端 2 - 启动 Vue 前端：
```powershell
cd D:\VSCode_Data\Project\cellTrack\web\frontend
npm run dev
```

### 3. 访问应用

- **前端应用**: http://localhost:5173
- **后端 API**: http://localhost:8000/api/test/
- **Django 管理后台**: http://localhost:8000/admin/

## 开发指南

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview

# 运行测试
npm run test

# 代码检查
npm run lint
```

### 后端开发

```bash
cd backend

# 激活虚拟环境
source ../venv/bin/activate  # Linux/Mac
venv\Scripts\activate        # Windows

# 创建新应用
python manage.py startapp app_name

# 创建数据库迁移
python manage.py makemigrations

# 执行数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver

# 进入 Django Shell
python manage.py shell
```

## 环境变量配置

复制 `.env.example` 为 `.env` 并配置：

```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件：
```
SECRET_KEY=your-secret-key-here
DEBUG=True
```

## API 测试

前端已配置测试页面，点击"测试后端连接"按钮即可验证前后端通信。

API 端点：
- `GET /api/test/` - 测试连接

## 常见问题

### 1. 前端无法连接后端

确保：
- Django 服务运行在 `http://localhost:8000`
- CORS 配置正确（已在 settings.py 中配置）
- 浏览器控制台无跨域错误

### 2. Node.js 版本警告

当前使用 Node.js v18.19.1，推荐升级到 v20.19.0+ 以获得更好的支持。

### 3. Python 环境问题

如果在 WSL 中遇到 Python 环境问题，请在 Windows 环境下操作。

## 项目特性

✅ 前后端分离架构
✅ TypeScript 类型安全
✅ 现代化 UI 框架（TailwindCSS v4）
✅ RESTful API 设计
✅ CORS 跨域支持
✅ 热重载开发体验
✅ 生产环境优化

## 下一步计划

- [ ] 添加用户认证系统
- [ ] 实现文件上传功能
- [ ] 集成数据库 ORM
- [ ] 添加单元测试
- [ ] 配置 Docker 部署
- [ ] 添加 CI/CD 流程

## License

MIT License
