# 快速启动指南

## 🚀 5 分钟快速开始

### 📋 前置条件检查

- ✅ Node.js v20.19.0+ 或 v22.12.0+
- ✅ Python 3.11+
- ✅ Git（可选）

### 🔧 快速安装（Windows 环境）

打开 PowerShell，执行以下命令：

```powershell
# 1. 进入项目目录
cd D:\VSCode_Data\Project\cellTrack\web

# 2. 激活 Python 环境
conda activate cell-yolo
# 或者
# python -m venv venv
# venv\Scripts\activate

# 3. 安装后端依赖
cd backend
pip install -r requirements.txt
python manage.py migrate

# 4. 返回 web 目录
cd ..
```

### ▶️ 启动项目

**方式 1：一键启动（推荐）**
```powershell
.\start-dev.bat
```

**方式 2：手动启动**

打开两个 PowerShell 窗口：

窗口 1：
```powershell
cd D:\VSCode_Data\Project\cellTrack\web\backend
conda activate cell-yolo
python manage.py runserver
```

窗口 2：
```powershell
cd D:\VSCode_Data\Project\cellTrack\web\frontend
npm run dev
```

### 🌐 访问应用

- **前端页面**: http://localhost:5173
- **后端 API**: http://localhost:8000/api/test/
- **管理后台**: http://localhost:8000/admin/

### ✅ 验证安装

1. 访问 http://localhost:5173
2. 点击"测试后端连接"按钮
3. 看到绿色成功消息 ✓

### ⚠️ 常见问题

**Q: 前端无法启动**
```powershell
# 检查 Node 版本
node -v  # 应该 >= 20.19.0

# 如果版本太低，升级 Node.js
# 访问 https://nodejs.org/
```

**Q: 后端无法启动**
```powershell
# 检查 Python 版本
python --version  # 应该 >= 3.11

# 重新安装依赖
pip install -r backend/requirements.txt
```

**Q: 端口被占用**
```powershell
# 查找并关闭占用 8000 或 5173 端口的进程
netstat -ano | findstr :8000
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

### 📚 下一步

- 阅读完整文档：[README.md](./README.md)
- Windows 详细安装：[WINDOWS-SETUP.md](./WINDOWS-SETUP.md)
- 开始开发：编辑 `frontend/src/views/HomeView.vue`

### 🛠️ 开发命令速查

**前端**
```bash
cd frontend
npm run dev        # 启动开发服务器
npm run build      # 构建生产版本
npm run preview    # 预览生产版本
npm run lint       # 代码检查
```

**后端**
```bash
cd backend
python manage.py runserver          # 启动服务器
python manage.py makemigrations     # 创建迁移
python manage.py migrate            # 执行迁移
python manage.py createsuperuser    # 创建管理员
python manage.py shell              # 进入 Shell
```

### 🎉 完成！

现在你已经成功启动了 Vue 3 + Django 全栈项目！

需要更多帮助？查看 [README.md](./README.md) 了解详细信息。
