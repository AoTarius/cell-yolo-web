import matplotlib.pyplot as plt
import numpy as np

rows = task_data.get('rows', [])
if not rows:
    raise RuntimeError('没有可用数据。')

perimeter = np.array([float(r.get('perimeter', 0.0)) for r in rows], dtype=float)
area = np.array([float(r.get('area', 0.0)) for r in rows], dtype=float)
circularity = np.array([float(r.get('circularity', 0.0)) for r in rows], dtype=float)
aspect_ratio = np.array([float(r.get('aspect_ratio', 0.0)) for r in rows], dtype=float)

fig, axes = plt.subplots(2, 2, figsize=(10, 8))
datasets = [
    ('Perimeter', perimeter, '#9a3412'),
    ('Area', area, '#b45309'),
    ('Circularity', circularity, '#0284c7'),
    ('Aspect Ratio', aspect_ratio, '#6d28d9'),
]

for ax, (name, data, color) in zip(axes.flatten(), datasets):
    if data.size == 0:
        ax.text(0.5, 0.5, 'No Data', ha='center', va='center')
        ax.axis('off')
        continue
    ax.hist(data, bins=20, alpha=0.8, color=color, edgecolor='white')
    ax.set_title(name)
    ax.set_xlabel(name)
    ax.set_ylabel('Count')
    ax.grid(alpha=0.25)

plt.suptitle('Case 07: Distribution Panels', y=0.98)
plt.tight_layout()