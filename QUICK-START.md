## 🚀 快速开始

### 🤖 自动化安装（推荐）

我们提供了自动化安装脚本，可以一键完成所有配置：

**macOS/Linux 用户**:
```bash
chmod +x setup.sh
./setup.sh
```

**Windows 用户**:
```powershell
.\setup.ps1
```

自动化脚本会自动执行以下步骤：
- ✓ 检查系统环境（conda、MySQL、Node.js）
- ✓ 创建/激活 Python 虚拟环境
- ✓ 配置环境变量（.env 文件）
- ✓ 安装 Python 和 npm 依赖
- ✓ 初始化数据库
- ✓ 安装前端依赖

在需要手动配置的地方，脚本会提示你输入：
- MySQL root 密码
- DeepSeek API 密钥（可选）

如果自动化脚本遇到问题，请参考下面的手动安装步骤。

---

### 📝 手动安装步骤

如果自动化脚本无法满足你的需求，可以按照以下步骤手动安装：

### 第一步：创建并激活 Python 虚拟环境

使用 Conda 创建名为 `cell-yolo` 的虚拟环境：

```bash
# 创建虚拟环境（指定 Python 版本，建议 3.10-3.12）
conda create -n cell-yolo python=3.11 -y

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
- Django == 4.2.28
- djangorestframework == 3.15.2
- django-cors-headers == 4.4.0
- python-dotenv == 1.0.1
- **channels == 4.2.2** (WebSocket 支持)
- **opencv-python == 4.13.0.92** (视频处理)
- **numpy == 1.24.4** (数值计算)
- **torch == 2.4.1** (PyTorch)
- **torchvision == 0.19.1** (PyTorch 视觉库)
- **ultralytics == 8.4.21** (YOLO 模型)
- **deep-sort-realtime == 1.3.2** (目标追踪)
- **psutil == 7.2.2** (系统工具)
- **tqdm == 4.67.3** (进度条)
- **scipy == 1.10.1** (科学计算)
- **pandas == 2.0.3** (数据分析)
- **polars == 1.8.2** (高性能数据处理)
- **PyYAML == 6.0.3** (配置解析)
- **requests == 2.32.4** (HTTP 请求)
- **Pillow == 10.4.0** (图像处理)
- **matplotlib == 3.7.5** (绘图)
- **seaborn == 0.13.2** (统计可视化)

**注意**: ultralytics 和 deep_sort_pytorch 已作为本地库包含在 `web/libs/ultralytics` 目录中，无需额外安装。项目会自动通过以下方式配置 Python 路径：
1. `backend/settings.py` 中的 sys.path 配置
2. VSCode 的 `.vscode/settings.json` 配置

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
python -c "from deep_sort_realtime.deepsort_tracker import DeepSort; print('✓ DeepSORT 导入成功')"
```

如果遇到导入错误，请检查：
1. 确认已激活 conda 环境：`conda activate cell-yolo`
2. 如果使用 VSCode，重新加载窗口：`Cmd + Shift + P` → "Reload Window"

### 第七步：安装前端 npm 包

**Node.js 版本要求**: ^20.19.0 || >=22.12.0

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
- **ECharts 5.6.0** (数据可视化)
- **ECharts GL 2.0.9** (3D 可视化)
- **@codemirror/lang-python** (Python 代码编辑器)
- **highlight.js** (代码高亮)
- **marked** (Markdown 渲染)
- **jszip** (ZIP 文件处理)
- **@vueuse/core** (Vue 工具集)
- **lucide-vue-next** (图标库)


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

### 自由绘图功能

系统提供自由绘图功能，允许用户使用 Python 代码自定义分析细胞追踪数据。

**功能特性**：
- 在线 Python 代码编辑器（基于 CodeMirror）
- 内置 10+ 数据分析示例模板
- 支持多种可视化类型（折线图、散点图、热力图、3D 图等）
- 实时代码预览和执行

**可用的数据变量**：
- `task_data`: 包含完整的任务追踪数据，结构如下：
  ```python
  {
    'task_id': str,
    'task_name': str,
    'video_name': str,
    'row_count': int,
    'truncated': bool,
    'rows': [
      {
        'frame': int,
        'track_id': int,
        'area': float,
        'speed': float,
        'bb_left': float,
        'bb_top': float,
        'bb_width': float,
        'bb_height': float,
        'center_x': float,
        'center_y': float,
        'perimeter': float,
        'circularity': float,
        'aspect_ratio': float,
        'distance': float,
        'migration_speed': float,
        'mean_square_displacement': float,
      },
      ...
    ]
  }
  ```

**示例模板位置**: `web/docs/examples/`
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

## 📚 更多文档

- [自由绘图 MVP 设计说明](./docs/自由绘图MVP设计说明.md) - 自由绘图功能的详细设计说明
- [API 集成指南](./frontend/docs/API-INTEGRATION.md) - 前端 API 集成文档
- [前端开发文档](./frontend/docs/DEVELOPMENT.md) - 前端开发指南
- [软件需求分析文档](./docs/软件需求分析文档_v1.md) - 完整需求文档
- [项目日志](./docs/项目日志.md) - 项目开发日志
- [原型设计文档](./docs/原型设计文档.md) - UI/UX 原型设计