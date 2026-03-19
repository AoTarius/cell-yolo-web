<script setup lang="ts">
import '@/assets/styles/colors.css'
import { computed } from 'vue'
import type { AnalysisRecord } from '@/stores/analysisStore'

type TabType = 'video' | 'cell' | 'chart' | 'frame'

const props = defineProps<{
  record: AnalysisRecord
  isExporting: boolean
  activeTab: TabType
}>()

const emit = defineEmits<{
  export: [format: 'csv' | 'json']
  download: []
  tabChange: [tab: TabType]
}>()

// 滑块位置计算
const sliderStyle = computed(() => {
  const tabPositions: Record<TabType, string> = {
    video: '0%',
    cell: '25%',
    chart: '50%',
    frame: '75%'
  }
  return {
    left: tabPositions[props.activeTab]
  }
})

// 切换选项卡
function switchTab(tab: TabType) {
  emit('tabChange', tab)
}
</script>

<template>
  <div class="result-header">
    <div>
      <h2>{{ record.task_name || record.video_name }}</h2>
      <div class="header-info">
        <p class="header-subtitle">任务ID: {{ record.task_id }}</p>
        <span class="model-badge">
          <svg
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
            class="model-icon"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
            ></path>
          </svg>
          {{ record.model_name || record.result?.model_name || 'N/A' }}
        </span>
      </div>
    </div>
    <div class="header-actions">
      <div class="view-toggle">
        <div class="view-toggle-slider" :style="sliderStyle"></div>
        <span class="view-toggle-item" :class="{ active: props.activeTab === 'video' }" @click="switchTab('video')">视频对比</span>
        <span class="view-toggle-divider"></span>
        <span class="view-toggle-item" :class="{ active: props.activeTab === 'cell' }" @click="switchTab('cell')">细胞详情</span>
        <span class="view-toggle-divider"></span>
        <span class="view-toggle-item" :class="{ active: props.activeTab === 'chart' }" @click="switchTab('chart')">图表绘制</span>
        <span class="view-toggle-divider"></span>
        <span class="view-toggle-item" :class="{ active: props.activeTab === 'frame' }" @click="switchTab('frame')">逐帧分析</span>
      </div>
      <div class="header-actions-spacer"></div>
      <button class="btn-action" @click="emit('export', 'csv')" :disabled="isExporting">
        <svg
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
          ></path>
        </svg>
        {{ isExporting ? '导出中...' : '导出 CSV' }}
      </button>
      <button class="btn-action" @click="emit('export', 'json')" :disabled="isExporting">
        <svg
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          ></path>
        </svg>
        导出 JSON
      </button>
      <button class="btn-action" @click="emit('download')" :disabled="isExporting">
        <svg
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
          ></path>
        </svg>
        下载视频
      </button>
    </div>
  </div>
</template>

<style scoped>
.result-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-card);
  transition: border-color 0.3s, background 0.3s;
}

:global(:root:not(.dark)) .result-header {
  border-bottom-color: var(--border-color-light);
  background: var(--bg-card-light);
}

.result-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.25rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .result-header h2 {
  color: var(--text-primary-light);
}

.header-subtitle {
  color: var(--text-muted);
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .header-subtitle {
  color: var(--text-muted-light);
}

.header-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.model-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.6rem;
  background: var(--alpha-badge);
  border: 1px solid var(--alpha-badge-hover);
  border-radius: 4px;
  color: var(--accent-blue);
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.2s;
}

:global(:root:not(.dark)) .model-badge {
  background: var(--alpha-badge);
  border-color: var(--alpha-badge-hover);
  color: var(--accent-blue);
}

.model-badge:hover {
  background: var(--alpha-badge-hover);
  border-color: var(--alpha-badge-hover);
}

:global(:root:not(.dark)) .model-badge:hover {
  background: var(--alpha-badge-hover);
  border-color: var(--alpha-badge-hover);
}

.model-icon {
  width: 12px;
  height: 12px;
}

.view-toggle {
  display: flex;
  align-items: center;
  position: relative;
  padding: 0.25rem;
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  overflow: hidden;
  width: 320px;
  margin-right: 5vh;
}

:global(:root:not(.dark)) .view-toggle {
  background: var(--bg-hover);
  border-color: var(--border-color-light);
}

.view-toggle-slider {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  background: var(--accent-blue);
  border-radius: 4px;
  transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 0;
  width: 25%;
}

:global(:root:not(.dark)) .view-toggle-slider {
  background: var(--accent-blue);
}

.view-toggle-item {
  padding: 0.5rem 0.25rem;
  font-size: 0.875rem;
  color: var(--text-muted);
  transition: all 0.2s;
  position: relative;
  z-index: 1;
  flex: 1;
  text-align: center;
}

:global(:root:not(.dark)) .view-toggle-item {
  color: var(--text-muted-light);
}

.view-toggle-item.active {
  color: #fff;
  font-weight: 500;
}

:global(:root:not(.dark)) .view-toggle-item.active {
  color: #fff;
}

.view-toggle-item:hover {
  color: var(--text-secondary);
}

:global(:root:not(.dark)) .view-toggle-item:hover {
  color: var(--text-disabled-light);
}

.view-toggle-divider {
  width: 1px;
  height: 16px;
  background: var(--border-color);
  margin: 0 0.25rem;
}

:global(:root:not(.dark)) .view-toggle-divider {
  background: var(--border-color-light);
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.header-actions-spacer {
  flex: 2;
  min-width: 0;
}

.btn-action {
  padding: 0.5rem 1rem;
  background: var(--bg-input);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: fit-content;
  margin: 0 auto;
  white-space: nowrap;
}

:global(:root:not(.dark)) .btn-action {
  background: var(--bg-card-light);
  color: var(--text-primary-light);
  border-color: var(--border-color-light);
}

.btn-action:hover {
  background: var(--bg-hover);
  border-color: var(--text-muted);
  color: var(--text-primary);
}

:global(:root:not(.dark)) .btn-action:hover {
  background: var(--bg-hover);
  border-color: var(--text-disabled-light);
}

.btn-action svg {
  width: 16px;
  height: 16px;
}
</style>