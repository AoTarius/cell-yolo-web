import matplotlib.pyplot as plt
import numpy as np

rows = task_data.get('rows', [])
if not rows:
    raise RuntimeError('没有可用数据。')

frames_all = sorted({int(r.get('frame', 0)) for r in rows})
if not frames_all:
    raise RuntimeError('没有帧数据。')

pick_idx = np.linspace(0, len(frames_all) - 1, min(4, len(frames_all)), dtype=int)
frames = [frames_all[i] for i in pick_idx]

fig, axes = plt.subplots(2, 2, figsize=(10, 8))
axes = axes.flatten()

for i, f in enumerate(frames):
    pts = [r for r in rows if int(r.get('frame', 0)) == f]
    xs = np.array([float(r.get('center_x', 0.0)) for r in pts], dtype=float)
    ys = np.array([float(r.get('center_y', 0.0)) for r in pts], dtype=float)
    axes[i].scatter(xs, ys, s=10, alpha=0.7, color='#0ea5e9')
    axes[i].set_title(f'Frame {f}')
    axes[i].set_xlabel('X')
    axes[i].set_ylabel('Y')
    axes[i].grid(alpha=0.25)

for j in range(len(frames), 4):
    axes[j].axis('off')

plt.suptitle('Case 03: Multi-frame Position Scatter', y=0.98)
plt.tight_layout()