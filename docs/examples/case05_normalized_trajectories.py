import matplotlib.pyplot as plt
import numpy as np

rows = task_data.get('rows', [])
if not rows:
    raise RuntimeError('没有可用数据。')

tracks = {}
for r in rows:
    tid = int(r.get('track_id', -1))
    tracks.setdefault(tid, []).append((
        int(r.get('frame', 0)),
        float(r.get('center_x', 0.0)),
        float(r.get('center_y', 0.0)),
    ))

items = sorted(tracks.items(), key=lambda kv: len(kv[1]), reverse=True)[:35]

fig = plt.figure(figsize=(8, 8))
ax = plt.gca()
ax.axhline(0, color='gray', linewidth=0.7, linestyle='--')
ax.axvline(0, color='gray', linewidth=0.7, linestyle='--')
ax.set_aspect('equal', adjustable='box')

for _tid, pts in items:
    pts_sorted = sorted(pts, key=lambda x: x[0])
    x0, y0 = pts_sorted[0][1], pts_sorted[0][2]
    nx = [p[1] - x0 for p in pts_sorted]
    ny = [p[2] - y0 for p in pts_sorted]
    ax.plot(nx, ny, alpha=0.75, linewidth=1.1)

for radius in [200, 400]:
    circle = plt.Circle((0, 0), radius, fill=False, linestyle='--', color='gray', alpha=0.45)
    ax.add_artist(circle)
    ax.text(radius, 0, f'{radius} μm', fontsize=9)

ax.set_title('Case 05: Normalized Trajectories (Start at Origin)')
ax.set_xlabel('Normalized X (μm)')
ax.set_ylabel('Normalized Y (μm)')
ax.grid(False)
plt.tight_layout()