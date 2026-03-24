<script setup lang="ts">
import '@/assets/styles/colors.css'
import { ref, computed, watch, onMounted } from 'vue'
import type { AnalysisRecord } from '@/stores/analysisStore'

const props = defineProps<{
  record: AnalysisRecord
}>()

// 响应式的当前帧号
const currentFrameIndex = ref(0)

// 图片加载状态
const isImageLoading = ref(false)

// 当前显示的图片 URL
const displayedImageUrl = ref('')

// 下一帧
function handleNextFrame() {
  const totalFrames = props.record.result?.total_frames ?? 0
  if (currentFrameIndex.value < totalFrames - 1) {
    currentFrameIndex.value++
    loadImage()
  }
}

// 上一帧
function handlePrevFrame() {
  if (currentFrameIndex.value > 0) {
    currentFrameIndex.value--
    loadImage()
  }
}

// 回到第一帧
function handleGoToFirstFrame() {
  currentFrameIndex.value = 0
  loadImage()
}

// 跳转到指定帧
function handleJumpToFrame(frameStr: string) {
  const frame = parseInt(frameStr, 10)
  const total = props.record.result?.total_frames ?? 0

  if (!isNaN(frame) && frame >= 1 && frame <= total) {
    currentFrameIndex.value = frame - 1
    loadImage()
  }
}

// 加载图片
function loadImage() {
  if (!props.record?.task_id) {
    return
  }

  // 添加时间戳参数避免浏览器缓存
  const timestamp = Date.now()
  const newUrl = `/api/frame/${props.record.task_id}/${currentFrameIndex.value}/?t=${timestamp}`
  isImageLoading.value = true

  const img = new Image()
  img.onload = () => {
    displayedImageUrl.value = newUrl
    isImageLoading.value = false
  }
  img.onerror = () => {
    console.error('帧图片加载失败:', newUrl)
    isImageLoading.value = false
  }
  img.src = newUrl
}

// 检查并加载图片
function checkAndLoadImage() {
  if ((props.record?.result?.total_frames ?? 0) > 0 && props.record.task_id) {
    currentFrameIndex.value = 0
    loadImage()
  }
}

// 监听 record 变化，初始化加载第一帧
watch(() => props.record, (newRecord) => {
  checkAndLoadImage()
}, { deep: true })

// 组件挂载时加载图片
onMounted(() => {
  checkAndLoadImage()
})

// 计算属性：当前帧号（从1开始显示）
const currentFrameNumber = computed(() => currentFrameIndex.value + 1)

// 计算属性：总帧数
const totalFrames = computed(() => props.record.result?.total_frames ?? 0)
</script>

<template>
  <div class="frame-analysis">
    <div class="detail-content">
      <!-- 左侧：帧图片显示 -->
      <div class="detail-video-section">
        <h3>逐帧查看</h3>
        <div class="detail-video-wrapper">
          <div class="detail-video-container">
            <img
              v-if="record.result && totalFrames > 0 && displayedImageUrl"
              :src="displayedImageUrl"
              class="detail-video-player"
              alt="当前帧"
              :class="{ 'loading': isImageLoading }"
            />
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
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                ></path>
              </svg>
              <p class="placeholder-text">暂无帧数据</p>
            </div>
          </div>

          <!-- 帧控制栏 -->
          <div v-if="record.result && totalFrames > 0" class="detail-video-controls">
            <button class="detail-btn-control" @click="handleGoToFirstFrame">
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
            <button class="detail-btn-control" @click="handlePrevFrame">
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
            <button class="detail-btn-control" @click="handleNextFrame">
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
</template>

<style scoped>
.frame-analysis {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
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
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-video-section h3 {
  color: var(--text-primary-light);
}

.detail-video-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-height: 0;
}

.detail-video-container {
  background: var(--bg-main);
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.3s;
  align-self: flex-start;
  display: flex;
  align-items: center;
  justify-content: center;
}

:global(:root:not(.dark)) .detail-video-container {
  background: var(--bg-main-light);
  border-color: var(--border-color-light);
}

.detail-video-player {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: contain;
  transition: opacity 0.15s ease-in-out;
}

.detail-video-player.loading {
  opacity: 0.7;
}

.detail-video-controls {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .detail-video-controls {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

.detail-btn-control {
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

:global(:root:not(.dark)) .detail-btn-control {
  background: var(--bg-card-light);
  color: var(--text-primary-light);
  border-color: var(--border-color-light);
}

.detail-btn-control:hover {
  background: var(--bg-hover);
  border-color: var(--text-muted);
}

:global(:root:not(.dark)) .detail-btn-control:hover {
  background: var(--bg-main-light);
  border-color: var(--text-disabled-light);
}

.detail-btn-control svg {
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

.detail-video-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--alpha-toast);
  transition: background 0.3s;
}

:global(:root:not(.dark)) .detail-video-placeholder {
  background: var(--alpha-toast-light);
}

.detail-video-placeholder .placeholder-icon {
  width: 64px;
  height: 64px;
  color: var(--text-muted);
  margin-bottom: 1rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-video-placeholder .placeholder-icon {
  color: var(--text-disabled-light);
}

.detail-video-placeholder .placeholder-text {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-video-placeholder .placeholder-text {
  color: var(--text-primary-light);
}

.detail-info-section {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.detail-info-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-info-section h3 {
  color: var(--text-primary-light);
}

.detail-divider {
  width: 1px;
  background: var(--border-color);
  height: 100%;
  align-self: stretch;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .detail-divider {
  background: var(--border-color-light);
}

.detail-placeholder {
  text-align: center;
  padding: 4rem 2rem;
  max-width: 500px;
}

.detail-placeholder .placeholder-icon {
  width: 80px;
  height: 80px;
  color: var(--border-color);
  margin: 0 auto 1.5rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-placeholder .placeholder-icon {
  color: var(--border-color-light);
}

.detail-placeholder > p {
  font-size: 1rem;
  color: var(--text-muted);
  margin: 0 0 0.5rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-placeholder > p {
  color: var(--text-muted-light);
}

.detail-placeholder .placeholder-hint {
  font-size: 0.875rem;
  color: var(--text-disabled) !important;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-placeholder .placeholder-hint {
  color: var(--text-disabled-light) !important;
}
</style>