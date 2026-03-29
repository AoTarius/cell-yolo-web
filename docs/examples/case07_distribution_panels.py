import matplotlib.pyplot as plt
import numpy as np

rows = task_data.get('rows', [])
if not rows:
    raise RuntimeError('没有可用数据。')

perimeter = np.array([float(r.get('perimeter', 0.0)) for r in rows], dtype=float)
area = np.array([float(r.get('area', 0.0)) for r in rows], dtype=float)
circularity = np.array([float(r.get('circularity', 0.0)) for r in rows], dtype=float)
aspect_ratio = np.array([float(r.get('aspect_ratio', 0.0)) for r in rows], dtype=float)

# ===== 可调参数区（优先修改下面这些） =====
fig_w, fig_h = 10, 8          # 图尺寸，越大越清晰
bins = 20                     # 直方图分箱数，越大越细
hist_alpha = 0.8              # 柱体透明度（0~1）
grid_alpha = 0.25             # 网格透明度（0~1）
edge_color = 'white'          # 柱体边框颜色
title_text = 'Case 07: Distribution Panels'
color_perimeter = '#9a3412'   # 周长分布颜色
color_area = '#b45309'        # 面积分布颜色
color_circularity = '#0284c7' # 圆度分布颜色
color_aspect = '#6d28d9'      # 长宽比分布颜色
# =====================================

fig, axes = plt.subplots(2, 2, figsize=(fig_w, fig_h))
datasets = [
    ('Perimeter', perimeter, color_perimeter),
    ('Area', area, color_area),
    ('Circularity', circularity, color_circularity),
    ('Aspect Ratio', aspect_ratio, color_aspect),
]

for ax, (name, data, color) in zip(axes.flatten(), datasets):
    if data.size == 0:
        ax.text(0.5, 0.5, 'No Data', ha='center', va='center')
        ax.axis('off')
        continue
    ax.hist(data, bins=bins, alpha=hist_alpha, color=color, edgecolor=edge_color)
    ax.set_title(name)
    ax.set_xlabel(name)
    ax.set_ylabel('Count')
    ax.grid(alpha=grid_alpha)

plt.suptitle(title_text, y=0.98)
plt.tight_layout()