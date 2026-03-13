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

// 响应式的当前帧号（各自独立）
const currentFrameIndexA = ref(0)
const currentFrameIndexB = ref(0)

const isExporting = ref(false)
const exportError = ref<string | null>(null)

// ==================== 视频A的控制函数 ====================

// 计算视频A的帧率
function getVideoFpsA(): number {
  const totalFramesA = recordA.value?.result?.total_frames || 0
  const durationA = recordA.value?.result?.video_duration || 0
  if (durationA > 0 && totalFramesA > 0) {
    return totalFramesA / durationA
  }
  return 30
}

// 视频A下一帧
function handleNextFrameA() {
  const totalFrames = recordA.value?.result?.total_frames || 0
  if (currentFrameIndexA.value < totalFrames - 1) {
    currentFrameIndexA.value++
    const fps = getVideoFpsA()
    if (videoARef.value) {
      videoARef.value.currentTime = currentFrameIndexA.value / fps
      videoARef.value.pause()
    }
  }
}

// 视频A上一帧
function handlePrevFrameA() {
  if (currentFrameIndexA.value > 0) {
    currentFrameIndexA.value--
    const fps = getVideoFpsA()
    if (videoARef.value) {
      videoARef.value.currentTime = currentFrameIndexA.value / fps
      videoARef.value.pause()
    }
  }
}

// 视频A回到第一帧
function handleGoToFirstFrameA() {
  currentFrameIndexA.value = 0
  if (videoARef.value) {
    videoARef.value.currentTime = 0
    videoARef.value.pause()
  }
}

// 视频A跳转到指定帧
function handleJumpToFrameA(frameStr: string) {
  const frame = parseInt(frameStr, 10)
  const total = recordA.value?.result?.total_frames || 0

  if (!isNaN(frame) && frame >= 1 && frame <= total) {
    currentFrameIndexA.value = frame - 1
    const fps = getVideoFpsA()
    if (videoARef.value) {
      videoARef.value.currentTime = currentFrameIndexA.value / fps
      videoARef.value.pause()
    }
  }
}

// ==================== 视频B的控制函数 ====================

// 计算视频B的帧率
function getVideoFpsB(): number {
  const totalFramesB = recordB.value?.result?.total_frames || 0
  const durationB = recordB.value?.result?.video_duration || 0
  if (durationB > 0 && totalFramesB > 0) {
    return totalFramesB / durationB
  }
  return 30
}

// 视频B下一帧
function handleNextFrameB() {
  const totalFrames = recordB.value?.result?.total_frames || 0
  if (currentFrameIndexB.value < totalFrames - 1) {
    currentFrameIndexB.value++
    const fps = getVideoFpsB()
    if (videoBRef.value) {
      videoBRef.value.currentTime = currentFrameIndexB.value / fps
      videoBRef.value.pause()
    }
  }
}

// 视频B上一帧
function handlePrevFrameB() {
  if (currentFrameIndexB.value > 0) {
    currentFrameIndexB.value--
    const fps = getVideoFpsB()
    if (videoBRef.value) {
      videoBRef.value.currentTime = currentFrameIndexB.value / fps
      videoBRef.value.pause()
    }
  }
}

// 视频B回到第一帧
function handleGoToFirstFrameB() {
  currentFrameIndexB.value = 0
  if (videoBRef.value) {
    videoBRef.value.currentTime = 0
    videoBRef.value.pause()
  }
}

// 视频B跳转到指定帧
function handleJumpToFrameB(frameStr: string) {
  const frame = parseInt(frameStr, 10)
  const total = recordB.value?.result?.total_frames || 0

  if (!isNaN(frame) && frame >= 1 && frame <= total) {
    currentFrameIndexB.value = frame - 1
    const fps = getVideoFpsB()
    if (videoBRef.value) {
      videoBRef.value.currentTime = currentFrameIndexB.value / fps
      videoBRef.value.pause()
    }
  }
}

// ==================== 计算属性 ====================

// 计算属性：当前帧号（从1开始显示）
const currentFrameNumberA = computed(() => currentFrameIndexA.value + 1)
const currentFrameNumberB = computed(() => currentFrameIndexB.value + 1)

