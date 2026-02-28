<script setup lang="ts">
import { ref } from 'vue'
import type { AnalysisRecord } from '@/stores/analysisStore'

const props = defineProps<{
  record: AnalysisRecord
}>()

// 视频播放器引用
const originalVideoRef = ref<HTMLVideoElement | null>(null)
const annotatedVideoRef = ref<HTMLVideoElement | null>(null)

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
  console.error('Video playback error:', event)
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
</style>