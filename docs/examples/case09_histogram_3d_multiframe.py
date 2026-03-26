import matplotlib.pyplot as plt
import numpy as np

rows = task_data.get('rows', [])
if not rows:
    raise RuntimeError('没有可用数据。')

feature = 'area'
frames_all = sorted({int(r.get('frame', 0)) for r in rows})
pick_idx = np.linspace(0, len(frames_all) - 1, min(5, len(frames_all)), dtype=int)
frames = [frames_all[i] for i in pick_idx]

all_values = np.array([float(r.get(feature, 0.0)) for r in rows], dtype=float)
bins = np.linspace(float(np.min(all_values)), float(np.max(all_values) + 1e-9), 12)
bar_w = (bins[1] - bins[0]) * 0.9

fig = plt.figure(figsize=(11, 7))
ax = fig.add_subplot(111, projection='3d')

for f in frames:
    vals = np.array([float(r.get(feature, 0.0)) for r in rows if int(r.get('frame', 0)) == f], dtype=float)
    hist, edges = np.histogram(vals, bins=bins, density=True)
    xpos = edges[:-1]
    ypos = np.full_like(xpos, float(f))
    zpos = np.zeros_like(xpos)
    dx = np.full_like(xpos, bar_w)
    dy = np.full_like(xpos, max(1.0, float(np.median(np.diff(frames))) if len(frames) > 1 else 1.0) * 0.7)
    dz = hist
    ax.bar3d(xpos, ypos, zpos, dx, dy, dz, alpha=0.72)

ax.set_xlabel('Area')
ax.set_ylabel('Frame')
ax.set_zlabel('Density')
ax.set_title('Case 09: 3D Histogram Across Frames')
ax.view_init(elev=28, azim=120)
plt.tight_layout()