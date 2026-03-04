# 前端颜色分析文档

## 概述
本文档记录了前端所有Vue文件中使用的颜色定义，包括深色模式和浅色模式的颜色值。

---

## 1. CellTrackingView.vue

| 元素/组件 | 属性 | 深色模式 | 浅色模式 | 用途描述 |
|-----------|------|----------|----------|----------|
| `.cell-tracking-view` | background | #0d1117 | - | 主视图背景色 |
| `.cell-tracking-view` | color | #c9d1d9 | - | 主文字颜色 |
| `.welcome-icon` | color | #30363d | - | 欢迎图标颜色 |
| `.welcome-content h1` | color | #fff | - | 欢迎标题颜色 |
| `.welcome-content p` | color | #8b949e | - | 欢迎描述文字颜色 |

---

## 2. Sidebar.vue

| 元素/组件 | 属性 | 深色模式 | 浅色模式 | 用途描述 |
|-----------|------|----------|----------|----------|
| `.sidebar` | background | #1e1e1e | - | 侧边栏背景色 |
| `.sidebar` | color | #e0e0e0 | - | 侧边栏文字颜色 |
| `.sidebar` | border-right | #333 | - | 侧边栏右边框 |
| `.sidebar-header` | border-bottom | #333 | - | 侧边栏头部边框 |
| `.sidebar-header h1` | color | #fff | - | 侧边栏标题颜色 |
| `.btn-new-analysis` | background | #007acc | - | 新建分析按钮背景 |
| `.btn-new-analysis` | color | white | - | 新建分析按钮文字 |
| `.btn-new-analysis:hover` | background | #005a9e | - | 新建分析按钮hover背景 |
| `.btn-upload-model` | background | #fb923c | - | 上传模型按钮背景 |
| `.btn-upload-model:hover` | background | #f97316 | - | 上传模型按钮hover背景 |
| `.btn-upload-model .icon` | color | white | - | 上传模型按钮图标文字 |
| `.btn-new-analysis .icon` | color | white | - | 新建分析按钮图标文字 |
| `.section-title` | color | #888 | - | 章节标题颜色 |
| `.dot-completed` | box-shadow | 0 0 6px rgba(74, 222, 128, 0.5) | - | 完成状态点阴影 |
| `.dot-processing` | box-shadow | 0 0 6px rgba(251, 146, 60, 0.5) | - | 处理状态点阴影 |
| `@keyframes pulse-orange` (0%, 100%) | opacity | 1 | - | 处理状态点脉冲动画不透明度 |
| `@keyframes pulse-orange` (50%) | opacity | 0.5 | - | 处理状态点脉冲动画不透明度 |
| `.record-item` | background | #252525 | - | 记录项背景 |
| `.record-item:hover` | background | #2d2d2d | - | 记录项hover背景 |
| `.record-item:hover` | border-color | #444 | - | 记录项hover边框 |
| `.record-item.active` | background | #264f78 | - | 激活记录项背景 |
| `.record-item.active` | border-color | #007acc | - | 激活记录项边框 |
| `.record-name` | color | #fff | - | 记录名称颜色 |
| `.dot-completed` | background | #4ade80 | - | 完成状态点背景 |
| `.dot-processing` | background | #fb923c | - | 处理状态点背景 |
| `.status-completed` | background | #0e5a2b | - | 完成状态背景 |
| `.status-completed` | color | #4ade80 | - | 完成状态文字 |
| `.status-processing` | background | #5a4a0e | - | 处理状态背景 |
| `.status-processing` | color | #fb923c | - | 处理状态文字 |
| `.record-video` | color | #b0b0b0 | - | 记录视频文字颜色 |
| `.record-time` | color | #777 | - | 记录时间文字颜色 |
| `.model-badge` | background | #1f6feb15 | #2196f315 | 模型徽章背景 |
| `.model-badge` | border-color | #1f6feb40 | #2196f340 | 模型徽章边框 |
| `.model-badge` | color | #58a6ff | #2196f3 | 模型徽章文字 |
| `.model-badge:hover` | background | #1f6feb25 | #2196f325 | 模型徽章hover背景 |
| `.model-badge:hover` | border-color | #1f6feb60 | #2196f360 | 模型徽章hover边框 |
| `.btn-delete` | color | #777 | - | 删除按钮文字 |
| `.btn-delete:hover:not(:disabled)` | background | rgba(248, 113, 113, 0.1) | - | 删除按钮hover背景 |
| `.btn-delete:hover:not(:disabled)` | color | #f87171 | - | 删除按钮hover文字 |
| `.sidebar-content::-webkit-scrollbar-track` | background | #1e1e1e | - | 滚动条轨道背景 |
| `.sidebar-content::-webkit-scrollbar-thumb` | background | #444 | - | 滚动条背景 |
| `.sidebar-content::-webkit-scrollbar-thumb:hover` | background | #555 | - | 滚动条hover背景 |
| `.btn-theme-toggle` | background | #2d2d2d | - | 主题切换按钮背景 |
| `.btn-theme-toggle` | border-color | #444 | - | 主题切换按钮边框 |
| `.btn-theme-toggle` | color | #e0e0e0 | - | 主题切换按钮文字 |
| `.btn-theme-toggle:hover` | background | #3d3d3d | - | 主题切换按钮hover背景 |
| `.btn-theme-toggle:hover` | border-color | #555 | - | 主题切换按钮hover边框 |

---

## 3. AnalysisResult.vue

