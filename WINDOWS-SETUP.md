# Windows 环境安装指南

由于 WSL 和 Windows 的 Python/Conda 环境不互通，需要在 Windows 环境下完成以下步骤。

## 需要在 Windows 完成的步骤

### 1. 打开 Windows PowerShell 或命令提示符

按 `Win + X`，选择"Windows PowerShell"或"命令提示符"。

### 2. 进入项目目录

```powershell
cd D:\VSCode_Data\Project\cellTrack\web
```

### 3. 安装 Python 依赖

#### 选项 A：使用 conda 环境 cell-yolo（推荐）

```powershell
# 激活 conda 环境
conda activate cell-yolo

# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt
```

#### 选项 B：使用 Python venv

```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt
```

### 4. 初始化数据库

```powershell
# 确保在 backend 目录下，并且已激活环境

# 执行数据库迁移
python manage.py migrate

# 输出示例：
# Operations to perform:
#   Apply all migrations: admin, auth, contenttypes, sessions
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   ...
```

### 5. 创建超级用户（可选）

```powershell
python manage.py createsuperuser

# 按提示输入：
# - 用户名
# - 邮箱（可选，直接回车跳过）
# - 密码（输入时不显示）
# - 确认密码
```

### 6. 测试后端启动

```powershell
python manage.py runserver

# 应该看到类似输出：
# Watching for file changes with StatReloader
# Performing system checks...
#
# System check identified no issues (0 silenced).
# February 11, 2026 - 14:00:00
# Django version 5.1.x, using settings 'backend.settings'
# Starting development server at http://127.0.0.1:8000/
# Quit the server with CTRL-BREAK.
```

按 `Ctrl + C` 停止服务器。

### 7. 启动完整项目

打开两个 PowerShell 窗口：

**窗口 1 - 后端**
```powershell
cd D:\VSCode_Data\Project\cellTrack\web\backend
conda activate cell-yolo  # 或 venv\Scripts\activate
python manage.py runserver
```

**窗口 2 - 前端**
```powershell
cd D:\VSCode_Data\Project\cellTrack\web\frontend
npm run dev
```

### 8. 访问应用

打开浏览器访问：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000/api/test/
- Django 管理后台：http://localhost:8000/admin/

## 使用启动脚本（简化版）

在 `web` 目录下运行：

```powershell
.\start-dev.bat
```

这会自动启动前端和后端服务。

## 验证安装

### 1. 检查后端 API

在浏览器中访问：http://localhost:8000/api/test/

应该看到 JSON 响应：
```json
{
  "message": "Django + Vue 前后端分离项目已启动！",
  "status": "success"
}
```

### 2. 测试前后端通信

在前端页面（http://localhost:5173）点击"测试后端连接"按钮，应该显示成功消息。

## 常见问题

### Q1: pip 找不到命令

**解决方案：**
- 确保已安装 Python
- 在安装 Python 时勾选"Add Python to PATH"
- 或者使用完整路径：`C:\Python312\Scripts\pip.exe`

### Q2: conda 找不到命令

**解决方案：**
- 确保已安装 Anaconda 或 Miniconda
- 打开 "Anaconda Prompt" 而不是普通的 PowerShell
- 或者在 PowerShell 中初始化 conda：
  ```powershell
  conda init powershell
  ```

### Q3: 虚拟环境激活失败

**解决方案（PowerShell 执行策略）：**
```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q4: 端口被占用

**Django (8000)：**
```powershell
# 查找占用端口的进程
netstat -ano | findstr :8000

# 结束进程（PID 是上一步显示的数字）
taskkill /PID <PID> /F
```

**Vite (5173)：**
```powershell
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

### Q5: Django 数据库错误

**解决方案：**
```powershell
# 删除数据库文件
del backend\db.sqlite3

# 重新迁移
cd backend
python manage.py migrate
```

## 依赖包说明

### 后端（requirements.txt）

- `Django>=5.1.0` - Web 框架
- `djangorestframework>=3.15.0` - REST API 工具包
- `django-cors-headers>=4.4.0` - CORS 跨域支持
- `python-dotenv>=1.0.0` - 环境变量管理

### 前端（package.json）

- `vue@^3.x` - 前端框架
- `typescript` - 类型系统
- `vite@^7.x` - 构建工具
- `tailwindcss@^4.x` - CSS 框架
- `axios` - HTTP 客户端
- `pinia` - 状态管理
- `vue-router` - 路由管理

## 下一步

安装完成后，阅读主 README.md 了解：
- 项目结构
- 开发指南
- API 文档

## 技术支持

如遇到其他问题，请查看：
1. Django 文档：https://docs.djangoproject.com/
2. Vue 3 文档：https://cn.vuejs.org/
3. Vite 文档：https://cn.vitejs.dev/
