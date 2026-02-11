<script setup lang="ts">
import { useAnalysisStore } from '@/stores/analysisStore'
import type { AnalysisRecord } from '@/stores/analysisStore'
import CellDetailPanel from './CellDetailPanel.vue'

const props = defineProps<{
  record: AnalysisRecord
}>()

const store = useAnalysisStore()

// 处理查看细胞详情
function handleViewCell(cellId: string) {
  store.selectCell(cellId)
}

// 处理返回结果列表
function handleBackToList() {
  store.backToResultList()
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
        <p class="header-subtitle">任务ID: {{ record.task_id }}</p>
      </div>
      <div class="header-actions">
        <button class="btn-action">
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
          导出数据
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
              {{ ((record.result?.total_frames || 0) / 30).toFixed(1) }}s
            </p>
          </div>
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
}

.result-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #21262d;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #161b22;
}

.result-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #fff;
  margin: 0 0 0.25rem 0;
}

.header-subtitle {
  color: #8b949e;
  margin: 0;
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

.btn-action:hover {
  background: #30363d;
  border-color: #8b949e;
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
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 600;
  color: #fff;
  margin: 0;
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
}

.visualization-placeholder {
  background: #161b22;
  border: 2px dashed #30363d;
  border-radius: 8px;
  padding: 4rem 2rem;
  text-align: center;
  color: #8b949e;
}

.placeholder-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 1rem;
  color: #30363d;
}

.visualization-placeholder p {
  margin: 0.5rem 0;
  font-size: 1rem;
  color: #c9d1d9;
}

.placeholder-hint {
  font-size: 0.875rem !important;
  color: #6e7681 !important;
}

.table-placeholder {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  overflow: hidden;
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
}

.cell-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #21262d;
  color: #c9d1d9;
  font-size: 0.875rem;
}

.cell-table tbody tr:hover {
  background: #0d1117;
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

.btn-view:hover {
  background: #1f6feb20;
  border-color: #58a6ff;
}

/* 滚动条样式 */
.result-content::-webkit-scrollbar {
  width: 10px;
}

.result-content::-webkit-scrollbar-track {
  background: #0d1117;
}

.result-content::-webkit-scrollbar-thumb {
  background: #30363d;
  border-radius: 5px;
}

.result-content::-webkit-scrollbar-thumb:hover {
  background: #484f58;
}
</style>