| 元素/组件 | 属性 | 深色模式 | 浅色模式 | 用途描述 |
|-----------|------|----------|----------|----------|
| `.result-panel` | background | #0d1117 | #f5f5f5 | 结果面板背景 |
| `.stat-card` | background | #161b22 | #fff | 统计卡片背景 |
| `.stat-card` | border-color | #30363d | #e0e0e0 | 统计卡片边框 |
| `.stat-icon` | background | #1f6feb20 | #2196f320 | 统计图标背景 |
| `.stat-icon` | color | #58a6ff | #2196f3 | 统计图标颜色 |
| `.stat-label` | color | #8b949e | #666 | 统计标签颜色 |
| `.stat-value` | color | #fff | #333 | 统计值颜色 |
| `.visualization-placeholder` | background | #161b22 | #fff | 可视化占位符背景 |
| `.visualization-placeholder` | border-color | #30363d | #ccc | 可视化占位符边框 |
| `.visualization-placeholder` | color | #8b949e | #666 | 可视化占位符文字 |
| `.placeholder-icon` | color | #30363d | #ccc | 占位符图标颜色 |
| `.visualization-placeholder p` | color | #c9d1d9 | #333 | 占位符段落文字 |
| `.placeholder-hint` | color | #6e7681 | #999 | 占位符提示文字 |
| `.result-content::-webkit-scrollbar-track` | background | #0d1117 | #f5f5f5 | 滚动条轨道背景 |
| `.result-content::-webkit-scrollbar-thumb` | background | #30363d | #ccc | 滚动条背景 |
| `.result-content::-webkit-scrollbar-thumb:hover` | background | #484f58 | #bbb | 滚动条hover背景 |
| `.detail-video-section h3` | color | #fff | #333 | 视频区域标题颜色 |
| `.detail-video-container` | background | #0d1117 | #f5f5f5 | 视频容器背景 |
| `.detail-video-container` | border-color | #30363d | #ccc | 视频容器边框 |
| `.detail-video-controls` | background | #161b22 | #fff | 视频控制栏背景 |
| `.detail-video-controls` | border-color | #30363d | #e0e0e0 | 视频控制栏边框 |
| `.detail-btn-control` | background | #21262d | #fff | 控制按钮背景 |
| `.detail-btn-control` | color | #c9d1d9 | #333 | 控制按钮文字 |
| `.detail-btn-control` | border-color | #30363d | #ccc | 控制按钮边框 |
| `.detail-btn-control:hover` | background | #30363d | #f5f5f5 | 控制按钮hover背景 |
| `.detail-btn-control:hover` | border-color | #8b949e | #999 | 控制按钮hover边框 |
| `.frame-counter` | color | #c9d1d9 | #333 | 帧计数器文字 |
| `.frame-input` | background | #21262d | #fff | 帧输入框背景 |
| `.frame-input` | color | #c9d1d9 | #333 | 帧输入框文字 |
| `.frame-input` | border-color | #30363d | #ccc | 帧输入框边框 |
| `.frame-input:focus` | border-color | #58a6ff | #2196f3 | 帧输入框聚焦边框 |
| `.frame-input:focus` | box-shadow | 0 0 0 2px rgba(88, 166, 255, 0.2) | 0 0 0 2px rgba(33, 150, 243, 0.2) | 帧输入框聚焦阴影 |
| `.frame-input:hover:not(:focus)` | border-color | #484f58 | #999 | 帧输入框hover边框 |
| `.frame-separator` | color | #6e7681 | #666 | 帧分隔符颜色 |
| `.frame-total` | color | #8b949e | #666 | 帧总数颜色 |
| `.frame-label` | color | #6e7681 | #666 | 帧标签颜色 |
| `.detail-video-placeholder` | background | rgba(13, 17, 23, 0.95) | rgba(245, 245, 245, 0.95) | 视频占位符背景 |
| `.detail-video-placeholder .placeholder-icon` | color | #8b949e | #999 | 视频占位符图标 |
| `.detail-video-placeholder .placeholder-text` | color | #c9d1d9 | #333 | 视频占位符文字 |
| `.detail-info-section h3` | color | #fff | #333 | 信息区域标题 |
| `.detail-divider` | background | #30363d | #e0e0e0 | 分隔线背景 |
| `.detail-placeholder .placeholder-icon` | color | #30363d | #ccc | 详情占位符图标 |
| `.detail-placeholder h3` | color | #fff | #333 | 详情占位符标题 |
| `.detail-placeholder > p` | color | #8b949e | #666 | 详情占位符文字 |
| `.detail-placeholder .placeholder-hint` | color | #6e7681 | #999 | 详情占位符提示 |

---

## 4. CellDetailList.vue

| 元素/组件 | 属性 | 深色模式 | 浅色模式 | 用途描述 |
|-----------|------|----------|----------|----------|
| `.cell-list-section h3` | color | #fff | #333 | 列表标题颜色 |
| `.table-placeholder` | background | #161b22 | #fff | 表格容器背景 |
| `.table-placeholder` | border-color | #30363d | #e0e0e0 | 表格容器边框 |
| `.cell-table th` | background | #21262d | #f5f5f5 | 表头背景 |
| `.cell-table th` | color | #8b949e | #666 | 表头文字颜色 |
| `.cell-table th` | border-bottom-color | #30363d | #e0e0e0 | 表头边框颜色 |
| `.cell-table th.sortable:hover` | background | #30363d | #e8e8e8 | 可排列表头hover背景 |
| `.cell-table th.sortable:hover` | color | #c9d1d9 | #333 | 可排序列表头hover文字 |
| `.cell-table th.sortable.disabled:hover` | background | #21262d | #f5f5f5 | 禁用排序列表头hover背景 |
| `.cell-table th.sortable.disabled:hover` | color | #8b949e | #666 | 禁用排序列表头hover文字 |
| `.sort-icon-neutral` | color | #6e7681 | #999 | 中性排序图标颜色 |
| `.sort-icon-active` | color | #58a6ff | #2196f3 | 激活排序图标颜色 |
| `.cell-table td` | border-bottom-color | #21262d | #e0e0e0 | 单元格边框颜色 |
| `.cell-table td` | color | #c9d1d9 | #333 | 单元格文字颜色 |
| `.cell-table tbody tr:hover` | background | #0d1117 | #f5f5f5 | 表格行hover背景 |
| `.btn-view` | background | #21262d | #fff | 查看按钮背景 |
| `.btn-view` | color | #58a6ff | #2196f3 | 查看按钮文字 |
| `.btn-view` | border-color | #30363d | #ccc | 查看按钮边框 |
| `.btn-view:hover` | background | #1f6feb20 | #e3f2fd | 查看按钮hover背景 |
| `.btn-view:hover` | border-color | #58a6ff | #2196f3 | 查看按钮hover边框 |

---

## 5. ResultHeader.vue

| 元素/组件 | 属性 | 深色模式 | 浅色模式 | 用途描述 |
|-----------|------|----------|----------|----------|
| `.result-header` | border-bottom-color | #21262d | #e0e0e0 | 结果头部边框 |
| `.result-header` | background | #161b22 | #fff | 结果头部背景 |
| `.result-header h2` | color | #fff | #333 | 标题颜色 |
| `.header-subtitle` | color | #8b949e | #666 | 副标题颜色 |
| `.model-badge` | background | #1f6feb15 | #2196f315 | 模型徽章背景 |
| `.model-badge` | border-color | #1f6feb40 | #2196f340 | 模型徽章边框 |
| `.model-badge` | color | #58a6ff | #2196f3 | 模型徽章文字 |
| `.model-badge:hover` | background | #1f6feb25 | #2196f325 | 模型徽章hover背景 |
| `.model-badge:hover` | border-color | #1f6feb60 | #2196f360 | 模型徽章hover边框 |
| `.view-toggle` | background | #21262d | #f5f5f5 | 视图切换背景 |
| `.view-toggle` | border-color | #30363d | #ccc | 视图切换边框 |
| `.view-toggle-slider` | background | #1f6feb | #2196f3 | 切换滑块背景 |
| `.view-toggle-item` | color | #8b949e | #666 | 切换项文字 |
| `.view-toggle-item.active` | color | #fff | #fff | 激活切换项文字 |
| `.view-toggle-item:hover` | color | #c9d1d9 | #555 | 切换项hover文字 |
| `.view-toggle-divider` | background | #30363d | #ccc | 切换分隔线 |
| `.btn-action` | background | #21262d | #fff | 操作按钮背景 |
| `.btn-action` | color | #c9d1d9 | #333 | 操作按钮文字 |
| `.btn-action` | border-color | #30363d | #ccc | 操作按钮边框 |
| `.btn-action:hover` | background | #30363d | #f5f5f5 | 操作按钮hover背景 |
| `.btn-action:hover` | border-color | #8b949e | #999 | 操作按钮hover边框 |

