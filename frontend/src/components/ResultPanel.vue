<script setup lang="ts">
import { ref } from 'vue'
import { useAnalysisStore } from '@/stores/analysisStore'
import type { AnalysisRecord } from '@/stores/analysisStore'
import { useAnalysisApi } from '@/composables/useAnalysisApi'
import CellDetailPanel from './CellDetailPanel.vue'

const props = defineProps<{
  record: AnalysisRecord
}>()

const store = useAnalysisStore()
const api = useAnalysisApi()

const isExporting = ref(false)
const exportError = ref<string | null>(null)

// 处理查看细胞详情
function handleViewCell(cellId: string) {
  store.selectCell(cellId)
}

// 处理返回结果列表
function handleBackToList() {
  store.backToResultList()
}

// 处理数据导出
async function handleExport(format: 'csv' | 'json' = 'csv') {
  try {
    isExporting.value = true
    exportError.value = null
    await api.exportData(props.record.task_id, format)
  } catch (error: any) {
    exportError.value = error.message || '导出失败'
    console.error('Export error:', error)
  } finally {
    isExporting.value = false
  }
}

// 处理视频下载
async function handleDownloadVideo() {
  try {
    isExporting.value = true
    exportError.value = null
    await api.downloadVideo(props.record.task_id, props.record.video_name)
  } catch (error: any) {
    exportError.value = error.message || '下载失败'
    console.error('Download error:', error)
  } finally {
    isExporting.value = false
  }
}

// 获取视频 URL
function getVideoUrl(taskId: string): string {
  return `/api/video/${taskId}/`
}

// 处理视频错误
function handleVideoError(event: Event) {
  console.error('Video playback error:', event)
  exportError.value = '视频加载失败'
}
</script>

<template>
  <!-- 显示细胞详情 -->
  <CellDetailPanel
    v-if="store.selectedCellData"
    :cell-data="store.selectedCellData"
    @back="handleBackToList"
  />

  <!-- 显示结果列表 -->
  <div v-else class="result-panel">
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
        <button class="btn-action" @click="handleExport('csv')" :disabled="isExporting">
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
        <button class="btn-action" @click="handleExport('json')" :disabled="isExporting">
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
        <button class="btn-action" @click="handleDownloadVideo" :disabled="isExporting">
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

    <div class="result-content">
      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">
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
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              ></path>
            </svg>
          </div>
          <div class="stat-content">
            <p class="stat-label">细胞总数</p>
            <p class="stat-value">{{ record.result?.cell_count || 0 }}</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">
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
                d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"
              ></path>
            </svg>
          </div>
          <div class="stat-content">
            <p class="stat-label">总帧数</p>
            <p class="stat-value">{{ record.result?.total_frames || 0 }}</p>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">
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
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              ></path>
            </svg>
          </div>
          <div class="stat-content">
            <p class="stat-label">视频时长</p>
            <p class="stat-value">
              {{ record.result?.video_duration || 0 }}s
            </p>
          </div>
        </div>
      </div>

      <!-- 标注视频播放器 -->
      <div v-if="record.result?.output_video_path" class="video-section">
        <h3>标注视频</h3>
        <div class="video-container">
          <video
            :src="getVideoUrl(record.task_id)"
            controls
            class="video-player"
            @error="handleVideoError"
          >
            您的浏览器不支持视频播放
          </video>
        </div>
      </div>

      <!-- 3D轨迹图占位 -->
      <div class="visualization-section">
        <h3>细胞轨迹 3D 可视化</h3>
        <div class="visualization-placeholder">
          <svg
            class="placeholder-icon"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
            ></path>
          </svg>
          <p>3D 轨迹图 (X-Y-Time)</p>
          <p class="placeholder-hint">此处将展示细胞运动轨迹的三维可视化</p>
        </div>
      </div>

      <!-- 细胞列表占位 -->
      <div class="cell-list-section">
        <h3>细胞详细信息</h3>
        <div class="table-placeholder">
          <table class="cell-table">
            <thead>
              <tr>
                <th>细胞ID</th>
                <th>首次出现</th>
                <th>最后出现</th>
                <th>存活帧数</th>
                <th>平均速度</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="cell in record.result?.cells || []" :key="cell.cell_id">
                <td>{{ cell.cell_id }}</td>
                <td>
                  第 {{ cell.frames.length > 0 ? cell.frames[0]?.frame_number ?? '-' : '-' }} 帧
                </td>
                <td>
                  第
                  {{
                    cell.frames.length > 0
                      ? cell.frames[cell.frames.length - 1]?.frame_number ?? '-'
                      : '-'
                  }}
                  帧
                </td>
                <td>{{ cell.frames.length }} 帧</td>
                <td>
                  {{
                    cell.frames.length > 0
                      ? (
                          cell.frames.reduce((sum, f) => sum + f.velocity.speed, 0) /
                          cell.frames.length
                        ).toFixed(2)
                      : '0.00'
                  }}
                  px/frame
                </td>
                <td>
                  <button class="btn-view" @click="handleViewCell(cell.cell_id)">查看详情</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.result-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #0d1117;
  overflow: hidden;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .result-panel {
  background: #f5f5f5;
}

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

