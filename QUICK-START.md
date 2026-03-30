## 🚀 快速开始

### 第一步：创建并激活 Python 虚拟环境

使用 Conda 创建名为 `cell-yolo` 的虚拟环境：

```bash
# 创建虚拟环境（指定 Python 版本）
conda create -n cell-yolo python=3.8 -y

# 激活虚拟环境
conda activate cell-yolo
```

### 第二步：安装 MySQL 数据库

项目使用 MySQL 作为数据库，需要先安装并配置 MySQL。

#### macOS 用户安装步骤

```bash
# 使用 Homebrew 安装 MySQL
brew install mysql

# 启动 MySQL 服务
brew services start mysql

# 设置 root 密码（按提示操作）
mysql_secure_installation
```

#### Windows 用户安装步骤

1. 下载 MySQL Installer: https://dev.mysql.com/downloads/installer/
2. 运行安装程序，选择 "Developer Default"
3. 按提示完成安装，记住设置的 root 密码
4. 启动 MySQL 服务：
   - 打开"服务"（Win + R，输入 `services.msc`）
   - 找到 "MySQLxx" 服务，右键选择"启动"

#### 创建数据库（可选）

初始化脚本会自动创建数据库，但也可以手动创建：

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE cell_tracking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 退出
EXIT;
```

### 第三步：配置环境变量

在 `backend` 目录下创建 `.env` 文件：

```bash
cd backend

# 复制示例配置
cp .env.example .env
```

编辑 `.env` 文件，将以下内容添加进去（将 `your_password` 替换为你的 MySQL root 密码, 将`DEEPSEEK_API_KEY`替换为你的 Deepseek API 密钥）：

```env
SECRET_KEY=django-insecure-changeme-in-production
DEBUG=True

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=cell_tracking

DEEPSEEK_API_KEY= your_deepseek_api_key  # DeepSeek API密钥（请替换为实际密钥）
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
```

**Windows 用户注意事项**：
- 在记事本中编辑 `.env` 文件时，注意选择"所有文件"类型
- 路径中使用正斜杠 `/` 或双反斜杠 `\\`

### 第四步：安装 Python 依赖

进入 backend 目录并安装所需的 Python 库：

```bash
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

### 第五步：初始化数据库

#### 1. 创建数据库
运行数据库初始化脚本，创建数据库：

```bash
cd scripts
python init_db.py
```

成功后会显示：
```
✓ 成功连接到 MySQL 服务器 (localhost:3306)
✓ 数据库 'cell_tracking' 创建成功或已存在
```

==这一步的报错是正常情况，后续会进行补齐==

#### 2. 执行 Django 迁移

进入 `backend` 目录，执行迁移以创建表结构：

```bash
cd ../backend
python manage.py migrate
```

#### 3. 检查表设置并初始化数据

运行数据初始化脚本，检查表设置并创建初始用户：

```bash
cd ../scripts
python init_data.py
```

成功后会显示：
```
==================================================
检查数据库表结构
==================================================
检查表: users
✓ 字段检查通过: username
✓ 字段检查通过: email
✗ 字段缺失: password_hash (表: users)
✓ 修复字段默认值: dark_mode -> TINYINT(1) DEFAULT 1
...（省略其他表的检查输出）...
==================================================
✓ 表结构检查完成
==================================================

==================================================
初始化 root 用户
==================================================
✓ 密码哈希完成
✓ root 用户创建成功 (ID: 1)
  用户名: root
  密码: password
  邮箱: 未设置
  暗色模式: False
  模型路径: models
  输出路径: output
==================================================
✓ 初始化完成！
==================================================
==================================================
初始化 导入model
==================================================
✓ 导入model 创建成功 (ID: 1)
==================================================
✓ 初始化完成！
==================================================
```

虽然已经使用 `init_db.py` 初始化了数据库表结构，但仍需执行 Django 迁移以确保 Django 管理后台等功能正常工作：
```bash
cd ../backend
python manage.py migrate
```

初始化数据库基本信息
```bash
cd ../scripts
python init_data.py
```

**注意**：如果脚本运行失败，请检查：
1. 数据库是否已正确初始化。
2. `.env` 文件中的配置是否正确。
3. MySQL 服务是否正常运行。

**如果连接失败**，检查：
1. MySQL 服务是否启动
   - macOS: `brew services list`
   - Windows: 查看服务管理器
2. `.env` 文件中的密码是否正确
3. MySQL root 用户权限设置


### 第六步（可选）：验证 ultralytics 本地库

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

### 第七步：安装前端 npm 包

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
- **ECharts 5.x**


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
cd web/libs/tif-mp4
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

详细说明见: [web/libs/tif-mp4/README.md](./libs/tif-mp4/README.md)

### 软删除数据清理命令

项目使用软删除机制（`is_deleted` 字段）删除数据，以支持数据恢复功能。需要定期清理超过保留期的软删除数据，避免数据库无限增长。

**使用方法:**
```bash
cd backend
python manage.py purge_soft_deleted [选项]
```

**选项说明:**
- `--days N`: 保留天数，默认为30天（只删除N天前的软删除数据）
- `--dry-run`: 只显示将要删除的记录，不实际删除
- `--force`: 强制删除所有软删除记录，不考虑时间限制

**使用示例:**
```bash
# 删除30天前的软删除数据（推荐）
python manage.py purge_soft_deleted --days 30

# 测试运行，查看将要删除的记录
python manage.py purge_soft_deleted --days 30 --dry-run

# 查看所有软删除记录（不删除）
python manage.py purge_soft_deleted --force --dry-run

# 强制删除所有软删除记录（谨慎使用）
python manage.py purge_soft_deleted --force
```

**定时任务配置（可选）:**
建议配置定时任务定期清理软删除数据：

```bash
# 使用 crontab 每天凌晨2点执行清理
0 2 * * * cd /path/to/cell-yolo/web/backend && python manage.py purge_soft_deleted --days 30 >> /var/log/cell_yolo_cleanup.log 2>&1
```

**注意事项:**
- 使用 `--dry-run` 参数可以安全地查看将要删除的记录
- `--force` 参数会删除所有软删除记录，开发调试时使用
- 默认保留30天的软删除数据，可根据业务需求调整
- 清理前建议先备份数据库