---

## 6. VideoPlayer.vue

| 元素/组件 | 属性 | 深色模式 | 浅色模式 | 用途描述 |
|-----------|------|----------|----------|----------|
| `.video-section h3` | color | #fff | #333 | 视频区域标题 |
| `.video-divider` | background | #30363d | #e0e0e0 | 视频分隔线 |
| `.video-controls-bar` | background | #161b22 | #fff | 视频控制栏背景 |
| `.video-controls-bar` | border-color | #30363d | #e0e0e0 | 视频控制栏边框 |
| `.btn-control` | background | #21262d | #fff | 控制按钮背景 |
| `.btn-control` | color | #c9d1d9 | #333 | 控制按钮文字 |
| `.btn-control` | border-color | #30363d | #ccc | 控制按钮边框 |
| `.btn-control:hover` | background | #30363d | #f5f5f5 | 控制按钮hover背景 |
| `.btn-control:hover` | border-color | #8b949e | #999 | 控制按钮hover边框 |
| `.btn-control-primary` | background | #1f6feb | #2196f3 | 主要控制按钮背景 |
| `.btn-control-primary` | color | #fff | #fff | 主要控制按钮文字 |
| `.btn-control-primary` | border-color | #1f6feb | #2196f3 | 主要控制按钮边框 |
| `.btn-control-primary:hover` | background | #388bfd | #1976d2 | 主要控制按钮hover背景 |
| `.video-container` | background | #0d1117 | #f5f5f5 | 视频容器背景 |
| `.video-container` | border-color | #30363d | #ccc | 视频容器边框 |
| `.video-placeholder` | background | rgba(13, 17, 23, 0.95) | rgba(245, 245, 245, 0.95) | 视频占位符背景 |
| `.placeholder-icon` | color | #8b949e | #999 | 占位符图标 |
| `.placeholder-text` | color | #c9d1d9 | #333 | 占位符文字 |
| `.placeholder-hint` | color: | #8b949e | #666 | 占位符提示 |
| `.video-section h3` | color | #fff | #333 | 视频区域标题 |
| `.video-container` | background | #000 | #000 | 视频容器（固定） |
| `.video-container` | border-color | #30363d | #ccc | 视频容器边框 |
| `.rate-dropdown-menu` | background | #21262d | #fff | 下拉菜单背景 |
| `.rate-dropdown-menu` | border-color | #30363d | #ccc | 下拉菜单边框 |
| `.rate-dropdown-menu` | box-shadow | 0 8px 24px rgba(0, 0, 0, 0.4) | 0 8px 24px rgba(0, 0, 0, 0.15) | 下拉菜单阴影 |
| `.rate-option` | color | #c9d1d9 | #333 | 下拉菜单选项文字 |
| `.rate-option:hover` | background | #30363d | #f5f5f5 | 下拉菜单选项hover背景 |
| `.rate-option-active` | background | #1f6feb | #2196f3 | 激活选项背景 |
| `.rate-option-active` | color | #fff | #fff | 激活选项文字 |
| `.rate-option-active:hover` | background | #388bfd | #1976d2 | 激活选项hover背景 |

---

## 7. App.vue

| 元素/组件 | 属性 | 深色模式 | 浅色模式 | 用途描述 |
|-----------|------|----------|----------|----------|
| - | - | - | - | 无颜色定义 |

---

## 8. CellDetailPanel.vue

| 元素/组件 | 属性 | 深色模式 | 浅色模式 | 用途描述 |
|-----------|------|----------|----------|----------|
| `.cell-detail-panel` | background | #0d1117 | - | 细胞详情面板背景 |
| `.detail-header` | border-bottom-color | #21262d | - | 头部边框 |
| `.detail-header` | background | #161b22 | - | 头部背景 |
| `.btn-back` | background | #21262d | - | 返回按钮背景 |
| `.btn-back` | color | #c9d1d9 | - | 返回按钮文字 |
| `.btn-back` | border-color | #30363d | - | 返回按钮边框 |
| `.btn-back:hover` | background | #30363d | - | 返回按钮hover背景 |
| `.btn-back:hover` | border-color | #8b949e | - | 返回按钮hover边框 |
| `.detail-header h2` | color | #fff | - | 标题颜色 |
| `.info-grid .info-item` | background | #161b22 | - | 信息项背景 |
| `.info-grid .info-item` | border-color | #30363d | - | 信息项边框 |
| `.info-label` | color | #8b949e | - | 信息标签颜色 |
| `.info-value` | color | #fff | - | 信息值颜色 |
| `.trajectory-placeholder` | background | #161b22 | - | 轨迹占位符背景 |
| `.trajectory-placeholder` | border-color | #30363d | - | 轨迹占位符边框 |
| `.trajectory-placeholder` | color | #8b949e | - | 轨迹占位符文字 |
| `.placeholder-icon` | color | #30363d | - | 占位符图标 |
| `.trajectory-placeholder p` | color | #c9d1d9 | - | 轨迹占位符段落文字 |
| `.placeholder-hint` | color | #6e7681 | - | 占位符提示 |
| `.table-wrapper` | background | #161b22 | - | 表格包装器背景 |
| `.table-wrapper` | border-color | #30363d | - | 表格包装器边框 |
| `.position-table th` | background | #21262d | - | 位置表头背景 |
| `.position-table th` | color | #8b949e | - | 位置表头文字 |
| `.position-table th` | border-bottom-color | #30363d | - | 位置表头边框 |
| `.position-table td` | border-bottom-color | #21262d | - | 位置单元格边框 |
| `.position-table td` | color | #c9d1d9 | - | 位置单元格文字 |
| `.position-table tbody tr:hover` | background | #0d1117 | - | 位置行hover背景 |
| `.detail-content::-webkit-scrollbar-track` | background | #0d1117 | - | 滚动条轨道背景 |
| `.detail-content::-webkit-scrollbar-thumb` | background | #30363d | - | 滚动条背景 |
| `.detail-content::-webkit-scrollbar-thumb:hover` | background | #484f58 | - | 滚动条hover背景 |

