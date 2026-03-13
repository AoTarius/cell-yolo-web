<script setup lang="ts">
import '@/assets/styles/colors.css'
import { ref, computed, onMounted } from 'vue'
import { useAnalysisStore, type AnalysisRecord } from '@/stores/analysisStore'
import { useAnalysisApi } from '@/composables/useAnalysisApi'
import { useToast } from '@/composables/useToast'
import { useRouter } from 'vue-router'

const store = useAnalysisStore()
const api = useAnalysisApi()
const { showToast } = useToast()
const router = useRouter()

// 从store中获取对比记录
const recordA = computed(() => store.compareRecords[0])
const recordB = computed(() => store.compareRecords[1])

// 检查是否有有效的对比记录
const hasValidRecords = computed(() => recordA.value && recordB.value)

// 组件挂载时，如果没有有效记录，返回对比页面
onMounted(() => {
  if (!hasValidRecords.value) {
    router.push({ name: 'compare' })
  }
})

// 视频播放器引用
const videoARef = ref<HTMLVideoElement | null>(null)
const videoBRef = ref<HTMLVideoElement | null>(null)

// 响应式的当前帧号
const currentFrameIndex = ref(0)

const isExporting = ref(false)
const exportError = ref<string | null>(null)

// 计算视频帧率（使用两个记录的较小值）
function getVideoFps(): number {
  const totalFramesA = recordA.value?.result?.total_frames || 0
  const durationA = recordA.value?.result?.video_duration || 0
  const totalFramesB = recordB.value?.result?.total_frames || 0
  const durationB = recordB.value?.result?.video_duration || 0

  const fpsA = durationA > 0 && totalFramesA > 0 ? totalFramesA / durationA : 30
  const fpsB = durationB > 0 && totalFramesB > 0 ? totalFramesB / durationB : 30

  return Math.min(fpsA, fpsB)
}

// 下一帧
function handleNextFrame() {
  const totalFrames = Math.min(
    recordA.value?.result?.total_frames || 0,
    recordB.value?.result?.total_frames || 0
  )
  if (currentFrameIndex.value < totalFrames - 1) {
    currentFrameIndex.value++
    const fps = getVideoFps()
    if (videoARef.value) {
      videoARef.value.currentTime = currentFrameIndex.value / fps
      videoARef.value.pause()
    }
    if (videoBRef.value) {
      videoBRef.value.currentTime = currentFrameIndex.value / fps
      videoBRef.value.pause()
    }
  }
}

// 上一帧
function handlePrevFrame() {
  if (currentFrameIndex.value > 0) {
    currentFrameIndex.value--
    const fps = getVideoFps()
    if (videoARef.value) {
      videoARef.value.currentTime = currentFrameIndex.value / fps
      videoARef.value.pause()
    }
    if (videoBRef.value) {
      videoBRef.value.currentTime = currentFrameIndex.value / fps
      videoBRef.value.pause()
    }
  }
}

// 回到第一帧
function handleGoToFirstFrame() {
  currentFrameIndex.value = 0
  if (videoARef.value) {
    videoARef.value.currentTime = 0
    videoARef.value.pause()
  }
  if (videoBRef.value) {
    videoBRef.value.currentTime = 0
    videoBRef.value.pause()
  }
}

// 跳转到指定帧
function handleJumpToFrame(frameStr: string) {
  const frame = parseInt(frameStr, 10)
  const total = Math.min(
    recordA.value?.result?.total_frames || 0,
    recordB.value?.result?.total_frames || 0
  )

  if (!isNaN(frame) && frame >= 1 && frame <= total) {
    currentFrameIndex.value = frame - 1
    const fps = getVideoFps()
    if (videoARef.value) {
      videoARef.value.currentTime = currentFrameIndex.value / fps
      videoARef.value.pause()
    }
    if (videoBRef.value) {
      videoBRef.value.currentTime = currentFrameIndex.value / fps
      videoBRef.value.pause()
    }
  }
}

// 计算属性：当前帧号（从1开始显示）
const currentFrameNumber = computed(() => currentFrameIndex.value + 1)

// 计算属性：总帧数
const totalFrames = computed(() =>
  Math.min(
    recordA.value?.result?.total_frames || 0,
    recordB.value?.result?.total_frames || 0
  )
)

// 处理返回对比页面
function handleBackToCompare() {
  store.backToCompareList(router)
}

// 处理视频错误
function handleVideoError() {
  exportError.value = '视频加载失败'
}
</script>

