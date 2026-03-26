import matplotlib.pyplot as plt
import numpy as np

rows = task_data.get('rows', [])
if not rows:
    raise RuntimeError('没有可用数据。')

metrics = {
    'circularity': {},
    'aspect_ratio': {},
    'speed': {},
    'migration_speed': {},
}

for r in rows:
    f = int(r.get('frame', 0))
    for k in metrics.keys():
        metrics[k].setdefault(f, []).append(float(r.get(k, 0.0)))

frames = sorted({int(r.get('frame', 0)) for r in rows})
series = {
    k: np.array([np.mean(metrics[k].get(f, [0.0])) for f in frames], dtype=float)
    for k in metrics.keys()
}

fig, axes = plt.subplots(4, 1, figsize=(10, 10), sharex=True)
axes[0].plot(frames, series['circularity'], color='#2563eb')
axes[0].set_ylabel('Circularity')
axes[0].grid(alpha=0.3)

axes[1].plot(frames, series['aspect_ratio'], color='#7c3aed')
axes[1].set_ylabel('Aspect Ratio')
axes[1].grid(alpha=0.3)

axes[2].plot(frames, series['speed'], color='#16a34a')
axes[2].set_ylabel('Speed')
axes[2].grid(alpha=0.3)

axes[3].plot(frames, series['migration_speed'], color='#dc2626')
axes[3].set_ylabel('Migration Speed')
axes[3].set_xlabel('Frame')
axes[3].grid(alpha=0.3)

fig.suptitle('Case 06: Multi-metric Mean Time Series', y=0.995)
plt.tight_layout()