---

## 9. CellPopulationChart.vue

| 元素/组件 | 属性 | 深色模式 | 浅色模式 | 用途描述 |
|-----------|------|----------|----------|----------|
| `.cell-population-chart h3` | color | #fff | #333 | 图表区域标题 |
| `.chart-button` | background | #161b22 | #fff | 图表按钮背景 |
| `.chart-button` | color | #c9d1d9 | #333 | 图表按钮文字 |
| `.chart-button` | border-color | #30363d | #e0e0e0 | 图表按钮边框 |
| `.chart-button:hover` | background | #1f6feb20 | #e3f2fd | 图表按钮hover背景 |
| `.chart-button:hover` | border-color | #58a6ff | #2196f3 | 图表按钮hover边框 |
| `.chart-button:hover` | color | #58a6ff | #2196f3 | 图表按钮hover文字 |
| `.chart-button.active` | background | #1f6feb20 | #e3f2fd | 激活图表按钮背景 |
| `.chart-button.active` | border-color | #58a6ff | #2196f3 | 激活图表按钮边框 |
| `.chart-button.active` | color | #58a6ff | #2196f3 | 激活图表按钮文字 |
| `.visualization-placeholder` | background | #161b22 | #fff | 可视化占位符背景 |
| `.visualization-placeholder` | border-color | #30363d | #e0e0e0 | 可视化占位符边框 |
| `.visualization-placeholder` | color | #8b949e | #666 | 可视化占位符文字 |
| `.placeholder-icon` | color | #30363d | #ccc | 占位符图标 |
| `.visualization-placeholder p` | color | #c9d1d9 | #333 | 占位符段落文字 |
| `.placeholder-hint` | color | #6e7681 | #999 | 占位符提示 |

---

## 10. ConfirmDialog.vue

| 元素/组件 | 属性 | 深色模式 | 浅色模式 | 用途描述 |
|-----------|------|----------|----------|----------|
| `.dialog-overlay` | background | rgba(0, 0, 0, 0.5) | - | 对话框遮罩层 |
| `.dialog-container` | background | #1e1e1e | #fff | 对话框容器背景 |
| `.dialog-container` | border-color | #333 | #e0e0e0 | 对话框容器边框 |
| `.dialog-container` | box-shadow | 0 20px 60px rgba(0, 0, 0, 0.5) | 0 20px 60px rgba(0, 0, 0, 0.3) | 对话框容器阴影 |
| `.dialog-header` | border-bottom-color | #333 | #e0e0e0 | 对话框头部边框 |
| `.dialog-header h3` | color | #fff | #333 | 对话框标题 |
| `.btn-close` | color | #8b949e | #666 | 关闭按钮文字 |
| `.btn-close:hover` | background | rgba(139, 148, 158, 0.1) | rgba(102, 102, 102, 0.1) | 关闭按钮hover背景 |
| `.btn-close:hover` | color | #c9d1d9 | #333 | 关闭按钮hover文字 |
| `.icon-danger` | background | rgba(248, 113, 113, 0.1) | - | 危险图标背景 |
| `.icon-danger` | color | #f87171 | - | 危险图标颜色 |
| `.icon-warning` | background | rgba(251, 191, 36, 0.1) | - | 警告图标背景 |
| `.icon-warning` | color | #fbbf24 | - | 警告图标颜色 |
| `.icon-info` | background | rgba(88, 166, 255, 0.1) | - | 信息图标背景 |
| `.icon-info` | color | #58a6ff | - | 信息图标颜色 |
| `.dialog-message` | color | #c9d1d9 | #333 | 对话框消息文字 |
| `.dialog-footer` | border-top-color | #333 | #e0e0e0 | 对话框底部边框 |
| `.btn-cancel` | color | #c9d1d9 | #333 | 取消按钮文字 |
| `.btn-cancel` | border-color | #30363d | #ccc | 取消按钮边框 |
| `.btn-cancel:hover` | background | rgba(48, 54, 61, 0.1) | rgba(204, 204, 204, 0.1) | 取消按钮hover背景 |
| `.btn-cancel:hover` | border-color | #8b949e | #999 | 取消按钮hover边框 |
| `.btn-danger` | background | #dc2626 | - | 危险按钮背景 |
| `.btn-danger` | color | white | - | 危险按钮文字 |
| `.btn-danger:hover` | background | #ef4444 | - | 危险按钮hover背景 |
| `.btn-warning` | background | #d97706 | - | 警告按钮背景 |
| `.btn-warning` | color | white | - | 警告按钮文字 |
| `.btn-warning:hover` | background | #f59e0b | - | 警告按钮hover背景 |
| `.btn-info` | background | #007acc | - | 信息按钮背景 |
| `.btn-info` | color | white | - | 信息按钮文字 |
| `.btn-info:hover` | background | #005a9e | - | 信息按钮hover背景 |

---

## 11. Toast.vue

