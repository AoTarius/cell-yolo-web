"""
案例1：数据结构展示 + 基础处理示例

说明：
- 自由绘图运行环境会提供 task_data 变量
- task_data 结构：
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
"""

import matplotlib.pyplot as plt
import numpy as np

rows = task_data.get('rows', [])
print(f"task_id={task_data.get('task_id')}")
print(f"row_count={task_data.get('row_count')}, truncated={task_data.get('truncated')}")

if not rows:
    raise RuntimeError('当前任务没有可用数据。')

# 1) 查看单行结构
first = rows[0]
print('single row keys:', sorted(first.keys()))

# 2) 基础统计：area/speed 均值
areas = np.array([r.get('area', 0.0) for r in rows], dtype=float)
speeds = np.array([r.get('speed', 0.0) for r in rows], dtype=float)
print(f"area mean={areas.mean():.3f}, speed mean={speeds.mean():.3f}")

# 3) 按 frame 聚合 area 均值（基础分组思路）
frame_area = {}
for r in rows:
    f = int(r.get('frame', 0))
    frame_area.setdefault(f, []).append(float(r.get('area', 0.0)))

frames = sorted(frame_area.keys())
avg_area = np.array([np.mean(frame_area[f]) for f in frames], dtype=float)

# 4) 最基础绘图：frame -> 平均 area
fig = plt.figure(figsize=(9, 4.5))
plt.plot(frames, avg_area, linewidth=1.5, color='#2563eb', label='Avg Area by Frame')
plt.scatter(frames[:: max(1, len(frames) // 25)], avg_area[:: max(1, len(frames) // 25)], s=14, color='#1d4ed8')
plt.title('Case 1: Data Structure + Basic Aggregation')
plt.xlabel('Frame')
plt.ylabel('Average Area')
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