<template>
  <div class="compare-result-panel">
    <!-- 结果头部 -->
    <div class="result-header">
      <div class="header-content">
        <button class="btn-back" @click="handleBackToCompare">
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
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            ></path>
          </svg>
          返回对比
        </button>
        <div class="header-title">
          <h2>对比分析结果</h2>
          <p class="header-subtitle">
            {{ recordA?.video_name || '未知' }} vs {{ recordB?.video_name || '未知' }}
          </p>
        </div>
      </div>
    </div>

    <div class="result-content">
      <!-- 视频对比区域 -->
      <div class="video-compare-section">
        <div class="video-compare-wrapper">
          <!-- 左侧：记录A的标注视频 -->
          <div class="video-panel video-panel-left">
            <h3>标注视频 A</h3>
            <div class="video-container">
              <div class="video-wrapper">
                <video
                  ref="videoARef"
                  v-if="recordA?.result?.output_video_path"
                  :src="`/api/video/${recordA.task_id}/`"
                  class="video-player"
                  @error="handleVideoError"
                >
                  您的浏览器不支持视频播放
                </video>
                <div v-else class="video-placeholder">
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
            </div>
          </div>

          <!-- 中间分隔线 -->
          <div class="video-divider"></div>

          <!-- 右侧：记录B的标注视频 -->
          <div class="video-panel video-panel-right">
            <h3>标注视频 B</h3>
            <div class="video-container">
              <div class="video-wrapper">
                <video
                  ref="videoBRef"
                  v-if="recordB?.result?.output_video_path"
                  :src="`/api/video/${recordB.task_id}/`"
                  class="video-player"
                  @error="handleVideoError"
                >
                  您的浏览器不支持视频播放
                </video>
                <div v-else class="video-placeholder">
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
            </div>
          </div>
        </div>

        <!-- 帧控制栏 -->
        <div class="video-controls">
          <button class="btn-control" @click="handleGoToFirstFrame">
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
                d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
              ></path>
            </svg>
            第一帧
          </button>
          <button class="btn-control" @click="handlePrevFrame">
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
                d="M15 19l-7-7 7-7"
              ></path>
            </svg>
            上一帧
          </button>
          <div class="frame-counter">
            <input
              type="number"
              :value="currentFrameNumber"
              :min="1"
              :max="totalFrames"
              @input="handleJumpToFrame(($event.target as HTMLInputElement).value)"
              @blur="handleJumpToFrame(($event.target as HTMLInputElement).value)"
              @keyup.enter="handleJumpToFrame(($event.target as HTMLInputElement).value)"
              class="frame-input"
            />
            <span class="frame-separator">/</span>
            <span class="frame-total">{{ totalFrames }}</span>
            <span class="frame-label">帧</span>
          </div>
          <button class="btn-control" @click="handleNextFrame">
            下一帧
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
                d="M9 5l7 7-7 7"
              ></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- 图表部分（仅标题） -->
      <div class="chart-section">
        <h3>对比图表</h3>
        <div class="chart-placeholder">
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
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            ></path>
          </svg>
          <p>对比图表区域</p>
          <p class="placeholder-hint">功能开发中...</p>
        </div>
      </div>

      <!-- 细胞详细信息部分（仅标题） -->
      <div class="cell-detail-section">
        <h3>细胞详细信息</h3>
        <div class="cell-detail-placeholder">
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
          <p>细胞详细信息区域</p>
          <p class="placeholder-hint">功能开发中...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.compare-result-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-main);
  overflow: hidden;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .compare-result-panel {
  background: var(--bg-main-light);
}