| 元素/组件 | 属性 | 深色模式 | 浅色模式 | 用途描述 |
|-----------|------|----------|----------|----------|
| `.toast-item` | background | #1c1917 | #ffffff | Toast项背景 |
| `.toast-item` | box-shadow | 0 4px 12px rgba(0, 0, 0, 0.15) | 0 4px 12px rgba(0, 0, 0, 0.1) | Toast项阴影 |
| `.toast-success` | border-color | #238636 | #4caf50 | 成功Toast边框 |
| `.toast-item:hover` | box-shadow | 0 6px 16px rgba(0, 0, 0, 0.2) | 0 6px 16px rgba(0, 0, 0, 0.15) | Toast项hover阴影 |
| `.toast-success` | background | linear-gradient(135deg, rgba(35, 134, 54, 0.1) 0%, #1c1917 100%) | linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, #ffffff 100%) | 成功Toast背景 |
| `.toast-error` | border-color | #dc2626 | #ef4444 | 错误Toast边框 |
| `.toast-error` | background | linear-gradient(135deg, rgba(220, 38, 38, 0.1) 0%, #1c1917 100%) | linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, #ffffff 100%) | 错误Toast背景 |
| `.toast-warning` | border-color | #f59e0b | #ff9800 | 警告Toast边框 |
| `.toast-warning` | background | linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, #1c1917 100%) | linear-gradient(135deg, rgba(255, 152, 0, 0.1) 0%, #ffffff 100%) | 警告Toast背景 |
| `.toast-info` | border-color | #3b82f6 | #2196f3 | 信息Toast边框 |
| `.toast-info` | background | linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, #1c1917 100%) | linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, #ffffff 100%) | 信息Toast背景 |
| `.toast-success .toast-icon` | color | #238636 | #4caf50 | 成功图标颜色 |
| `.toast-error .toast-icon` | color | #dc2626 | #ef4444 | 错误图标颜色 |
| `.toast-warning .toast-icon` | color | #f59e0b | #ff9800 | 警告图标颜色 |
| `.toast-info .toast-icon` | color | #3b82f6 | #2196f3 | 信息图标颜色 |
| `.toast-message` | color | #c9d1d9 | #333 | Toast消息文字 |
| `.toast-close` | color | #8b949e | #999 | Toast关闭按钮文字 |
| `.toast-close:hover` | background | rgba(139, 148, 158, 0.1) | rgba(153, 153, 153, 0.1) | Toast关闭按钮hover背景 |
| `.toast-close:hover` | color | #c9d1d9 | #333 | Toast关闭按钮hover文字 |

---

## 12. UploadPanel.vue

| 元素/组件 | 属性 | 深色模式 | 浅色模式 | 用途描述 |
|-----------|------|----------|----------|----------|
| `.upload-panel` | background | #0d1117 | #f5f5f5 | 上传面板背景 |
| `h2` | color | #fff | #333 | 标题颜色 |
| `.upload-description` | color | #8b949e | #666 | 描述文字颜色 |
| `.upload-area` | border-color | #30363d | #ccc | 上传区域边框 |
| `.upload-area` | background | #161b22 | #fff | 上传区域背景 |
| `.upload-area.dragging` | border-color | #1f6feb | #2196f3 | 拖拽状态边框 |
| `.upload-area.dragging` | background | #0d1520 | #e3f2fd | 拖拽状态背景 |
| `.upload-area.has-file` | border-color | #238636 | #4caf50 | 有文件状态边框 |
| `.upload-area.has-file` | background | #0d1520 | #e8f5e9 | 有文件状态背景 |
| `.upload-icon` | color | #8b949e | #999 | 上传图标颜色 |
| `.upload-text` | color | #c9d1d9 | #333 | 上传文字颜色 |
| `.upload-hint` | color | #8b949e | #666 | 上传提示颜色 |
| `.file-info` | background | #0d1117 | #f5f5f5 | 文件信息背景 |
| `.file-icon` | color | #58a6ff | - | 文件图标颜色 |
| `.file-name` | color | #c9d1d9 | #333 | 文件名颜色 |
| `.file-size` | color | #8b949e | #666 | 文件大小颜色 |
| `.btn-clear` | border-color | #30363d | #ccc | 清除按钮边框 |
| `.btn-clear` | color | #8b949e | #666 | 清除按钮文字 |
| `.btn-clear:hover` | background | #21262d | #e0e0e0 | 清除按钮hover背景 |
| `.btn-clear:hover` | border-color | #8b949e | #999 | 清除按钮hover边框 |
| `.btn-clear:hover` | color | #c9d1d9 | #333 | 清除按钮hover文字 |
| `.model-label` | color | #c9d1d9 | #333 | 模型标签颜色 |
| `.model-select` | background | #161b22 | #fff | 模型选择框背景 |
| `.model-select` | border-color | #30363d | #ccc | 模型选择框边框 |
| `.model-select` | color | #c9d1d9 | #333 | 模型选择框文字 |
| `.model-select` | background-image (SVG fill) | #8b949e | #666 | 模型选择框下拉箭头图标颜色 |
| `.model-select:hover:not(:disabled)` | background | #21262d | #f5f5f5 | 模型选择框hover背景 |
| `.model-select:hover:not(:disabled)` | border-color | #58a6ff | #2196f3 | 模型选择框hover边框 |
| `.model-select:focus` | border-color | #58a6ff | #2196f3 | 模型选择框聚焦边框 |
| `.model-select:focus` | box-shadow | 0 0 0 3px rgba(88, 166, 255, 0.1) | 0 0 0 3px rgba(33, 150, 243, 0.1) | 模型选择框聚焦阴影 |
| `.model-warning` | background | rgba(220, 38, 38, 0.1) | rgba(239, 68, 68, 0.1) | 模型警告背景 |
| `.model-warning` | border-left-color | #dc2626 | #ef4444 | 模型警告边框 |
| `.model-warning` | color | #f87171 | #ef4444 | 模型警告文字 |
| `.btn-toggle-settings` | background | #161b22 | #fff | 设置切换按钮背景 |
| `.btn-toggle-settings` | border-color | #30363d | #ccc | 设置切换按钮边框 |
| `.btn-toggle-settings` | color | #c9d1d9 | #333 | 设置切换按钮文字 |
| `.btn-toggle-settings:hover` | background | #21262d | #f5f5f5 | 设置切换按钮hover背景 |
| `.btn-toggle-settings:hover` | border-color | #58a6ff | #2196f3 | 设置切换按钮hover边框 |
| `.settings-content` | background | #161b22 | #fff | 设置内容背景 |
| `.settings-content` | border-color | #30363d | #ccc | 设置内容边框 |
| `.setting-label` | color | #c9d1d9 | #333 | 设置标签颜色 |
| `.setting-value` | background | #21262d | #e0e0e0 | 设置值背景 |
| `.setting-value` | color | #58a6ff | #2196f3 | 设置值文字 |
| `.setting-slider` | background | #21262d | #e0e0e0 | 滑块背景 |
| `.setting-slider::-webkit-slider-thumb` | background | #58a6ff | - | 滑块滑块背景 |
| `.setting-slider::-webkit-slider-thumb:hover` | background | #1f6feb | - | 滑块滑块hover背景 |
| `.setting-slider::-moz-range-thumb` | background | #58a6ff | - | 滑块滑块背景（Firefox） |
| `.setting-slider::-moz-range-thumb:hover` | background | #1f6feb | - | 滑块滑块hover背景（Firefox） |
| `.setting-select` | background | #21262d | #fff | 下拉选择背景 |
| `.setting-select` | border-color | #30363d | #ccc | 下拉选择边框 |
| `.setting-select` | color | #c9d1d9 | #333 | 下拉选择文字 |
| `.setting-select` | background-image (SVG fill) | #8b949e | #666 | 下拉选择下拉箭头图标颜色 |
| `.setting-select:hover` | background | #30363d | #f5f5f5 | 下拉选择hover背景 |
| `.setting-select:hover` | border-color | #58a6ff | #2196f3 | 下拉选择hover边框 |
| `.setting-select:hover` | color | #fff | #333 | 下拉选择hover文字 |
| `.setting-select:focus` | border-color | #58a6ff | #2196f3 | 下拉选择聚焦边框 |
| `.setting-select:focus` | box-shadow | 0 0 0 3px rgba(88, 166, 255, 0.1) | 0 0 0 3px rgba(33, 150, 243, 0.1) | 下拉选择聚焦阴影 |
| `.setting-select:focus` | background | #30363d | #fff | 下拉选择聚焦背景 |
| `.setting-hint` | color | #8b949e | #666 | 设置提示颜色 |
| `.upload-progress` | background | #161b22 | #fff | 上传进度背景 |
| `.upload-progress` | border-color | #30363d | #ccc | 上传进度边框 |
| `.progress-bar` | background | #21262d | #e0e0e0 | 进度条背景 |
| `.progress-fill` | background | linear-gradient(90deg, #238636, #2ea043) | - | 进度填充背景 |
| `.progress-text` | color | #58a6ff | #2196f3 | 进度文字颜色 |
| `.progress-message` | color | #8b949e | #666 | 进度消息颜色 |
| `.progress-frame-info` | color | #58a6ff | #2196f3 | 进度帧信息颜色 |
| `.upload-error` | background | #1c1917 | #fff5f5 | 错误消息背景 |
| `.upload-error` | border-color | #dc2626 | #ef4444 | 错误消息边框 |
| `.upload-error` | color | #f87171 | - | 错误消息文字 |
| `.btn-close-error` | color | #f87171 | - | 关闭错误按钮文字 |
| `.btn-close-error:hover` | background | rgba(248, 113, 113, 0.1) | - | 关闭错误按钮hover背景 |
| `.btn-submit` | background | #238636 | - | 提交按钮背景 |
| `.btn-submit` | color | white | - | 提交按钮文字 |
| `.btn-submit:hover:not(:disabled)` | background | #2ea043 | - | 提交按钮hover背景 |
| `.btn-submit:disabled` | background | #21262d | #e0e0e0 | 提交按钮禁用背景 |
| `.btn-submit:disabled` | color | #6e7681 | #999 | 提交按钮禁用文字 |

---

## 13. ModelUploadView.vue

| 元素/组件 | 属性 | 深色模式 | 浅色模式 | 用途描述 |
|-----------|------|----------|----------|----------|
| `.model-upload-view` | background | #0d1117 | - | 模型上传视图背景 |
| `.model-upload-view` | color | #c9d1d9 | - | 模型上传视图文字 |
| `.upload-header h1` | color | #fff | #333 | 标题颜色 |
| `.subtitle` | color | #8b949e | #666 | 副标题颜色 |
| `.upload-area` | border-color | #30363d | #ccc | 上传区域边框 |
| `.upload-area` | background | #161b22 | #fff | 上传区域背景 |
| `.upload-area:hover` | border-color | #1f6feb | #2196f3 | 上传区域hover边框 |
| `.upload-area:hover` | background | #0d1520 | #e3f2fd | 上传区域hover背景 |
| `.upload-area.has-file` | border-color | #238636 | #4caf50 | 有文件状态边框 |
| `.upload-area.has-file` | background | #0d1520 | #e8f5e9 | 有文件状态背景 |
| `.upload-icon` | color | #8b949e | #999 | 上传图标颜色 |
| `.upload-text` | color | #c9d1d9 | #333 | 上传文字颜色 |
| `.upload-hint` | color | #8b949e | #666 | 上传提示颜色 |
| `.file-info` | background | #0d1117 | #f5f5f5 | 文件信息背景 |
| `.file-icon` | color | #58a6ff | - | 文件图标颜色 |
| `.file-name` | color | #c9d1d9 | #333 | 文件名颜色 |
| `.file-size` | color | #8b949e | #666 | 文件大小颜色 |
| `.btn-clear` | border-color | #30363d | #ccc | 清除按钮边框 |
| `.btn-clear` | color | #8b949e | #666 | 清除按钮文字 |
| `.btn-clear:hover` | background | #21262d | #e0e0e0 | 清除按钮hover背景 |
| `.btn-clear:hover` | border-color | #8b949e | #999 | 清除按钮hover边框 |
| `.btn-clear:hover` | color | #c9d1d9 | #333 | 清除按钮hover文字 |
| `.btn-submit` | background | #fb923c | - | 提交按钮背景 |
| `.btn-submit` | color | white | - | 提交按钮文字 |
| `.btn-submit:hover:not(:disabled)` | background | #f97316 | - | 提交按钮hover背景 |
| `.btn-submit:disabled` | background | #21262d | #e0e0e0 | 提交按钮禁用背景 |
| `.btn-submit:disabled` | color | #6e7681 | #999 | 提交按钮禁用文字 |
| `.error-message` | background | #1c1917 | #fff5f5 | 错误消息背景 |
| `.error-message` | border-color | #dc2626 | #ef4444 | 错误消息边框 |
| `.error-message` | color | #f87171 | - | 错误消息文字 |
| `.btn-close-error` | color | #f87171 | - | 关闭错误按钮文字 |
| `.btn-close-error:hover` | background | rgba(248, 113, 113, 0.1) | - | 关闭错误按钮hover背景 |

---

## 14. ProgressView.vue

| 元素/组件 | 属性 | 深色模式 | 浅色模式 | 用途描述 |
|-----------|------|----------|----------|----------|
| `.progress-view` | background | #0d1117 | #f5f5f5 | 进度视图背景 |
| `.progress-view` | color | #c9d1d9 | #333 | 进度视图文字 |
| `.error-icon` | color | #f87171 | - | 错误图标颜色 |
| `.error-container h2` | color | #fff | #333 | 错误标题颜色 |
| `.error-message` | color | #8b949e | #666 | 错误消息颜色 |
| `.error-hint` | color | #6e7681 | #999 | 错误提示颜色 |
| `.progress-header h2` | color | #fff | #333 | 进度标题颜色 |
| `.video-name` | color | #8b949e | #666 | 视频名称颜色 |
| `.progress-bar` | background | #21262d | #e0e0e0 | 进度条背景 |
| `.progress-fill` | background | linear-gradient(90deg, #238636, #2ea043) | - | 进度填充背景 |
| `.progress-text` | color | #238636 | #4caf50 | 进度文字颜色 |
| `.status-info` | background | #161b22 | #fff | 状态信息背景 |
| `.status-info` | border-color | #30363d | #ccc | 状态信息边框 |
| `.status-item:not(:last-child)` | border-bottom-color | #21262d | #e0e0e0 | 状态项边框 |
| `.status-label` | color | #8b949e | #666 | 状态标签颜色 |
| `.status-value` | color | #c9d1d9 | #333 | 状态值颜色 |
| `.steps-section` | background | #161b22 | #fff | 步骤区域背景 |
| `.steps-section` | border-color | #30363d | #ccc | 步骤区域边框 |
| `.step-item:not(:last-child)` | border-bottom-color | #21262d | #e0e0e0 | 步骤项边框 |
| `.step-icon` | color | #6e7681 | #ccc | 步骤图标颜色 |
| `.step-item.current .step-icon` | color | #fb923c | - | 当前步骤图标颜色 |
| `.step-title` | color | #c9d1d9 | #333 | 步骤标题颜色 |
| `.step-desc` | color | #8b949e | #666 | 步骤描述颜色 |
| `.hint-text` | color | #6e7681 | #999 | 提示文字颜色 |
| `.hint-subtext` | color | #238636 | #4caf50 | 提示子文字颜色 |
| `.btn-primary` | background | #238636 | #4caf50 | 主要按钮背景 |
| `.btn-primary` | color | white | - | 主要按钮文字 |
| `.btn-primary:hover` | background | #2ea043 | #66bb6a | 主要按钮hover背景 |
| `.btn-secondary` | background | #21262d | #f5f5f5 | 次要按钮背景 |
| `.btn-secondary` | color | #c9d1d9 | #333 | 次要按钮文字 |
| `.btn-secondary` | border-color | #30363d | #ccc | 次要按钮边框 |
| `.btn-secondary:hover` | background | #30363d | #e0e0e0 | 次要按钮hover背景 |
| `.btn-secondary:hover` | border-color | #484f58 | #bbb | 次要按钮hover边框 |

---

## 颜色总结

### 深色模式主要颜色
- **主背景**: #0d1117
- **次级背景**: #161b22, #1e1e1e, #21262d, #252525, #2d2d2d, #30363d
- **边框**: #30363d, #333, #444, #484f58, #555
- **主要文字**: #fff, #c9d1d9, #e0e0e0
- **次要文字**: #8b949e, #6e7681, #777, #b0b0b0
- **强调色（蓝色）**: #58a6ff, #1f6feb, #388bfd
- **成功色（绿色）**: #238636, #2ea043, #4ade80
- **警告色（橙色）**: #fb923c, #f97316, #fbbf24
- **危险色（红色）**: #dc2626, #ef4444, #f87171
- **信息色（紫色）**: #007acc, #005a9e

### 浅色模式主要颜色
- **主背景**: #f5f5f5, #fff
- **次级背景**: #e0e0e0, #e3f2fd, #e8f5e9, #f5f5f5
- **边框**: #ccc, #e0e0e0, #999, #bbb
- **主要文字**: #333
- **次要文字**: #666, #999
- **强调色（蓝色）**: #2196f3, #1976d2, #66bb6a
- **成功色（绿色）**: #4caf50, #66bb6a
- **警告色（橙色）**: #ff9800, #fbbf24
- **危险色（红色）**: #ef4444, #f87171
- **信息色**: #2196f3

---

## 建议

基于以上分析，建议创建以下CSS变量以便统一管理深色和浅色模式的颜色：

```css
:root {
  /* ========== 深色模式 - 背景色 ========== */
  --bg-main: #0d1117;          /* 主区域背景（所有主面板：cell-tracking-view, result-panel, upload-panel, model-upload-view, progress-view） */
  --bg-sidebar: #1e1e1e;       /* 侧边栏背景（sidebar整体） */
  --bg-record: #252525;        /* 侧边栏记录项背景（record-item） */
  --bg-record-hover: #2d2d2d;  /* 记录项hover背景（record-item:hover） */
  --bg-record-active: #264f78; /* 记录项激活背景（record-item.active） */
  --bg-dialog: #1e1e1e;        /* 对话框背景（dialog-container） */
  --bg-card: #161b22;          /* 卡片背景（stat-card, settings-content等） */
  --bg-input: #21262d;         /* 输入框背景（model-select, setting-select, frame-input等） */
  --bg-hover: #30363d;         /* 通用hover背景（可排序列表头hover、按钮hover等） */
  --bg-toast: #1c1917;         /* Toast背景（toast-item） */
  --bg-video: #000;            /* 视频背景（video-container） */
  --bg-overlay: rgba(0, 0, 0, 0.5);  /* 遮罩层背景（dialog-overlay） */

  /* ========== 深色模式 - 边框色 ========== */
  --border-color: #30363d;     /* 通用边框（按钮、输入框、卡片等） */
  --border-secondary: #333;    /* 次级边框（侧边栏边框、对话框边框等） */
  --border-tertiary: #444;     /* 三级边框（滚动条、hover边框等） */
  --border-hover: #484f58;     /* hover状态边框（输入框hover、按钮hover等） */
  --border-active: #58a6ff;    /* 激活状态边框（focus、active状态） */

  /* ========== 深色模式 - 文字色 ========== */
  --text-primary: #fff;        /* 主要文字（标题、重要内容） */
  --text-secondary: #c9d1d9;   /* 次要文字（描述、内容文字） */
  --text-muted: #8b949e;       /* 弱化文字（标签、提示） */
  --text-disabled: #6e7681;    /* 禁用文字（disabled状态） */
  --text-icon: #30363d;        /* 图标颜色（占位符图标） */

  /* ========== 深色模式 - 强调色 ========== */
  --accent-blue: #58a6ff;      /* 蓝色强调（主要按钮、链接、图标） */
  --accent-blue-hover: #1f6feb;/* 蓝色hover（按钮hover、链接hover） */
  --accent-blue-active: #388bfd; /* 蓝色激活（按下状态） */
  --accent-info: #007acc;      /* 信息色（信息按钮、信息图标） */
  --accent-info-hover: #005a9e; /* 信息色hover */

  /* ========== 深色模式 - 状态色 ========== */
  --success: #238636;          /* 成功色（成功按钮、成功图标） */
  --success-hover: #2ea043;    /* 成功色hover */
  --success-light: #4ade80;    /* 成功色浅色（状态点、进度条） */
  --success-bg: #0e5a2b;       /* 成功色背景（状态徽章） */
  
  --warning: #fb923c;          /* 警告色（警告按钮、警告图标） */
  --warning-hover: #f97316;    /* 警告色hover */
  --warning-light: #fbbf24;    /* 警告色浅色（警告图标） */
  --warning-bg: #5a4a0e;       /* 警告色背景（状态徽章） */
  
  --danger: #dc2626;           /* 危险色（危险按钮、危险图标） */
  --danger-hover: #ef4444;     /* 危险色hover */
  --danger-light: #f87171;     /* 危险色浅色（错误文字、删除hover） */
  --danger-bg: rgba(220, 38, 38, 0.1); /* 危险色背景（警告框、危险图标背景） */

  /* ========== 深色模式 - 特殊色 ========== */
  --upload-hover-bg: #0d1520;  /* 上传区域hover背景 */
  --upload-success-bg: #e8f5e9; /* 上传成功背景 */
  --upload-error-bg: #1c1917;  /* 上传错误背景 */
  --btn-upload: #fb923c;       /* 上传按钮背景 */
  --btn-upload-hover: #f97316; /* 上传按钮hover背景 */

  /* ========== 深色模式 - 透明度 ========== */
  --alpha-focus: rgba(88, 166, 255, 0.1);      /* focus背景透明度（输入框focus） */
  --alpha-focus-ring: rgba(88, 166, 255, 0.2); /* focus环透明度（focus阴影） */
  --alpha-hover: rgba(248, 113, 113, 0.1);     /* hover背景透明度（删除按钮hover） */
  --alpha-badge: rgba(31, 254, 235, 0.21);      /* badge背景透明度（模型徽章） */
  --alpha-badge-hover: rgba(31, 254, 235, 0.37); /* badge hover背景透明度 */
  --alpha-toast: rgba(13, 17, 23, 0.95);        /* Toast背景透明度 */

  /* ========== 深色模式 - 阴影 ========== */
  --shadow-sm: 0 4px 12px rgba(0, 0, 0, 0.15);      /* 小阴影（Toast默认） */
  --shadow-md: 0 6px 16px rgba(0, 0, 0, 0.2);       /* 中阴影（Toast hover） */
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.4);       /* 大阴影（下拉菜单深色） */
  --shadow-xl: 0 20px 60px rgba(0, 0, 0, 0.5);      /* 特大阴影（对话框深色） */
  --shadow-success: 0 0 6px rgba(74, 222, 128, 0.5); /* 成功状态阴影（完成状态点） */
  --shadow-warning: 0 0 6px rgba(251, 146, 60, 0.5); /* 警告状态阴影（处理状态点） */
}

:root:not(.dark) {
  /* ========== 浅色模式 - 背景色 ========== */
  --bg-main: #f5f5f5;          /* 主区域背景（所有主面板） */
  --bg-sidebar: #fff;          /* 侧边栏背景（sidebar整体） */
  --bg-record: #f5f5f5;        /* 侧边栏记录项背景（record-item） */
  --bg-record-hover: #e0e0e0;  /* 记录项hover背景（record-item:hover） */
  --bg-record-active: #e3f2fd; /* 记录项激活背景（record-item.active） */
  --bg-dialog: #fff;           /* 对话框背景（dialog-container） */
  --bg-card: #fff;             /* 卡片背景（stat-card, settings-content等） */
  --bg-input: #fff;            /* 输入框背景（model-select, setting-select, frame-input等） */
  --bg-hover: #e8e8e8;         /* 通用hover背景（可排序列表头hover、按钮hover等） */
  --bg-toast: #ffffff;         /* Toast背景（toast-item） */
  --bg-video: #000;            /* 视频背景（video-container） */
  --bg-overlay: rgba(0, 0, 0, 0.5);  /* 遮罩层背景（dialog-overlay） */

  /* ========== 浅色模式 - 边框色 ========== */
  --border-color: #ccc;        /* 通用边框（按钮、输入框、卡片等） */
  --border-secondary: #e0e0e0; /* 次级边框（表格边框、对话框边框等） */
  --border-tertiary: #999;     /* 三级边框（滚动条、hover边框等） */
  --border-hover: #bbb;        /* hover状态边框（输入框hover、按钮hover等） */
  --border-active: #2196f3;    /* 激活状态边框（focus、active状态） */

  /* ========== 浅色模式 - 文字色 ========== */
  --text-primary: #333;        /* 主要文字（标题、重要内容） */
  --text-secondary: #666;      /* 次要文字（描述、内容文字） */
  --text-muted: #999;          /* 弱化文字（标签、提示） */
  --text-disabled: #999;       /* 禁用文字（disabled状态） */
  --text-icon: #ccc;           /* 图标颜色（占位符图标） */

  /* ========== 浅色模式 - 强调色 ========== */
  --accent-blue: #2196f3;      /* 蓝色强调（主要按钮、链接、图标） */
  --accent-blue-hover: #1976d2;/* 蓝色hover（按钮hover、链接hover） */
  --accent-blue-active: #1976d2; /* 蓝色激活（按下状态） */
  --accent-info: #2196f3;      /* 信息色（信息按钮、信息图标） */

  /* ========== 浅色模式 - 状态色 ========== */
  --success: #4caf50;          /* 成功色（成功按钮、成功图标） */
  --success-hover: #66bb6a;    /* 成功色hover */
  --success-light: #4caf50;    /* 成功色浅色（状态点、进度条） */
  
  --warning: #ff9800;          /* 警告色（警告按钮、警告图标） */
  --warning-hover: #fbbf24;    /* 警告色hover */
  --warning-light: #fbbf24;    /* 警告色浅色（警告图标） */
  
  --danger: #ef4444;           /* 危险色（危险按钮、危险图标） */
  --danger-hover: #f87171;     /* 危险色hover */
  --danger-light: #f87171;     /* 危险色浅色（错误文字、删除hover） */
  --danger-bg: rgba(239, 68, 68, 0.1); /* 危险色背景（警告框、危险图标背景） */

  /* ========== 浅色模式 - 特殊色 ========== */
  --upload-hover-bg: #e3f2fd;  /* 上传区域hover背景 */
  --upload-success-bg: #e8f5e9; /* 上传成功背景 */
  --upload-error-bg: #fff5f5;  /* 上传错误背景 */
  --btn-upload: #fb923c;       /* 上传按钮背景 */
  --btn-upload-hover: #f97316; /* 上传按钮hover背景 */

  /* ========== 浅色模式 - 透明度 ========== */
  --alpha-focus: rgba(33, 150, 243, 0.1);      /* focus背景透明度（输入框focus） */
  --alpha-focus-ring: rgba(33, 150, 243, 0.2); /* focus环透明度（focus阴影） */
  --alpha-hover: rgba(204, 204, 204, 0.1);     /* hover背景透明度（删除按钮hover） */
  --alpha-badge: rgba(33, 150, 243, 0.21);      /* badge背景透明度（模型徽章） */
  --alpha-badge-hover: rgba(33, 150, 243, 0.37); /* badge hover背景透明度 */
  --alpha-toast: rgba(245, 245, 245, 0.95);     /* Toast背景透明度 */

  /* ========== 浅色模式 - 阴影 ========== */
  --shadow-sm: 0 4px 12px rgba(0, 0, 0, 0.1);       /* 小阴影（Toast默认） */
  --shadow-md: 0 6px 16px rgba(0, 0, 0, 0.15);      /* 中阴影（Toast hover） */
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.15);      /* 大阴影（下拉菜单浅色） */
  --shadow-xl: 0 20px 60px rgba(0, 0, 0, 0.3);      /* 特大阴影（对话框浅色） */
}
```