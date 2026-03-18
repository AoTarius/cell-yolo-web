<script setup lang="ts">
import '@/assets/styles/colors.css'
import type { AnalysisRecord } from '@/stores/analysisStore'
import VideoPlayer from './VideoPlayer.vue'

const props = defineProps<{
  record: AnalysisRecord
}>()

const emit = defineEmits<{
  videoError: []
}>()

function handleVideoError() {
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

    <!-- 视频播放器 -->
    <VideoPlayer
      :record="record"
      @video-error="handleVideoError"
    />
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
</style>