// 计算属性：总帧数
const totalFramesA = computed(() => recordA.value?.result?.total_frames || 0)
const totalFramesB = computed(() => recordB.value?.result?.total_frames || 0)

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
            <h3>标注视频 A - {{ recordA?.video_name || '未知' }}</h3>
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

            <!-- 视频A的帧控制栏 -->
            <div class="video-controls">
              <button class="btn-control" @click="handleGoToFirstFrameA">
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
              <button class="btn-control" @click="handlePrevFrameA">
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
                  :value="currentFrameNumberA"
                  :min="1"
                  :max="totalFramesA"
                  @input="handleJumpToFrameA(($event.target as HTMLInputElement).value)"
                  @blur="handleJumpToFrameA(($event.target as HTMLInputElement).value)"
                  @keyup.enter="handleJumpToFrameA(($event.target as HTMLInputElement).value)"
                  class="frame-input"
                />
                <span class="frame-separator">/</span>
                <span class="frame-total">{{ totalFramesA }}</span>
                <span class="frame-label">帧</span>
              </div>
              <button class="btn-control" @click="handleNextFrameA">
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

          <!-- 中间分隔线 -->
          <div class="video-divider"></div>

          <!-- 右侧：记录B的标注视频 -->
          <div class="video-panel video-panel-right">
            <h3>标注视频 B - {{ recordB?.video_name || '未知' }}</h3>
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

            <!-- 视频B的帧控制栏 -->
            <div class="video-controls">
              <button class="btn-control" @click="handleGoToFirstFrameB">
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
              <button class="btn-control" @click="handlePrevFrameB">
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
                  :value="currentFrameNumberB"
                  :min="1"
                  :max="totalFramesB"
                  @input="handleJumpToFrameB(($event.target as HTMLInputElement).value)"
                  @blur="handleJumpToFrameB(($event.target as HTMLInputElement).value)"
                  @keyup.enter="handleJumpToFrameB(($event.target as HTMLInputElement).value)"
                  class="frame-input"
                />
                <span class="frame-separator">/</span>
                <span class="frame-total">{{ totalFramesB }}</span>
                <span class="frame-label">帧</span>
              </div>
              <button class="btn-control" @click="handleNextFrameB">
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
        </div>
      </div>

      <!-- 图表部分（左右两块） -->
      <div class="chart-section">
        <h3>对比图表</h3>
        <div class="chart-wrapper">
          <!-- 左侧：记录A的图表 -->
          <div class="chart-panel chart-panel-left">
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
              <p>任务 A 图表区域</p>
              <p class="placeholder-hint">功能开发中...</p>
            </div>
          </div>

          <!-- 中间分隔线 -->
          <div class="chart-divider"></div>

          <!-- 右侧：记录B的图表 -->
          <div class="chart-panel chart-panel-right">
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
              <p>任务 B 图表区域</p>
              <p class="placeholder-hint">功能开发中...</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 细胞详细信息部分（左右两块） -->
      <div class="cell-detail-section">
        <h3>细胞详细信息</h3>
        <div class="cell-detail-wrapper">
          <!-- 左侧：记录A的细胞信息 -->
          <div class="cell-detail-panel cell-detail-panel-left">
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
              <p>任务 A 细胞详细信息</p>
              <p class="placeholder-hint">功能开发中...</p>
            </div>
          </div>

          <!-- 中间分隔线 -->
          <div class="cell-detail-divider"></div>

          <!-- 右侧：记录B的细胞信息 -->
          <div class="cell-detail-panel cell-detail-panel-right">
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
              <p>任务 B 细胞详细信息</p>
              <p class="placeholder-hint">功能开发中...</p>
            </div>
          </div>
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
  background: var(--bg-hover);
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
  gap: 1rem;
}

.video-panel h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
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
  background: var(--bg-hover);
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

.chart-section {
  margin-bottom: 2rem;
}

.chart-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .chart-section h3 {
  color: var(--text-primary-light);
}

.chart-wrapper {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 1rem;
  min-height: 500px;
}

.chart-panel {
  display: flex;
  flex-direction: column;
}

.chart-panel h4 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.75rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .chart-panel h4 {
  color: var(--text-primary-light);
}

.chart-divider {
  width: 1px;
  background: var(--border-color);
  align-self: stretch;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .chart-divider {
  background: var(--border-color-light);
}

.chart-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg-card);
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  color: var(--text-muted);
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .chart-placeholder {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
  color: var(--text-muted-light);
}

.cell-detail-section {
  margin-bottom: 2rem;
}

.cell-detail-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .cell-detail-section h3 {
  color: var(--text-primary-light);
}

.cell-detail-wrapper {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 1rem;
  min-height: 500px;
}

.cell-detail-panel {
  display: flex;
  flex-direction: column;
}

.cell-detail-panel h4 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.75rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .cell-detail-panel h4 {
  color: var(--text-primary-light);
}

.cell-detail-divider {
  width: 1px;
  background: var(--border-color);
  align-self: stretch;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .cell-detail-divider {
  background: var(--border-color-light);
}

.cell-detail-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg-card);
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  color: var(--text-muted);
  transition: background 0.3s, border-color 0.3s;
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

:global(:root:not(.dark)) .chart-placeholder > p,
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