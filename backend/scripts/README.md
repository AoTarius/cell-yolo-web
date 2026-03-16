# 数据库脚本

本目录包含数据库初始化和维护脚本。

## 初始化脚本

### init_db.py

用于初始化 MySQL 数据库的脚本，会自动创建：
- 数据库（如果不存在）
- 表结构（users, videos, models, tasks, cells, task_status）
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
└── videos/                 # 视频库，统一管理所有原始视频
    └── {video_id}/         # 视频专属文件夹
        └── {video_name}.{ext}

└── tasks/
    └── {task_id}/          # 任务专属文件夹
        ├── output/         # 处理后视频文件夹
        │   ├── {annotated_video_name}.{ext}
        │   ├── frames/     # 处理后视频帧图像（可选）
        │   └── labels/     # 标注信息（txt格式，可选）
        ├── *.txt           # 其他文本信息（如检测结果、统计信息等）
        └── logs/           # 任务日志（可选）
```

### 表结构说明

数据库包含6个核心表：users、videos、models、tasks、cells、task_status

#### users 表
记录用户信息的表
- `id`: 用户 ID（主键，INTEGER, 自增）
- `username`: 用户名（VARCHAR(100), NOT NULL）
- `password_hash`: 密码哈希（VARCHAR(255), NOT NULL）
- `email`: 邮箱（VARCHAR(255)
- `dark_mode`: 色彩模式（BOOLEAN, NOT NULL, 默认True）
- `model_base_path`: 用户模型文件基础路径（VARCHAR(500), NOT NULL）
- `output_base_path`: 用户输出文件基础路径（VARCHAR(500), NOT NULL）
- `created_at`: 创建时间（DATETIME, NOT NULL, 默认当前时间）
- `updated_at`: 更新时间（DATETIME, NOT NULL, 默认当前时间）
- `is_deleted`: 软删除标识（BOOLEAN, NOT NULL, 默认False）
- `deleted_at`: 删除时间（DATETIME, 可为NULL）

#### videos 表
记录原始视频信息的表，支持视频复用
- `id`: 视频ID（主键，INTEGER, 自增）
- `user_id`: 所属用户ID（INTEGER, NOT NULL）
- `video_name`: 原始视频文件名（VARCHAR(255), NOT NULL）
- `video_path`: 原始视频相对路径（VARCHAR(255), NOT NULL）
- `total_frames`: 总帧数（INTEGER）
- `video_duration`: 视频时长（FLOAT, 单位：秒）
- `file_size`: 文件大小（INTEGER, 单位：字节）
- `created_at`: 创建时间（DATETIME, NOT NULL, 默认当前时间）
- `updated_at`: 更新时间（DATETIME, NOT NULL, 默认当前时间）
- `is_deleted`: 软删除标识（BOOLEAN, NOT NULL, 默认False）
- `deleted_at`: 删除时间（DATETIME, 可为NULL）

#### models 表
记录模型信息的表，模型存储在本地文件夹下，路径记录在users表内
- `id`: 模型 ID（主键，INTEGER, 自增）
- `user_id`: 所属用户ID（INTEGER, NOT NULL）
- `model_name`: 模型名称（VARCHAR(100), NOT NULL）
- `model_path`: 模型文件相对路径（VARCHAR(255), NOT NULL, 相对于用户的model_base_path）
- `created_at`: 创建时间（DATETIME, NOT NULL, 默认当前时间）
- `updated_at`: 更新时间（DATETIME, NOT NULL, 默认当前时间）
- `is_deleted`: 软删除标识（BOOLEAN, NOT NULL, 默认False）
- `deleted_at`: 删除时间（DATETIME, 可为NULL）

#### tasks 表
记录所有任务信息的表，存储任务的静态配置和最终结果
- `id`: 任务 ID（主键，INTEGER, 自增）
- `user_id`: 提出任务的用户ID（INTEGER, NOT NULL）
- `video_id`: 使用的原始视频ID（INTEGER, NOT NULL）
- `model_id`: 使用的模型ID（INTEGER, NOT NULL）
- `task_id`: 任务唯一标识（VARCHAR(36), NOT NULL, UNIQUE），是创建tasks内文件夹的标识
- `task_name`: 任务名（VARCHAR(255), NOT NULL）
- `status`: 任务状态（VARCHAR(20), NOT NULL, 枚举值: 'pending', 'processing', 'completed', 'failed'）
- `total_frames`: 总帧数（INTEGER, 默认0）
- `conf`: 置信度阈值（FLOAT, 默认0.3, 范围0-1）
- `imgsz`: 图像尺寸（INTEGER, 默认1024）
- `fps`: 帧率（INTEGER, 默认10）
- `annotated_video_name`: 处理后视频文件名（VARCHAR(255), 存储在任务文件夹内）
- `error_message`: 错误信息（TEXT）
- `created_at`: 创建时间（DATETIME, NOT NULL, 默认当前时间）
- `updated_at`: 更新时间（DATETIME, NOT NULL, 默认当前时间）
- `is_deleted`: 软删除标识（BOOLEAN, NOT NULL, 默认False）
- `deleted_at`: 删除时间（DATETIME, 可为NULL）

#### task_status 表
记录任务实时处理状态的表，存储动态状态和实时进度信息
- `id`: 状态记录 ID（主键，INTEGER, 自增）
- `task_id`: 关联任务ID（VARCHAR(36), NOT NULL, UNIQUE），关联tasks表的task_id字段
- `status`: 任务状态（VARCHAR(20), 默认'pending', 枚举值: 'pending', 'processing', 'completed', 'failed'）
- `progress`: 进度（INTEGER, 默认0, 范围0-100）
- `stage`: 当前处理阶段（VARCHAR(50), 可为NULL）
- `current_frame`: 当前处理帧数（INTEGER, 默认0）
- `total_frames`: 总帧数（INTEGER, 默认0）
- `error_message`: 错误信息（TEXT, 可为NULL）
- `estimated_remaining_time`: 预计剩余时间（INTEGER, 可为NULL, 单位：秒）
- `created_at`: 创建时间（DATETIME, NOT NULL, 默认当前时间）
- `updated_at`: 更新时间（DATETIME, NOT NULL, 默认当前时间）
- `is_deleted`: 软删除标识（BOOLEAN, NOT NULL, 默认False）
- `deleted_at`: 删除时间（DATETIME, 可为NULL）

#### cells 表
记录每个任务的细胞的具体信息
- `id`: 细胞 ID（主键，INTEGER, 自增）
- `task_id`: 关联的任务ID（INTEGER, NOT NULL）
- `frame`: 帧号（INTEGER, NOT NULL），表示该检测记录出现在视频的第几帧
- `track_id`: 轨迹ID（INTEGER, NOT NULL），用于追踪同一个细胞在不同帧中的位置（DeepSORT分配的唯一标识）
- `area`: 面积（FLOAT, NOT NULL），常用筛选字段，保留结构化
- `speed`: 速度（FLOAT, NOT NULL），常用筛选字段，保留结构化
- `tracking_persistence`: 持续追踪度（FLOAT, NOT NULL），常用筛选字段，保留结构化
- `metrics_json`: 聚合后的指标 JSON（JSON, NOT NULL），包含以下字段：
  - `bbox`: 边界框信息，包含 `left`（左上角 x 坐标）、`top`（左上角 y 坐标）、`width`（宽度）、`height`（高度）
  - `center`: 中心点信息，包含 `cx`（中心点 x 坐标）、`cy`（中心点 y 坐标）
  - `shape`: 形状信息，包含 `perimeter`（周长）、`circularity`（圆度）、`circularity_increment`（圆度增量）、`aspect_ratio`（长宽比）、`shape_change_rate`（形态变化速率）、`spreading_index`（铺展指数）、`protrusion_activity_index`（膜突起活动指数）
  - `motion`: 运动信息，包含 `vx`（x 方向速度）、`vy`（y 方向速度）、`distance`（位移距离）、`migration_speed`（迁移速度）、`mean_square_displacement`（平均平方位移）、`turning_angle`（转向角）、`persistence_index`（方向持久性）
  - `visibility`: 可见性（FLOAT）
  - `cell- `: 类别（INTEGER）
  - `confidence`: 置信度（FLOAT）
- `created_at`: 创建时间（DATETIME, NOT NULL, 默认当前时间）
- `is_deleted`: 软删除标识（BOOLEAN, NOT NULL, 默认False）
- `deleted_at`: 删除时间（DATETIME, 可为NULL）

### 索引设计

**注意：本设计不使用数据库外键约束，所有关联关系通过代码层面维护。**

#### users表索引
- PRIMARY KEY: `id`
- UNIQUE INDEX: `idx_username` (username)
- INDEX: `idx_email` (email)
- INDEX: `idx_deleted` (is_deleted)

#### videos表索引
- PRIMARY KEY: `id`
- INDEX: `idx_user_id` (user_id)
- INDEX: `idx_user_deleted` (user_id, is_deleted)
- UNIQUE INDEX: `idx_user_video_name` (user_id, video_name) - 同一用户内视频名称唯一

#### models表索引
- PRIMARY KEY: `id`
- INDEX: `idx_user_id` (user_id)
- INDEX: `idx_user_deleted` (user_id, is_deleted)
- UNIQUE INDEX: `idx_user_model_name` (user_id, model_name) - 同一用户内模型名称唯一

#### tasks表索引
- PRIMARY KEY: `id`
- UNIQUE INDEX: `idx_task_id` (task_id)
- INDEX: `idx_user_id` (user_id)
- INDEX: `idx_user_status` (user_id, status)
- INDEX: `idx_user_deleted` (user_id, is_deleted)
- INDEX: `idx_video_id` (video_id)
- INDEX: `idx_model_id` (model_id)
- INDEX: `idx_created_at` (created_at)
- 复合索引：`idx_user_status_deleted` (user_id, status, is_deleted)

#### task_status表索引
- PRIMARY KEY: `id`
- UNIQUE INDEX: `idx_task_id` (task_id) - 关联tasks表的task_id
- INDEX: `idx_task_status` (task_id, status)
- INDEX: `idx_status` (status)

#### cells表索引
- PRIMARY KEY: `id`
- INDEX: `idx_task_id` (task_id)
- INDEX: `idx_task_frame_track` (task_id, frame, track_id) - 核心查询：按任务、帧、轨迹查询
- INDEX: `idx_task_track` (task_id, track_id) - 查询特定细胞轨迹
- INDEX: `idx_task_frame` (task_id, frame) - 按帧加载数据
- INDEX: `idx_task_area` (task_id, area) - 按任务和面积筛选
- INDEX: `idx_task_speed` (task_id, speed) - 按任务和速度筛选
- INDEX: `idx_task_tracking_persistence` (task_id, tracking_persistence) - 按任务和持续追踪度筛选
- INDEX: `idx_task_deleted` (task_id, is_deleted)

### 软删除策略

所有表统一使用软删除策略：
- `is_deleted`: 软删除标识（BOOLEAN, NOT NULL, 默认False）
- `deleted_at`: 删除时间（DATETIME, 可为NULL）

**支持软删除的表**：users、videos、models、tasks、cells、task_status

**删除操作流程：**
1. 将记录的 `is_deleted` 设为 `true`
2. 将 `deleted_at` 设为当前时间
3. 代码层面处理级联逻辑
4. 代码层面清理文件系统

**查询注意事项：**
- 所有查询默认添加 `WHERE is_deleted = false` 条件
- 支持数据恢复操作（将 `is_deleted` 改回 `false`）
- **唯一性约束**：数据库层面的唯一性约束会检查所有记录（包括已删除的），因此在代码层面需要确保用户名/视频名/模型名的唯一性只在未删除记录间生效

### 文件路径生成规则

所有文件路径均通过用户配置和ID动态生成，避免在数据库中存储重复的完整路径：

#### 模型文件路径
- **存储位置**: `{user.model_base_path}/{model.model_path}`
- **查询时拼接**: `model_base_path` + `model_path`

#### 原始视频文件路径
- **存储位置**: `{user.output_base_path}/videos/{video.video_id}/{video.video_name}`
- **查询时拼接**: `output_base_path` + "videos/" + `video_id` + "/" + `video_name`

#### 任务文件夹路径
- **存储位置**: `{user.output_base_path}/tasks/{task.task_id}/`
- **查询时拼接**: `output_base_path` + "tasks/" + `task_id`

#### 处理后视频文件路径
- **存储位置**: `{user.output_base_path}/tasks/{task.task_id}/output/{task.annotated_video_name}`
- **查询时拼接**: `output_base_path` + "tasks/" + `task_id` + "/output/" + `annotated_video_name`

#### 帧图像路径
- **处理后视频帧**: `{user.output_base_path}/tasks/{task.task_id}/output/frames/frame_{frame_number}.{ext}`
- **查询时拼接**: `output_base_path` + "tasks/" + `task_id` + "/output/frames/" + 文件名

#### 标签文件路径
- **标注信息**: `{user.output_base_path}/tasks/{task.task_id}/output/labels/{label_name}.txt`
- **查询时拼接**: `output_base_path` + "tasks/" + `task_id` + "/output/labels/" + 文件名

#### 结果数据（不存储文件）
- **检测结果**: 不存储result.json，通过查询cells表动态生成
- **统计信息**: 通过聚合查询tasks表和cells表生成
- **导出功能**: 根据需要实时生成CSV、JSON等格式

#### API访问路径
- **原始视频**: `/api/video/{video_id}`
- **处理后视频**: `/api/task-video/{task_id}`
- **检测结果**: `/api/result/{task_id}`（从数据库实时查询生成）
- **细胞数据**: `/api/cells/{task_id}`（从数据库查询）

### 软删除的级联逻辑

由于不使用数据库外键约束，所有级联删除逻辑需要在代码层面实现：

#### 删除用户
1. 将 `users` 表中对应记录的 `is_deleted` 设为 `true`，`deleted_at` 设为当前时间
2. **代码级联**：将该用户的所有 `videos`、`models`、`tasks` 的 `is_deleted` 设为 `true`
3. **代码级联**：将所有关联的 `tasks` 对应的 `cells` 和 `task_status` 的 `is_deleted` 设为 `true`
4. 清理文件系统中的用户文件夹

#### 删除视频
1. 将 `videos` 表中对应记录的 `is_deleted` 设为 `true`，`deleted_at` 设为当前时间
2. **代码级联**：将使用该视频的所有 `tasks` 的 `is_deleted` 设为 `true`
3. **代码级联**：将所有关联的 `cells` 和 `task_status` 的 `is_deleted` 设为 `true`
4. 清理文件系统中的视频文件

#### 删除模型
1. 将 `models` 表中对应记录的 `is_deleted` 设为 `true`，`deleted_at` 设为当前时间
2. **检查**：是否有正在使用该模型的 `tasks`（`status` 为 `processing`），如有则阻止删除
3. 清理文件系统中的模型文件

#### 删除任务
1. 将 `tasks` 表中对应记录的 `is_deleted` 设为 `true`，`deleted_at` 设为当前时间
2. **代码级联**：将所有关联的 `cells` 的 `is_deleted` 设为 `true`
3. **代码级联**：将关联的 `task_status` 的 `is_deleted` 设为 `true`
4. 清理文件系统中的任务文件夹（保留视频文件，因为可能在 `videos` 表中）

## 注意事项

1. 确保 MySQL 服务器已启动并可访问
2. 确保 MySQL 用户有创建数据库和表的权限
3. 生产环境中应该使用 bcrypt 等库处理密码哈希
4. 根据实际需求修改表结构
5. 帧图像存储在文件系统，不存储在数据库BLOB字段中
6. 删除用户/任务/模型时，需要同步清理文件系统
7. **所有查询默认需要过滤 `is_deleted = true` 的记录**
8. **task_status表设计说明**：
   - task_status表的task_id字段直接关联tasks表的task_id（VARCHAR UUID）
   - 创建任务时需要同时创建tasks和task_status记录
   - 任务处理过程中只更新task_status表，不更新tasks表
   - 任务完成/失败时同时更新tasks和task_status表
   - 查询任务状态时JOIN task_status表获取实时进度信息
9. **代码层面需要实现以下约束**：
   - 唯一性检查：创建 `users` 时检查 `username` 的唯一性（排除已删除记录）
   - 唯一性检查：创建 `videos` 时检查 `user_id + video_name` 的唯一性（排除已删除记录）
   - 唯一性检查：创建 `models` 时检查 `user_id + model_name` 的唯一性（排除已删除记录）
   - 引用完整性：创建记录时验证关联的 `id` 存在且 `is_deleted = false`
   - 级联删除：实现上述软删除的级联逻辑（包括task_status表）
   - 数据恢复：支持将 `is_deleted` 改回 `false` 进行数据恢复