.result-content {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 1.25rem;
  display: flex;
  gap: 1rem;
  align-items: center;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .stat-card {
  background: #fff;
  border-color: #e0e0e0;
}

.stat-icon {
  width: 48px;
  height: 48px;
  background: #1f6feb20;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #58a6ff;
  flex-shrink: 0;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .stat-icon {
  background: #2196f320;
  color: #2196f3;
}

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 0.875rem;
  color: #8b949e;
  margin: 0 0 0.25rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .stat-label {
  color: #666;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 600;
  color: #fff;
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .stat-value {
  color: #333;
}

.video-section {
  margin-bottom: 2rem;
}

.video-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #fff;
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .video-section h3 {
  color: #333;
}

.video-container {
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #30363d;
  transition: border-color 0.3s;
}

:global(:root:not(.dark)) .video-container {
  border-color: #ccc;
}

.video-player {
  width: 100%;
  height: auto;
  display: block;
  max-height: 600px;
}

.visualization-section,
.cell-list-section {
  margin-bottom: 2rem;
}

.visualization-section h3,
.cell-list-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #fff;
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .visualization-section h3,
:global(:root:not(.dark)) .cell-list-section h3 {
  color: #333;
}

.visualization-placeholder {
  background: #161b22;
  border: 2px dashed #30363d;
  border-radius: 8px;
  padding: 4rem 2rem;
  text-align: center;
  color: #8b949e;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .visualization-placeholder {
  background: #fff;
  border-color: #ccc;
  color: #666;
}

.placeholder-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 1rem;
  color: #30363d;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .placeholder-icon {
  color: #ccc;
}

.visualization-placeholder p {
  margin: 0.5rem 0;
  font-size: 1rem;
  color: #c9d1d9;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .visualization-placeholder p {
  color: #333;
}

.placeholder-hint {
  font-size: 0.875rem !important;
  color: #6e7681 !important;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .placeholder-hint {
  color: #999 !important;
}

.table-placeholder {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  overflow: hidden;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .table-placeholder {
  background: #fff;
  border-color: #e0e0e0;
}

.cell-table {
  width: 100%;
  border-collapse: collapse;
}

.cell-table th {
  background: #21262d;
  padding: 0.75rem 1rem;
  text-align: left;
  font-size: 0.875rem;
  font-weight: 600;
  color: #8b949e;
  border-bottom: 1px solid #30363d;
  transition: background 0.3s, border-color 0.3s, color 0.3s;
}

:global(:root:not(.dark)) .cell-table th {
  background: #f5f5f5;
  border-bottom-color: #e0e0e0;
  color: #666;
}

.cell-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #21262d;
  color: #c9d1d9;
  font-size: 0.875rem;
  transition: border-color 0.3s, color 0.3s;
}

:global(:root:not(.dark)) .cell-table td {
  border-bottom-color: #e0e0e0;
  color: #333;
}

.cell-table tbody tr:hover {
  background: #0d1117;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .cell-table tbody tr:hover {
  background: #f5f5f5;
}

.btn-view {
  padding: 0.25rem 0.75rem;
  background: #21262d;
  color: #58a6ff;
  border: 1px solid #30363d;
  border-radius: 4px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

:global(:root:not(.dark)) .btn-view {
  background: #fff;
  color: #2196f3;
  border-color: #ccc;
}

.btn-view:hover {
  background: #1f6feb20;
  border-color: #58a6ff;
}

:global(:root:not(.dark)) .btn-view:hover {
  background: #e3f2fd;
  border-color: #2196f3;
}

/* 滚动条样式 */
.result-content::-webkit-scrollbar {
  width: 10px;
}

.result-content::-webkit-scrollbar-track {
  background: #0d1117;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .result-content::-webkit-scrollbar-track {
  background: #f5f5f5;
}

.result-content::-webkit-scrollbar-thumb {
  background: #30363d;
  border-radius: 5px;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .result-content::-webkit-scrollbar-thumb {
  background: #ccc;
}

.result-content::-webkit-scrollbar-thumb:hover {
  background: #484f58;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .result-content::-webkit-scrollbar-thumb:hover {
  background: #bbb;
}
</style>
