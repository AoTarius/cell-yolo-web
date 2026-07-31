<script setup lang="ts">
import '@/assets/styles/colors.css'
import { ref, watch } from 'vue'
import type { AnalysisRecord } from '@/stores/analysisStore'

const props = defineProps<{
  record: AnalysisRecord
}>()

const emit = defineEmits<{
  videoError: []
}>()

// 视频播放器引用
const originalVideoRef = ref<HTMLVideoElement | null>(null)
const annotatedVideoRef = ref<HTMLVideoElement | null>(null)

// 视频加载错误状态
const originalVideoError = ref(false)
const annotatedVideoError = ref(false)

// 视频布局模式：'side-by-side' (并排) 或 'stacked' (上下)
const videoLayoutMode = ref<'side-by-side' | 'stacked'>('side-by-side')

// 播放速率选项
const playbackRates = [0.25, 0.5, 1, 2]
const currentPlaybackRate = ref(1)
const showRateMenu = ref(false)

function getNativePlaybackRate(displayRate: number): number {
  if (displayRate === 2) return 1
  if (displayRate === 1) return 0.5
  if (displayRate === 0.5) return 0.25
  if (displayRate === 0.25) return 0.125
  return 1
}

// 监听record.task_id变化，切换记录卡时重置播放速率
watch(() => props.record.task_id, () => {
  currentPlaybackRate.value = 1
  showRateMenu.value = false
  const nativeRate = getNativePlaybackRate(1)
  if (originalVideoRef.value) {
    originalVideoRef.value.playbackRate = nativeRate
  }
  if (annotatedVideoRef.value) {
    annotatedVideoRef.value.playbackRate = nativeRate
  }
})

// 切换视频布局模式
function toggleVideoLayout() {
  videoLayoutMode.value = videoLayoutMode.value === 'side-by-side' ? 'stacked' : 'side-by-side'
}

// 切换速率菜单显示
function toggleRateMenu() {
  showRateMenu.value = !showRateMenu.value
}

// 设置播放速率
function setPlaybackRate(rate: number) {
  currentPlaybackRate.value = rate
  const nativeRate = getNativePlaybackRate(rate)
  if (originalVideoRef.value) {
    originalVideoRef.value.playbackRate = nativeRate
  }
  if (annotatedVideoRef.value) {
    annotatedVideoRef.value.playbackRate = nativeRate
  }
  showRateMenu.value = false
}

// 同时播放功能
function handlePlayBoth() {
  if (originalVideoRef.value && originalVideoRef.value.paused) {
    originalVideoRef.value.play()
  }
  if (annotatedVideoRef.value && annotatedVideoRef.value.paused) {
    annotatedVideoRef.value.play()
  }
}

// 同时暂停功能
function handlePauseBoth() {
  if (originalVideoRef.value && !originalVideoRef.value.paused) {
    originalVideoRef.value.pause()
  }
  if (annotatedVideoRef.value && !annotatedVideoRef.value.paused) {
    annotatedVideoRef.value.pause()
  }
}

// 回到开始并暂停功能
function handleRewindBoth() {
  if (originalVideoRef.value) {
    originalVideoRef.value.currentTime = 0
    originalVideoRef.value.pause()
  }
  if (annotatedVideoRef.value) {
    annotatedVideoRef.value.currentTime = 0
    annotatedVideoRef.value.pause()
  }
}

/*
 * 前进/后退一帧功能已移除。
 *
 * 原因：HTML5 video.currentTime 的帧级跳转仅在 Safari (macOS) 上可靠，
 * Chrome / Firefox / Edge 会吸附到最近的关键帧 (keyframe)，无法精确逐帧定位。
 *
 * 替代方案：使用"细化视图"中的 FrameAnalysis 组件——
 * 它通过后端 /api/frame/ 接口加载静态帧图片，全平台通用。
 */

// 获取视频 URL
function getVideoUrl(taskId: string): string {
  return `/api/video/${taskId}/`
}

// 获取原始视频 URL
function getOriginalVideoUrl(taskId: string): string {
  return `/api/original-video/${taskId}/`
}

// 处理视频错误
function handleVideoError(event: Event) {
  const target = event.target as HTMLVideoElement
  if (target === originalVideoRef.value) {
    originalVideoError.value = true
  } else if (target === annotatedVideoRef.value) {
    annotatedVideoError.value = true
  }
  emit('videoError')
}
</script>

