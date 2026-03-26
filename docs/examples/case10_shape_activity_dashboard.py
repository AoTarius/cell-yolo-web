import matplotlib.pyplot as plt
import numpy as np

rows = task_data.get('rows', [])
if not rows:
    raise RuntimeError('没有可用数据。')

track_stats = {}
for r in rows:
    tid = int(r.get('track_id', -1))
    track_stats.setdefault(tid, {'distance': 0.0, 'speed': []})
    track_stats[tid]['distance'] += float(r.get('distance', 0.0))
    track_stats[tid]['speed'].append(float(r.get('speed', 0.0)))

scores = []
all_dist = np.array([v['distance'] for v in track_stats.values()], dtype=float)
all_spd = np.array([np.mean(v['speed']) if v['speed'] else 0.0 for v in track_stats.values()], dtype=float)
d_max = float(np.max(all_dist)) if all_dist.size else 1.0
s_max = float(np.max(all_spd)) if all_spd.size else 1.0

for tid, v in track_stats.items():
    d_norm = v['distance'] / (d_max + 1e-9)
    s_norm = (np.mean(v['speed']) if v['speed'] else 0.0) / (s_max + 1e-9)
    scores.append((tid, 0.5 * d_norm + 0.5 * s_norm))

top_ids = [tid for tid, _ in sorted(scores, key=lambda x: x[1], reverse=True)[:10]]

circularity = np.array([float(r.get('circularity', 0.0)) for r in rows], dtype=float)
aspect_ratio = np.array([float(r.get('aspect_ratio', 0.0)) for r in rows], dtype=float)

fig, axes = plt.subplots(2, 2, figsize=(10, 8))

axes[0, 0].hist(circularity, bins=30, alpha=0.75, color='#0ea5e9', edgecolor='white', orientation='horizontal')
axes[0, 0].set_title('Circularity Distribution')
axes[0, 0].set_xlabel('Count')
axes[0, 0].set_ylabel('Circularity')
axes[0, 0].grid(alpha=0.25)

for tid in top_ids:
    pts = sorted([r for r in rows if int(r.get('track_id', -1)) == tid], key=lambda r: int(r.get('frame', 0)))
    fs = [int(p.get('frame', 0)) for p in pts]
    cs = [float(p.get('circularity', 0.0)) for p in pts]
    axes[0, 1].plot(fs, cs, linewidth=1.0, alpha=0.85)
axes[0, 1].set_title('Top Tracks Circularity Over Time')
axes[0, 1].set_xlabel('Frame')
axes[0, 1].set_ylabel('Circularity')
axes[0, 1].grid(alpha=0.25)

axes[1, 0].hist(aspect_ratio, bins=30, alpha=0.75, color='#22c55e', edgecolor='white', orientation='horizontal')
axes[1, 0].set_title('Aspect Ratio Distribution')
axes[1, 0].set_xlabel('Count')
axes[1, 0].set_ylabel('Aspect Ratio')
axes[1, 0].grid(alpha=0.25)

for tid in top_ids:
    pts = sorted([r for r in rows if int(r.get('track_id', -1)) == tid], key=lambda r: int(r.get('frame', 0)))
    fs = [int(p.get('frame', 0)) for p in pts]
    ars = [float(p.get('aspect_ratio', 0.0)) for p in pts]
    axes[1, 1].plot(fs, ars, linewidth=1.0, alpha=0.85)
axes[1, 1].set_title('Top Tracks Aspect Ratio Over Time')
axes[1, 1].set_xlabel('Frame')
axes[1, 1].set_ylabel('Aspect Ratio')
axes[1, 1].grid(alpha=0.25)

plt.suptitle('Case 10: Shape + Activity Dashboard', y=0.98)
plt.tight_layout()