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

# ===== 可调参数区（优先修改下面这些） =====
fig_w, fig_h = 10, 7          # 图尺寸，越大细节越清楚
max_tracks = 30               # 最多显示多少条轨迹，避免过密
line_width = 1.0              # 轨迹线宽
line_alpha = 0.85             # 轨迹透明度（0~1）
elev = 24                     # 俯仰角，改变视角高度
azim = 120                    # 方位角，改变旋转方向
title_text = 'Case 08: 3D Trajectories'
# =====================================

items = sorted(tracks.items(), key=lambda kv: len(kv[1]), reverse=True)[:max_tracks]

fig = plt.figure(figsize=(fig_w, fig_h))
ax = fig.add_subplot(111, projection='3d')

for _tid, pts in items:
    pts_sorted = sorted(pts, key=lambda x: x[2])
    xs = [p[0] for p in pts_sorted]
    ys = [p[1] for p in pts_sorted]
    zs = [p[2] for p in pts_sorted]
    ax.plot(xs, ys, zs, linewidth=line_width, alpha=line_alpha)

ax.set_xlabel('X Position (μm)')
ax.set_ylabel('Y Position (μm)')
ax.set_zlabel('Frame')
ax.set_title(title_text)
ax.view_init(elev=elev, azim=azim)
plt.tight_layout()