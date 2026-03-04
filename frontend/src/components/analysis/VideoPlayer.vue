<script setup lang="ts">
import { ref, watch } from 'vue'
import type { AnalysisRecord } from '@/stores/analysisStore'

const props = defineProps<{
  record: AnalysisRecord
}>()

// 视频播放器引用
const originalVideoRef = ref<HTMLVideoElement | null>(null)
const annotatedVideoRef = ref<HTMLVideoElement | null>(null)

// 视频加载错误状态
const originalVideoError = ref(false)
const annotatedVideoError = ref(false)

// 监听record.task_id变化，切换记录卡时重置播放速率
watch(() => props.record.task_id, () => {
  currentPlaybackRate.value = 1
  showRateMenu.value = false
  if (originalVideoRef.value) {
    originalVideoRef.value.playbackRate = 1
  }
  if (annotatedVideoRef.value) {
    annotatedVideoRef.value.playbackRate = 1
  }
})

// 计算视频帧率（基于总帧数和时长）
function getVideoFps(): number {
  const totalFrames = props.record.result?.total_frames || 0
  const duration = props.record.result?.video_duration || 0
  if (duration > 0 && totalFrames > 0) {
    return totalFrames / duration
  }
  return 30 // 默认帧率
}

// 视频布局模式：'side-by-side' (并排) 或 'stacked' (上下)
const videoLayoutMode = ref<'side-by-side' | 'stacked'>('side-by-side')

// 切换视频布局模式
function toggleVideoLayout() {
  videoLayoutMode.value = videoLayoutMode.value === 'side-by-side' ? 'stacked' : 'side-by-side'
}

// 播放速率选项
const playbackRates = [0.25, 0.5, 0.75, 1, 1.5, 2]
const currentPlaybackRate = ref(1)
const showRateMenu = ref(false)

// 切换速率菜单显示
function toggleRateMenu() {
  showRateMenu.value = !showRateMenu.value
}

// 设置播放速率
function setPlaybackRate(rate: number) {
  currentPlaybackRate.value = rate
  if (originalVideoRef.value) {
    originalVideoRef.value.playbackRate = rate
  }
  if (annotatedVideoRef.value) {
    annotatedVideoRef.value.playbackRate = rate
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

// 前进一帧功能
function handleForwardFrame() {
  const fps = getVideoFps()
  const frameDuration = 1 / fps
  if (originalVideoRef.value) {
    originalVideoRef.value.currentTime += frameDuration
    originalVideoRef.value.pause()
  }
  if (annotatedVideoRef.value) {
    annotatedVideoRef.value.currentTime += frameDuration
    annotatedVideoRef.value.pause()
  }
}

// 后退一帧功能
function handleBackwardFrame() {
  const fps = getVideoFps()
  const frameDuration = 1 / fps
  if (originalVideoRef.value) {
    originalVideoRef.value.currentTime = Math.max(0, originalVideoRef.value.currentTime - frameDuration)
    originalVideoRef.value.pause()
  }
  if (annotatedVideoRef.value) {
    annotatedVideoRef.value.currentTime = Math.max(0, annotatedVideoRef.value.currentTime - frameDuration)
    annotatedVideoRef.value.pause()
  }
}

// 获取视频 URL
function getVideoUrl(taskId: string): string {
  return `/api/video/${taskId}/`
}

// 获取原始视频 URL
function getOriginalVideoUrl(taskId: string): string {
  return `/api/original-video/${taskId}/`
}

// 处理视频错误
const emit = defineEmits<{
  videoError: []
}>()

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
      {{ videoLayoutMode === 'side-by-side' ? '放大显示' : '并排显示' }}
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
    <button class="btn-control" @click="handleBackwardFrame">
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
    <button class="btn-control" @click="handleForwardFrame">
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
</template>

<style scoped>
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
  background: #30363d;
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
  background: #e0e0e0;
}

.video-controls-bar {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 2rem;
  padding: 1rem;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .video-controls-bar {
  background: #fff;
  border-color: #e0e0e0;
}

.btn-control {
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

:global(:root:not(.dark)) .btn-control {
  background: #fff;
  color: #333;
  border-color: #ccc;
}

.btn-control:hover {
  background: #30363d;
  border-color: #8b949e;
}

:global(:root:not(.dark)) .btn-control:hover {
  background: #f5f5f5;
  border-color: #999;
}

.btn-control svg {
  width: 16px;
  height: 16px;
}

.btn-control-primary {
  background: #1f6feb;
  color: #fff;
  border-color: #1f6feb;
  transition: all 0.2s;
}

:global(:root:not(.dark)) .btn-control-primary {
  background: #2196f3;
  color: #fff;
  border-color: #2196f3;
}

.btn-control-primary:hover {
  background: #388bfd;
  border-color: #388bfd;
}

:global(:root:not(.dark)) .btn-control-primary:hover {
  background: #1976d2;
  border-color: #1976d2;
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
  position: relative;
  background: #0d1117;
  border-radius: 8px;
  overflow: hidden;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .video-container {
  background: #f5f5f5;
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
  background: rgba(13, 17, 23, 0.95);
  transition: background 0.3s;
}

:global(:root:not(.dark)) .video-placeholder {
  background: rgba(245, 245, 245, 0.95);
}

.placeholder-icon {
  width: 64px;
  height: 64px;
  color: #8b949e;
  margin-bottom: 1rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .placeholder-icon {
  color: #999;
}

.placeholder-text {
  font-size: 1rem;
  color: #c9d1d9;
  margin: 0 0 0.5rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .placeholder-text {
  color: #333;
}

.placeholder-hint {
  font-size: 0.875rem;
  color: #8b949e;
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .placeholder-hint {
  color: #666;
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
  background: #21262d;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 0.5rem 0;
  z-index: 100;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

:global(:root:not(.dark)) .rate-dropdown-menu {
  background: #fff;
  border-color: #ccc;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.rate-option {
  width: 100%;
  padding: 0.5rem 1rem;
  background: transparent;
  color: #c9d1d9;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
}

:global(:root:not(.dark)) .rate-option {
  color: #333;
}

.rate-option:hover {
  background: #30363d;
}

:global(:root:not(.dark)) .rate-option:hover {
  background: #f5f5f5;
}

.rate-option-active {
  background: #1f6feb;
  color: #fff;
}

:global(:root:not(.dark)) .rate-option-active {
  background: #2196f3;
  color: #fff;
}

.rate-option-active:hover {
  background: #388bfd;
}

:global(:root:not(.dark)) .rate-option-active:hover {
  background: #1976d2;
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