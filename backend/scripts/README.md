# 数据库脚本

本目录包含数据库初始化和维护脚本。

## 初始化脚本

### init_db.py

用于初始化 MySQL 数据库的脚本，会自动创建：
- 数据库（如果不存在）
- 表结构（users, models, tasks, cells）
- 初始数据（可选）

### 使用方法

1. **配置环境变量**

在 `web/backend/.env` 文件中配置数据库连接信息：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=cell_tracking
```

2. **安装依赖**

```bash
cd web/backend
pip install pymysql python-dotenv
```

3. **运行脚本**

```bash
cd scripts
python init_db.py
```

或者从 backend 根目录运行：

```bash
python scripts/init_db.py
```

## 数据库设计

### 文件夹结构设计

系统采用用户隔离的文件夹结构，每个用户拥有独立的数据目录：

```
{user.model_base_path}/
└── {model_name}.pt         # 用户模型文件

{user.output_base_path}/
└── tasks/
    └── {task_id}/          # 任务专属文件夹
        ├── original/       # 原始视频文件夹
        │   ├── {original_video_name}.{ext}
        │   └── frames/     # 原始视频帧图像（可选）
        ├── output/         # 处理后视频文件夹
        │   ├── {annotated_video_name}.{ext}
        │   ├── frames/     # 处理后视频帧图像（可选）
        │   └── labels/     # 标注信息（txt格式，可选）
        ├── *.txt           # 其他文本信息（如检测结果、统计信息等）
        └── logs/           # 任务日志（可选）
