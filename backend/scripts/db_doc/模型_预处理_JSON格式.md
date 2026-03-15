# 预处理 JSON 格式

## 顶层字段

| 字段名                   | 数据类型  | 描述                                                                 |
|--------------------------|-----------|----------------------------------------------------------------------|
| `task_id`               | STRING    | 任务的唯一标识符，例如 `3be8daa4-6e63-47b5-bd07-6b74292de4c5`。       |
| `status`                | STRING    | 任务状态，当前为 `completed`。                                       |
| `progress`              | FLOAT     | 任务进度百分比，当前为 `100`。                                       |
| `total_frames`          | INT       | 视频的总帧数，当前为 `50`。                                          |
| `cell_count`            | INT       | 检测到的细胞总数，当前为 `558`。                                     |
| `video_duration`        | FLOAT     | 视频时长（秒），当前为 `5.0`。                                       |
| `model_name`            | STRING    | 使用的模型名称，例如 `best_origin.pt`。                              |
| `annotated_video_path`  | STRING    | 标注视频的本地路径。                                                 |
| `annotated_video_url`   | STRING    | 标注视频的 API 访问 URL。                                            |
| `original_video_path`   | STRING    | 原始视频的本地路径。                                                 |
| `created_at`            | DATETIME  | 任务创建时间，例如 `2026-03-08T21:33:47.550677`。                    |

---

## 嵌套字段

### `summary` (统计摘要)

| 字段名                   | 数据类型  | 描述                                                                 |
|--------------------------|-----------|----------------------------------------------------------------------|
| `总帧数`                | INT       | 视频的总帧数。                                                      |
| `总检测记录数`          | INT       | 所有检测记录的数量。                                                |
| `唯一轨迹数`            | INT       | 唯一目标的数量。                                                    |
| `Track ID 范围`         | STRING    | 轨迹 ID 的范围。                                                    |
| `原始 DeepSORT 最大 ID` | INT       | 原始 DeepSORT 的最大轨迹 ID。                                       |

---

### `tracking_data` (追踪数据)

| 字段名                   | 数据类型  | 描述                                                                 |
|--------------------------|-----------|----------------------------------------------------------------------|
| `frame`                 | INT       | 帧号。                                                              |
| `track_id`              | INT       | 目标的轨迹 ID。                                                     |
| `bb_left`               | FLOAT     | 边界框左上角的 x 坐标。                                             |
| `bb_top`                | FLOAT     | 边界框左上角的 y 坐标。                                             |
| `bb_width`              | FLOAT     | 边界框的宽度。                                                      |
| `bb_height`             | FLOAT     | 边界框的高度。                                                      |
| `conf`                  | FLOAT     | 置信度分数。                                                        |
| `class`                 | INT       | 目标的类别。                                                        |
| `visibility`            | FLOAT     | 目标的可见性。                                                      |