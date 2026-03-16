# 预处理 JSON 格式

## 顶层字段

| 字段名                   | 数据类型  | 描述                                                                 |
|--------------------------|-----------|----------------------------------------------------------------------|
| `task_id`               | STRING    | 任务的唯一标识符，例如 `3be8daa4-6e63-47b5-bd07-6b74292de4c5`。       |
| `status`                | STRING    | 任务状态，当前为 `completed`。                                       |
| `progress`              | FLOAT     | 任务进度百分比，当前为 `100`。                                       |
| `model_name`            | STRING    | 使用的模型名称，例如 `best_origin.pt`。                              |
| `annotated_video_path`  | STRING    | 标注视频的本地路径。                                                 |
| `created_at`            | DATETIME  | 任务创建时间，例如 `2026-03-08T21:33:47.550677`。                    |

## 嵌套字段

### `summary` (统计摘要)

| 字段名                   | 数据类型  | 描述                                                                 |
|--------------------------|-----------|----------------------------------------------------------------------|
| `总检测记录数`          | INT       | 所有检测记录的数量。                                                |
| `唯一轨迹数`            | INT       | 唯一目标的数量。                                                    |

---

### `tracking_data` (追踪数据)

| 字段名                   | 数据类型  | 描述                                                                 |
|--------------------------|-----------|----------------------------------------------------------------------|
| `frame`                 | INT       | 帧号。                                                              |
| `track_id`              | INT       | 目标的轨迹 ID。                                                     |
| `area`                  | FLOAT     | 面积（常用筛选字段，保留结构化）。                                  |
| `speed`                 | FLOAT     | 速度（常用筛选字段，保留结构化）。                                  |
| `tracking_persistence`  | FLOAT     | 持续追踪度（常用筛选字段，保留结构化）。                            |
| `metrics_json`          | JSON      | 聚合后的指标 JSON，包含以下字段：                                   |

#### `metrics_json` 字段结构

| 字段名                   | 数据类型  | 描述                                                                 |
|--------------------------|-----------|----------------------------------------------------------------------|
| `bbox`                  | OBJECT    | 边界框信息，包含 `left`（左上角 x 坐标）、`top`（左上角 y 坐标）、`width`（宽度）、`height`（高度）。 |
| `center`                | OBJECT    | 中心点信息，包含 `cx`（中心点 x 坐标）、`cy`（中心点 y 坐标）。     |
| `shape`                 | OBJECT    | 形状信息，包含 `perimeter`（周长）、`circularity`（圆度）、`circularity_increment`（圆度增量）、`aspect_ratio`（长宽比）、`shape_change_rate`（形态变化速率）、`spreading_index`（铺展指数）、`protrusion_activity_index`（膜突起活动指数）。 |
| `motion`                | OBJECT    | 运动信息，包含 `vx`（x 方向速度）、`vy`（y 方向速度）、`distance`（位移距离）、`migration_speed`（迁移速度）、`mean_square_displacement`（平均平方位移）、`turning_angle`（转向角）、`persistence_index`（方向持久性）。 |
| `visibility`            | FLOAT     | 可见性。                                                            |
| `class`                 | INT       | 类别。                                                              |
| `confidence`            | FLOAT     | 置信度。                                                            |

## 缺失字段

### 顶层字段

| 字段名       | 数据类型  | 描述                                   |
|--------------|-----------|----------------------------------------|
| `video_id`   | STRING    | 关联的视频 ID。                        |
| `user_id`    | STRING    | 任务所属用户 ID。                      |
| `fps`        | INT       | 帧率。                                 |
| `task_name`  | STRING    | 任务名称。                             |
| `error_message` | STRING | 任务错误信息。                         |
| `imgsz`      | INT       | 图像尺寸。                             |
| `conf`       | FLOAT     | 任务置信度                             |