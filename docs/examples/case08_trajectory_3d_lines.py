import matplotlib.pyplot as plt

rows = task_data.get('rows', [])
if not rows:
    raise RuntimeError('没有可用数据。')

tracks = {}
for r in rows:
    tid = int(r.get('track_id', -1))
    tracks.setdefault(tid, []).append((
        float(r.get('center_x', 0.0)),
        float(r.get('center_y', 0.0)),
        float(r.get('frame', 0.0)),
    ))

items = sorted(tracks.items(), key=lambda kv: len(kv[1]), reverse=True)[:30]

fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')

for _tid, pts in items:
    pts_sorted = sorted(pts, key=lambda x: x[2])
    xs = [p[0] for p in pts_sorted]
    ys = [p[1] for p in pts_sorted]
    zs = [p[2] for p in pts_sorted]
    ax.plot(xs, ys, zs, linewidth=1.0, alpha=0.85)

ax.set_xlabel('X Position (μm)')
ax.set_ylabel('Y Position (μm)')
ax.set_zlabel('Frame')
ax.set_title('Case 08: 3D Trajectories')
ax.view_init(elev=24, azim=120)
plt.tight_layout()