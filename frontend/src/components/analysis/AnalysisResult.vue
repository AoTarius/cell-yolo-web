<script setup lang="ts">
import { ref, watch } from 'vue'
import { useAnalysisStore } from '@/stores/analysisStore'
import type { AnalysisRecord } from '@/stores/analysisStore'
import { useAnalysisApi } from '@/composables/useAnalysisApi'
import { useToast } from '@/composables/useToast'
import CellDetailPanel from './CellDetailPanel.vue'
import ResultHeader from './ResultHeader.vue'
import VideoPlayer from './VideoPlayer.vue'
import CellPopulationChart from './CellPopulationChart.vue'
import CellDetailList from './CellDetailList.vue'

const props = defineProps<{
  record: AnalysisRecord
}>()

const store = useAnalysisStore()
const api = useAnalysisApi()
const { showToast } = useToast()

// 视图模式：整体/细化
const viewMode = ref<'overall' | 'detail'>('overall')

// 监听 record 变化，切换记录时重置为整体模式
watch(() => props.record, () => {
  viewMode.value = 'overall'
})

// 细化视图视频播放器引用
const detailVideoRef = ref<HTMLVideoElement | null>(null)

const isExporting = ref(false)
const exportError = ref<string | null>(null)

// 计算视频帧率
function getVideoFps(): number {
  const totalFrames = props.record.result?.total_frames || 0
  const duration = props.record.result?.video_duration || 0
  if (duration > 0 && totalFrames > 0) {
    return totalFrames / duration
  }
  return 30 // 默认帧率
}

// 播放视频
function handlePlay() {
  if (detailVideoRef.value) {
    detailVideoRef.value.play()
  }
}

// 暂停视频
function handlePause() {
  if (detailVideoRef.value) {
    detailVideoRef.value.pause()
  }
}

// 后退一帧
function handleBackwardFrame() {
  const fps = getVideoFps()
  const frameDuration = 1 / fps
  if (detailVideoRef.value) {
    detailVideoRef.value.currentTime = Math.max(0, detailVideoRef.value.currentTime - frameDuration)
    detailVideoRef.value.pause()
  }
}

// 前进一帧
function handleForwardFrame() {
  const fps = getVideoFps()
  const frameDuration = 1 / fps
  if (detailVideoRef.value) {
    detailVideoRef.value.currentTime += frameDuration
    detailVideoRef.value.pause()
  }
}

// 回到开头
function handleRewindToStart() {
  if (detailVideoRef.value) {
    detailVideoRef.value.currentTime = 0
    detailVideoRef.value.pause()
  }
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
    showToast(`数据已成功导出为 ${format.toUpperCase()} 格式`, 'success')
  } catch (error: any) {
    exportError.value = error.message || '导出失败'
    console.error('Export error:', error)
    showToast(error.message || '导出失败', 'error')
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
    showToast('标注视频下载成功！', 'success')
  } catch (error: any) {
    exportError.value = error.message || '下载失败'
    console.error('Download error:', error)
    showToast(error.message || '下载失败', 'error')
  } finally {
    isExporting.value = false
  }
}

// 处理视频错误
function handleVideoError() {
  exportError.value = '视频加载失败'
}