```

### 表结构说明

#### users 表
记录用户信息的表
- `id`: 用户 ID（主键，INTEGER, 自增）
- `username`: 用户名（VARCHAR(100), NOT NULL, UNIQUE）
- `password_hash`: 密码哈希（VARCHAR(255), NOT NULL）
- `created_at`: 创建时间（DATETIME, NOT NULL, 默认当前时间）
- `updated_at`: 更新时间（DATETIME, NOT NULL, 默认当前时间）
- `dark_mode`: 使用的色彩模式（BOOLEAN, NOT NULL, 默认True）
- `email`: 邮箱（VARCHAR(255), UNIQUE）
- `model_base_path`: 用户模型文件基础路径（VARCHAR(500), NOT NULL）
- `output_base_path`: 用户输出文件基础路径（VARCHAR(500), NOT NULL）

#### models 表
记录模型信息的表，模型存储在本地文件夹下，路径记录在users表内
- `id`: 模型 ID（主键，INTEGER, 自增）
- `user_id`: 所属用户ID（INTEGER, NOT NULL, 外键到users表的id）
- `model_name`: 模型名称（VARCHAR(100), NOT NULL, 同一用户内唯一）
- `model_path`: 模型文件相对路径（VARCHAR(255), NOT NULL, 相对于用户的model_base_path）

#### tasks 表
记录所有任务信息的表，视频存储在本地文件夹下，路径记录在users表内
- `id`: 任务 ID（主键，INTEGER, 自增）
- `user_id`: 提出任务的用户ID（INTEGER, NOT NULL, 外键到users表的id）
- `task_id`: 任务唯一标识（VARCHAR(36), NOT NULL, UNIQUE），是创建tasks内文件夹的标识
- `video_name`: 视频名（VARCHAR(255), NOT NULL）
- `task_name`: 任务名（VARCHAR(255), NOT NULL, 默认等于视频名）
- `status`: 任务状态（VARCHAR(20), NOT NULL, 枚举值: 'pending', 'processing', 'completed', 'failed'）
- `progress`: 进度（INTEGER, NOT NULL, 默认0, 范围0-100）
- `total_frames`: 总帧数（INTEGER）
- `video_duration`: 视频时长（FLOAT, 单位：秒）
- `model_id`: 使用的模型id（INTEGER, 外键到models表的id）
- `conf`: 置信度阈值（FLOAT, 默认0.3, 范围0-1）
- `imgsz`: 图像尺寸（INTEGER, 默认1024）
- `fps`: 帧率（INTEGER, 默认10）
- `annotated_video_name`: 处理后视频文件名（VARCHAR(255), 存储在任务文件夹内）
- `original_video_name`: 原始视频文件名（VARCHAR(255), 上传时直接存储在任务文件夹内）
- `error_message`: 错误信息（TEXT）
- `created_at`: 创建时间（DATETIME, NOT NULL, 默认当前时间）
- `updated_at`: 更新时间（DATETIME, NOT NULL, 默认当前时间）

#### cells 表
记录每个任务的细胞的具体信息
- `id`: 细胞 ID（主键，INTEGER, 自增）
- `task_id`: 关联的任务ID（INTEGER, NOT NULL, 外键到tasks表的id）
- `frame`: 帧号（INTEGER, NOT NULL），表示该检测记录出现在视频的第几帧
- `track_id`: 轨迹ID（INTEGER, NOT NULL），用于追踪同一个细胞在不同帧中的位置（DeepSORT分配的唯一标识）
- `bb_left`: 边界框左上角X坐标（FLOAT, NOT NULL）
- `bb_top`: 边界框左上角Y坐标（FLOAT, NOT NULL）
- `bb_width`: 边界框宽度（FLOAT, NOT NULL）
- `bb_height`: 边界框高度（FLOAT, NOT NULL）
- `conf`: 置信度（FLOAT, NOT NULL, 范围0-1），模型检测该细胞的置信度分数
- `class`: 类别（INTEGER, NOT NULL, 默认0），检测到的细胞类别（0表示细胞）
- `visibility`: 可见性（FLOAT, 范围0-1），细胞的可见程度
- `created_at`: 创建时间（DATETIME, NOT NULL, 默认当前时间）

### 索引设计

#### users表索引
- PRIMARY KEY: `id`

#### models表索引
- PRIMARY KEY: `id`
- UNIQUE INDEX: `user_model_name` (user_id, model_name) - 同一用户内模型名称唯一
- INDEX: `idx_user_id` (user_id) - 外键索引

#### tasks表索引
- PRIMARY KEY: `id`
- UNIQUE INDEX: `task_id` (业务唯一标识)
- INDEX: `idx_user_status` (user_id, status) - 用于查询用户的任务列表
- INDEX: `idx_created_at` (created_at) - 用于按时间排序
- INDEX: `idx_user_id` (user_id) - 外键索引
- INDEX: `idx_model_id` (model_id) - 外键索引

#### cells表索引
- PRIMARY KEY: `id`
- INDEX: `idx_task_frame_track` (task_id, frame, track_id) - 核心查询：按任务、帧、轨迹查询
- INDEX: `idx_task_track` (task_id, track_id) - 查询特定细胞轨迹
- INDEX: `idx_task_frame` (task_id, frame) - 按帧加载数据
- INDEX: `idx_task_id` (task_id) - 外键索引

### 外键约束

#### models表
- FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
  - 当用户被删除时，如果用户拥有模型，则阻止删除，防止误删

#### tasks表
- FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
  - 当用户被删除时，其所有任务也会被删除
- FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE RESTRICT
  - 当模型被删除时，使用该模型的任务将保留，防止误删

#### cells表
- FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
  - 当任务被删除时，其所有细胞数据也会被删除

### 文件路径生成规则

所有文件路径均通过用户配置和任务ID动态生成，避免在数据库中存储重复的完整路径：

#### 模型文件路径
- **存储位置**: `{user.model_base_path}/{model.model_path}`
- **查询时拼接**: `model_base_path` + `model_path`

#### 任务文件夹路径
- **存储位置**: `{user.output_base_path}/tasks/{task.task_id}/`
- **查询时拼接**: `output_base_path` + "tasks/" + `task_id`

#### 视频文件路径
- **原始视频**: `{user.output_base_path}/tasks/{task.task_id}/original/{task.original_video_name}`
- **处理后视频**: `{user.output_base_path}/tasks/{task.task_id}/output/{task.annotated_video_name}`
- **查询时拼接**: `output_base_path` + "tasks/" + `task_id` + "/" + 子文件夹 + 文件名

#### 帧图像路径
- **原始视频帧**: `{user.output_base_path}/tasks/{task.task_id}/original/frames/frame_{frame_number}.{ext}`
- **处理后视频帧**: `{user.output_base_path}/tasks/{task.task_id}/output/frames/frame_{frame_number}.{ext}`
- **查询时拼接**: `output_base_path` + "tasks/" + `task_id` + "/" + 子文件夹 + "frames/" + 文件名

#### 标签文件路径
- **标注信息**: `{user.output_base_path}/tasks/{task.task_id}/output/labels/{label_name}.txt`
- **查询时拼接**: `output_base_path` + "tasks/" + `task_id` + "/output/labels/" + 文件名

#### 结果数据（不存储文件）
- **检测结果**: 不存储result.json，通过查询cells表动态生成
- **统计信息**: 通过聚合查询tasks表和cells表生成
- **导出功能**: 根据需要实时生成CSV、JSON等格式

#### API访问路径
- **原始视频**: `/api/original-video/{task_id}`
- **处理后视频**: `/api/video/{task_id}`
- **检测结果**: `/api/result/{task_id}`（从数据库实时查询生成）
- **细胞数据**: `/api/cells/{task_id}`（从数据库查询）

## 注意事项

1. 确保 MySQL 服务器已启动并可访问
2. 确保 MySQL 用户有创建数据库和表的权限
3. 生产环境中应该使用 bcrypt 等库处理密码哈希
4. 根据实际需求修改表结构
5. 帧图像存储在文件系统，不存储在数据库BLOB字段中
6. 删除用户/任务/模型时，需要同步清理文件系统