<template>
  <div class="video-comparison">
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

    <!-- 视频播放器区域（支持并排和上下布局） -->
    <div
      v-if="record.video_path || record.result?.output_video_path"
      class="videos-wrapper"
      :class="`videos-wrapper-${videoLayoutMode}`"
    >
      <!-- 原始视频播放器 -->
      <div v-if="record.video_path" class="video-section video-section-half">
        <h3>原始视频</h3>
        <div class="video-container">
          <video
            ref="originalVideoRef"
            :src="getOriginalVideoUrl(record.task_id)"
            controls
            class="video-player"
            @error="handleVideoError"
          >
            您的浏览器不支持视频播放
          </video>
          <div v-if="originalVideoError" class="video-placeholder">
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
            <p class="placeholder-text">样例视频（演示数据）</p>
            <p class="placeholder-hint">此为设计稿演示，无真实视频文件</p>
          </div>
        </div>
      </div>

      <!-- 分隔线 -->
      <div v-if="record.video_path && record.result?.output_video_path" class="video-divider"></div>

      <!-- 标注视频播放器 -->
      <div v-if="record.result?.output_video_path" class="video-section video-section-half">
        <h3>标注视频</h3>
        <div class="video-container">
          <video
            ref="annotatedVideoRef"
            :src="getVideoUrl(record.task_id)"
            controls
            class="video-player"
            @error="handleVideoError"
          >
            您的浏览器不支持视频播放
          </video>
          <div v-if="annotatedVideoError" class="video-placeholder">
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
            <p class="placeholder-text">样例视频（演示数据）</p>
            <p class="placeholder-hint">此为设计稿演示，无真实视频文件</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 视频功能栏 -->
    <div v-if="record.video_path || record.result?.output_video_path" class="video-controls-bar">
      <button class="btn-control btn-control-primary" @click="toggleVideoLayout">
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
            d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
          ></path>
        </svg>
        {{ videoLayoutMode === 'side-by-side' ? '分行显示' : '并排显示' }}
      </button>
      <button class="btn-control" @click="handlePlayBoth">
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
        同时播放
      </button>
      <button class="btn-control" @click="handlePauseBoth">
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
        同时暂停
      </button>
      <!--
        前进/后退一帧按钮已移除。
        原因：HTML5 video.currentTime 的帧级跳转仅在 Safari 上可靠，
        Chrome/Firefox/Edge 会吸附到最近的关键帧，无法精确逐帧。
        替代方案：使用"细化视图"中的 FrameAnalysis 组件——它通过
        后端 /api/frame/ 接口加载静态帧图片，全平台通用。
      -->
      <!--
      <button class="btn-control" @click="handleBackwardFrame">
        ...
        后退一帧
      </button>
      <button class="btn-control" @click="handleForwardFrame">
        ...
        前进一帧
      </button>
      -->
      <button class="btn-control" @click="handleRewindBoth">
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
        回到开始并暂停
      </button>
      <div class="rate-control-wrapper">
        <button class="btn-control" @click="toggleRateMenu">
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
          调整速率: {{ currentPlaybackRate }}x
          <svg
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
            class="dropdown-arrow"
            :class="{ 'dropdown-arrow-open': showRateMenu }"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 9l-7 7-7-7"
            ></path>
          </svg>
        </button>
        <div v-if="showRateMenu" class="rate-dropdown-menu">
          <button
            v-for="rate in playbackRates"
            :key="rate"
            class="rate-option"
            :class="{ 'rate-option-active': rate === currentPlaybackRate }"
            @click="setPlaybackRate(rate)"
          >
            {{ rate }}x
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.video-comparison {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1.25rem;
  display: flex;
  gap: 1rem;
  align-items: center;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .stat-card {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

.stat-icon {
  width: 48px;
  height: 48px;
  background: var(--alpha-badge);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-blue);
  flex-shrink: 0;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .stat-icon {
  background: var(--alpha-badge);
  color: var(--accent-blue);
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
  color: var(--text-muted);
  margin: 0 0 0.25rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .stat-label {
  color: var(--text-muted-light);
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .stat-value {
  color: var(--text-primary-light);
}

/* VideoPlayer 样式 */
.video-section {
  margin-bottom: 2rem;
}

.videos-wrapper {
  display: flex;
  gap: 0;
  margin-bottom: 2rem;
  align-items: flex-start;
}

/* 并排布局（默认） */
.videos-wrapper-side-by-side {
  flex-direction: row;
}

/* 上下布局 */
.videos-wrapper-stacked {
  flex-direction: column;
}

.video-section-half {
  flex: 1;
  margin-bottom: 0;
  min-width: 0;
  width: 100%;
}

/* 上下布局时，视频区域占满整个宽度 */
.videos-wrapper-stacked .video-section-half {
  flex: none;
  width: 100%;
}

.video-divider {
  width: 1px;
  background: var(--border-color);
  margin: 0 1.5rem;
  flex-shrink: 0;
  transition: background 0.3s;
}

/* 上下布局时的分隔线样式 */
.videos-wrapper-stacked .video-divider {
  width: 100%;
  height: 1px;
  margin: 1.5rem 0;
}

:global(:root:not(.dark)) .video-divider {
  background: var(--border-color-light);
}

.video-controls-bar {
  display: flex;
  gap: 0.75rem;
  width: fit-content;
  margin-bottom: 2rem;
  padding: 1rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .video-controls-bar {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

.btn-control {
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
  background: var(--bg-hover);
  border-color: var(--text-disabled-light);
}

.btn-control svg {
  width: 16px;
  height: 16px;
}

.btn-control-primary {
  background: var(--accent-blue);
  color: #fff;
  border-color: var(--accent-blue);
  transition: all 0.2s;
}

:global(:root:not(.dark)) .btn-control-primary {
  background: var(--accent-blue);
  color: #fff;
  border-color: var(--accent-blue);
}

.btn-control-primary:hover {
  background: var(--accent-blue-hover);
  border-color: var(--accent-blue-hover);
}

:global(:root:not(.dark)) .btn-control-primary:hover {
  background: var(--accent-info-hover);
  border-color: var(--accent-info-hover);
}

.video-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .video-section h3 {
  color: var(--text-primary-light);
}

.video-container {
  position: relative;
  background: var(--bg-main);
  border-radius: 8px;
  overflow: hidden;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .video-container {
  background: var(--bg-main-light);
}

.video-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
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

.placeholder-icon {
  width: 64px;
  height: 64px;
  color: var(--text-muted);
  margin-bottom: 1rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .placeholder-icon {
  color: var(--text-disabled-light);
}

.placeholder-text {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0 0 0.5rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .placeholder-text {
  color: var(--text-primary-light);
}

.placeholder-hint {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .placeholder-hint {
  color: var(--text-muted-light);
}

.video-container {
  background: var(--bg-video);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border-color);
  transition: border-color 0.3s;
}

:global(:root:not(.dark)) .video-container {
  border-color: var(--border-color-light);
}

.video-player {
  width: 100%;
  height: auto;
  display: block;
  max-height: 600px;
}

/* 上下布局时，让视频撑满宽度并调整最大高度 */
.videos-wrapper-stacked .video-player {
  max-height: 500px;
  object-fit: contain;
}

/* 速率控制下拉菜单 */
.rate-control-wrapper {
  position: relative;
}

.rate-dropdown-menu {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  min-width: 120px;
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 0.5rem 0;
  z-index: 100;
  box-shadow: var(--shadow-lg);
}

:global(:root:not(.dark)) .rate-dropdown-menu {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
  box-shadow: var(--shadow-lg-light);
}

.rate-option {
  width: 100%;
  padding: 0.5rem 1rem;
  background: transparent;
  color: var(--text-secondary);
  border: none;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
}

:global(:root:not(.dark)) .rate-option {
  color: var(--text-primary-light);
}

.rate-option:hover {
  background: var(--bg-hover);
}

:global(:root:not(.dark)) .rate-option:hover {
  background: var(--bg-hover);
}

.rate-option-active {
  background: var(--accent-blue);
  color: #fff;
}

:global(:root:not(.dark)) .rate-option-active {
  background: var(--accent-blue);
  color: #fff;
}

.rate-option-active:hover {
  background: var(--accent-blue-hover);
}

:global(:root:not(.dark)) .rate-option-active:hover {
  background: var(--accent-info-hover);
}

.dropdown-arrow {
  width: 12px;
  height: 12px;
  transition: transform 0.2s;
  margin-left: auto;
}

.dropdown-arrow-open {
  transform: rotate(180deg);
}
</style>