// 处理视图模式切换
function handleViewModeChange(mode: 'overall' | 'detail') {
  viewMode.value = mode
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
    <!-- 结果头部 -->
    <ResultHeader
      :record="record"
      :is-exporting="isExporting"
      :viewMode="viewMode"
      @export="handleExport"
      @download="handleDownloadVideo"
      @viewModeChange="handleViewModeChange"
    />

    <div class="result-content">
      <!-- 整体模式：显示统计卡片、视频播放器、图表、细胞列表 -->
      <div v-if="viewMode === 'overall'">
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

        <!-- 视频播放器 -->
        <VideoPlayer
          :record="record"
          @video-error="handleVideoError"
        />

        <!-- 细胞群体图表 -->
        <CellPopulationChart />

        <!-- 细胞详细信息 -->
        <CellDetailList />
      </div>

      <!-- 细化模式：显示详细分析界面 -->
      <div v-else-if="viewMode === 'detail'" class="detail-view">
        <div class="detail-content">
          <!-- 左侧：标注视频播放器 -->
          <div class="detail-video-section">
            <h3>标注视频</h3>
            <div class="detail-video-wrapper">
              <div class="detail-video-container">
                <video
                  ref="detailVideoRef"
                  v-if="record.result?.output_video_path"
                  :src="`/api/video/${record.task_id}/`"
                  controls
                  class="detail-video-player"
                >
                  您的浏览器不支持视频播放
                </video>
                <div v-else class="detail-video-placeholder">
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
                      d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                    ></path>
                  </svg>
                  <p class="placeholder-text">暂无标注视频</p>
                </div>
              </div>

              <!-- 视频功能栏 -->
              <div v-if="record.result?.output_video_path" class="detail-video-controls">
                <button class="detail-btn-control" @click="handlePlay">
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
                      d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                    ></path>
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    ></path>
                  </svg>
                  播放
                </button>
                <button class="detail-btn-control" @click="handlePause">
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
                      d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    ></path>
                  </svg>
                  暂停
                </button>
                <button class="detail-btn-control" @click="handleBackwardFrame">
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
                      d="M12.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0019 16V8a1 1 0 00-1.6-.8l-5.333 4zM4.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0011 16V8a1 1 0 00-1.6-.8l-5.334 4z"
                    ></path>
                  </svg>
                  后退一帧
                </button>
                <button class="detail-btn-control" @click="handleForwardFrame">
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
                      d="M11.933 12.8a1 1 0 000-1.6L6.6 7.2A1 1 0 005 8v8a1 1 0 001.6.8l5.333-4zM19.933 12.8a1 1 0 000-1.6l-5.333-4A1 1 0 0013 8v8a1 1 0 001.6.8l5.333-4z"
                    ></path>
                  </svg>
                  前进一帧
                </button>
                <button class="detail-btn-control" @click="handleRewindToStart">
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
                      d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"
                    ></path>
                  </svg>
                  回到开头
                </button>
              </div>
            </div>
          </div>

          <!-- 竖向分隔线 -->
          <div class="detail-divider"></div>

          <!-- 右侧：逐帧分析 -->
          <div class="detail-info-section">
            <h3>逐帧分析</h3>
            <div class="detail-placeholder">
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
                  d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"
                ></path>
              </svg>
              <p>此区域用于展示详细的细胞分析数据</p>
              <p class="placeholder-hint">功能开发中...</p>
            </div>
          </div>
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

:global(:root:not(.dark)) .visualization-section h3 {
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

/* 细化视图样式 */
.detail-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 1rem;
  padding: 2rem;
  overflow: hidden;
}

.detail-video-section {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.detail-video-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #fff;
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-video-section h3 {
  color: #333;
}

.detail-video-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-height: 0;
}

.detail-video-container {
  flex: 1;
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.3s;
  min-height: 300px;
}

:global(:root:not(.dark)) .detail-video-container {
  background: #f5f5f5;
  border-color: #ccc;
}

.detail-video-player {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.detail-video-controls {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .detail-video-controls {
  background: #fff;
  border-color: #e0e0e0;
}

.detail-btn-control {
  flex: 1;
  padding: 0.5rem 0.75rem;
  background: #21262d;
  color: #c9d1d9;
  border: 1px solid #30363d;
  border-radius: 4px;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  white-space: nowrap;
}

:global(:root:not(.dark)) .detail-btn-control {
  background: #fff;
  color: #333;
  border-color: #ccc;
}

.detail-btn-control:hover {
  background: #30363d;
  border-color: #8b949e;
}

:global(:root:not(.dark)) .detail-btn-control:hover {
  background: #f5f5f5;
  border-color: #999;
}

.detail-btn-control svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.detail-video-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(13, 17, 23, 0.95);
  transition: background 0.3s;
}

:global(:root:not(.dark)) .detail-video-placeholder {
  background: rgba(245, 245, 245, 0.95);
}

.detail-video-placeholder .placeholder-icon {
  width: 64px;
  height: 64px;
  color: #8b949e;
  margin-bottom: 1rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-video-placeholder .placeholder-icon {
  color: #999;
}

.detail-video-placeholder .placeholder-text {
  font-size: 1rem;
  color: #c9d1d9;
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-video-placeholder .placeholder-text {
  color: #333;
}

.detail-info-section {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.detail-info-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #fff;
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-info-section h3 {
  color: #333;
}

.detail-divider {
  width: 1px;
  background: #30363d;
  height: 100%;
  align-self: stretch;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .detail-divider {
  background: #e0e0e0;
}

.detail-placeholder {
  text-align: center;
  padding: 4rem 2rem;
  max-width: 500px;
}

.detail-placeholder .placeholder-icon {
  width: 80px;
  height: 80px;
  color: #30363d;
  margin: 0 auto 1.5rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-placeholder .placeholder-icon {
  color: #ccc;
}

.detail-placeholder h3 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #fff;
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-placeholder h3 {
  color: #333;
}

.detail-placeholder > p {
  font-size: 1rem;
  color: #8b949e;
  margin: 0 0 0.5rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-placeholder > p {
  color: #666;
}

.detail-placeholder .placeholder-hint {
  font-size: 0.875rem;
  color: #6e7681 !important;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-placeholder .placeholder-hint {
  color: #999 !important;
}
</style>