.result-header {
  padding: 1.5rem 2rem;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .result-header {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  max-width: 1600px;
  margin: 0 auto;
}

.btn-back {
  padding: 0.5rem 1rem;
  background: var(--bg-input);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  white-space: nowrap;
}

:global(:root:not(.dark)) .btn-back {
  background: var(--bg-card-light);
  color: var(--text-primary-light);
  border-color: var(--border-color-light);
}

.btn-back:hover {
  background: var(--border-color);
  border-color: var(--text-muted);
}

:global(:root:not(.dark)) .btn-back:hover {
  background: var(--bg-main-light);
  border-color: var(--text-disabled-light);
}

.btn-back svg {
  width: 16px;
  height: 16px;
}

.header-title {
  flex: 1;
}

.header-title h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.25rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .header-title h2 {
  color: var(--text-primary-light);
}

.header-subtitle {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .header-subtitle {
  color: var(--text-muted-light);
}

.result-content {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.video-compare-section {
  margin-bottom: 2rem;
}

.video-compare-wrapper {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.video-panel {
  display: flex;
  flex-direction: column;
}

.video-panel h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.75rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .video-panel h3 {
  color: var(--text-primary-light);
}

.video-container {
  flex: 1;
  background: var(--bg-main);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.3s;
  min-height: 400px;
}

:global(:root:not(.dark)) .video-container {
  background: var(--bg-main-light);
  border-color: var(--border-color-light);
}

.video-wrapper {
  width: 100%;
  height: 100%;
}

.video-player {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.video-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--alpha-toast);
  transition: background 0.3s;
}

:global(:root:not(.dark)) .video-placeholder {
  background: var(--alpha-toast-light);
}

.video-placeholder .placeholder-icon {
  width: 64px;
  height: 64px;
  color: var(--text-muted);
  margin-bottom: 1rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .video-placeholder .placeholder-icon {
  color: var(--text-disabled-light);
}

.video-placeholder .placeholder-text {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .video-placeholder .placeholder-text {
  color: var(--text-primary-light);
}

.video-divider {
  width: 1px;
  background: var(--border-color);
  align-self: stretch;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .video-divider {
  background: var(--border-color-light);
}

.video-controls {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .video-controls {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

.btn-control {
  flex: 1;
  padding: 0.5rem 0.75rem;
  background: var(--bg-input);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
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

:global(:root:not(.dark)) .btn-control {
  background: var(--bg-card-light);
  color: var(--text-primary-light);
  border-color: var(--border-color-light);
}

.btn-control:hover {
  background: var(--border-color);
  border-color: var(--text-muted);
}

:global(:root:not(.dark)) .btn-control:hover {
  background: var(--bg-main-light);
  border-color: var(--text-disabled-light);
}

.btn-control svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.frame-counter {
  flex: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .frame-counter {
  color: var(--text-primary-light);
}

.frame-input {
  width: 50px;
  padding: 0.25rem 0.375rem;
  background: var(--bg-input);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
  text-align: center;
  transition: all 0.2s;
  outline: none;
}

:global(:root:not(.dark)) .frame-input {
  background: var(--bg-card-light);
  color: var(--text-primary-light);
  border-color: var(--border-color-light);
}

.frame-input:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px var(--alpha-focus-ring);
}

:global(:root:not(.dark)) .frame-input:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px var(--alpha-focus-ring);
}

.frame-input:hover:not(:focus) {
  border-color: var(--border-hover);
}

:global(:root:not(.dark)) .frame-input:hover:not(:focus) {
  border-color: var(--border-hover-light);
}

.frame-separator {
  color: var(--text-disabled);
  font-weight: 400;
}

:global(:root:not(.dark)) .frame-separator {
  color: var(--text-muted-light);
}

.frame-total {
  color: var(--text-muted);
  font-weight: 400;
}

:global(:root:not(.dark)) .frame-total {
  color: var(--text-muted-light);
}

.frame-label {
  color: var(--text-disabled);
  font-weight: 400;
}

:global(:root:not(.dark)) .frame-label {
  color: var(--text-muted-light);
}

.chart-section,
.cell-detail-section {
  margin-bottom: 2rem;
}

.chart-section h3,
.cell-detail-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .chart-section h3 {
  color: var(--text-primary-light);
}

:global(:root:not(.dark)) .cell-detail-section h3 {
  color: var(--text-primary-light);
}

.chart-placeholder,
.cell-detail-placeholder {
  background: var(--bg-card);
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  padding: 4rem 2rem;
  text-align: center;
  color: var(--text-muted);
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .chart-placeholder {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
  color: var(--text-muted-light);
}

:global(:root:not(.dark)) .cell-detail-placeholder {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
  color: var(--text-muted-light);
}

.placeholder-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 1rem;
  color: var(--border-color);
  transition: color 0.3s;
}

:global(:root:not(.dark)) .placeholder-icon {
  color: var(--border-color-light);
}

.chart-placeholder > p,
.cell-detail-placeholder > p {
  margin: 0.5rem 0;
  font-size: 1rem;
  color: var(--text-secondary);
  transition: color 0.3s;
}

:global(:root:not(.dark)) .chart-placeholder > p {
  color: var(--text-primary-light);
}

:global(:root:not(.dark)) .cell-detail-placeholder > p {
  color: var(--text-primary-light);
}

.placeholder-hint {
  font-size: 0.875rem !important;
  color: var(--text-disabled) !important;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .placeholder-hint {
  color: var(--text-disabled-light) !important;
}

/* 滚动条样式 */
.result-content::-webkit-scrollbar {
  width: 10px;
}

.result-content::-webkit-scrollbar-track {
  background: var(--bg-main);
  transition: background 0.3s;
}

:global(:root:not(.dark)) .result-content::-webkit-scrollbar-track {
  background: var(--bg-main-light);
}

.result-content::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 5px;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .result-content::-webkit-scrollbar-thumb {
  background: var(--border-color-light);
}

.result-content::-webkit-scrollbar-thumb:hover {
  background: var(--border-hover);
  transition: background 0.3s;
}

:global(:root:not(.dark)) .result-content::-webkit-scrollbar-thumb:hover {
  background: var(--border-hover-light);
}
</style>