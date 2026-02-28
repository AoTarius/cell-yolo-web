<script setup lang="ts">
import type { AnalysisRecord } from '@/stores/analysisStore'

const props = defineProps<{
  record: AnalysisRecord
  isExporting: boolean
}>()

const emit = defineEmits<{
  export: [format: 'csv' | 'json']
  download: []
}>()
</script>

<template>
  <div class="result-header">
    <div>
      <h2>{{ record.video_name }}</h2>
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
          {{ record.result?.model_name || 'N/A' }}
        </span>
      </div>
    </div>
    <div class="header-actions">
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
  border-bottom: 1px solid #21262d;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #161b22;
  transition: border-color 0.3s, background 0.3s;
}

:global(:root:not(.dark)) .result-header {
  border-bottom-color: #e0e0e0;
  background: #fff;
}

.result-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #fff;
  margin: 0 0 0.25rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .result-header h2 {
  color: #333;
}

.header-subtitle {
  color: #8b949e;
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .header-subtitle {
  color: #666;
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
  background: #1f6feb15;
  border: 1px solid #1f6feb40;
  border-radius: 4px;
  color: #58a6ff;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.2s;
}

:global(:root:not(.dark)) .model-badge {
  background: #2196f315;
  border-color: #2196f340;
  color: #2196f3;
}

.model-badge:hover {
  background: #1f6feb25;
  border-color: #1f6feb60;
}

:global(:root:not(.dark)) .model-badge:hover {
  background: #2196f325;
  border-color: #2196f360;
}

.model-icon {
  width: 12px;
  height: 12px;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-action {
  padding: 0.5rem 1rem;
  background: #21262d;
  color: #c9d1d9;
  border: 1px solid #30363d;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

:global(:root:not(.dark)) .btn-action {
  background: #fff;
  color: #333;
  border-color: #ccc;
}

.btn-action:hover {
  background: #30363d;
  border-color: #8b949e;
}

:global(:root:not(.dark)) .btn-action:hover {
  background: #f5f5f5;
  border-color: #999;
}

.btn-action svg {
  width: 16px;
  height: 16px;
}
</style>