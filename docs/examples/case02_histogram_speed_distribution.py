import matplotlib.pyplot as plt
import numpy as np

rows = task_data.get('rows', [])
if not rows:
    raise RuntimeError('没有可用数据。')

# 每个细胞(track_id)平均速度分布
grouped = {}
for r in rows:
    tid = int(r.get('track_id', -1))
    grouped.setdefault(tid, []).append(float(r.get('speed', 0.0)))

avg_speed = np.array([np.mean(v) for v in grouped.values() if len(v) > 0], dtype=float)

fig = plt.figure(figsize=(9, 4.8))
plt.hist(avg_speed, bins=20, density=True, alpha=0.78, color='#3b82f6', edgecolor='white')
plt.xlabel('Average Speed')
plt.ylabel('Probability Density')
plt.title('Case 02: Distribution of Mean Speed by Track')
plt.grid(alpha=0.25)
plt.tight_layout()