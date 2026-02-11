<script setup lang="ts">
const props = defineProps<{
  videoName?: string
  progress?: number
}>()
</script>

<template>
  <div class="loading-panel">
    <div class="loading-container">
      <div class="spinner-container">
        <div class="spinner"></div>
        <div class="spinner-glow"></div>
      </div>

      <h2>正在分析视频</h2>
      <p class="loading-subtitle" v-if="videoName">{{ videoName }}</p>

      <!-- 进度条 -->
      <div class="progress-bar-container" v-if="progress !== undefined">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
        </div>
        <p class="progress-text">{{ progress }}%</p>
      </div>

      <div class="progress-info">
        <div class="progress-step">
          <div class="step-icon">
            <svg
              class="animate-spin"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              ></path>
            </svg>
          </div>
          <div class="step-text">
            <p class="step-title">视频处理中</p>
            <p class="step-desc">使用 YOLOv8 进行细胞分割...</p>
          </div>
        </div>

        <div class="progress-step">
          <div class="step-icon">
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
                d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
              ></path>
            </svg>
          </div>
          <div class="step-text">
            <p class="step-title">轨迹跟踪</p>
            <p class="step-desc">使用 DeepSORT 追踪细胞运动...</p>
          </div>
        </div>

        <div class="progress-step">
          <div class="step-icon">
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
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              ></path>
            </svg>
          </div>
          <div class="step-text">
            <p class="step-title">数据生成</p>
            <p class="step-desc">生成可视化数据和统计信息...</p>
          </div>
        </div>
      </div>

      <p class="loading-hint">这可能需要几分钟时间，请稍候...</p>
    </div>
  </div>
</template>

<style scoped>
.loading-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: #0d1117;
}

.loading-container {
  max-width: 500px;
  width: 100%;
  text-align: center;
}

.spinner-container {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 2rem;
}

.spinner {
  width: 120px;
  height: 120px;
  border: 4px solid #21262d;
  border-top-color: #58a6ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(88, 166, 255, 0.1) 0%, transparent 70%);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.1);
  }
}

.animate-spin {
  animation: spin 2s linear infinite;
}

h2 {
  font-size: 1.75rem;
  font-weight: 600;
  color: #fff;
  margin: 0 0 0.5rem 0;
}

.loading-subtitle {
  color: #8b949e;
  margin: 0 0 1rem 0;
}

.progress-bar-container {
  margin: 1rem 0 2rem 0;
}

.progress-bar {
  height: 8px;
  background: #21262d;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #58a6ff, #1f6feb);
  transition: width 0.3s ease;
  border-radius: 4px;
}

.progress-text {
  font-size: 0.875rem;
  color: #58a6ff;
  font-weight: 600;
  margin: 0;
}

.progress-info {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 1.5rem;
  margin: 2rem 0;
  text-align: left;
}

.progress-step {
  display: flex;
  gap: 1rem;
  padding: 1rem 0;
}

.progress-step:not(:last-child) {
  border-bottom: 1px solid #21262d;
}

.step-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  color: #58a6ff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-icon svg {
  width: 24px;
  height: 24px;
}

.step-text {
  flex: 1;
}

.step-title {
  font-size: 1rem;
  font-weight: 500;
  color: #c9d1d9;
  margin: 0 0 0.25rem 0;
}

.step-desc {
  font-size: 0.875rem;
  color: #8b949e;
  margin: 0;
}

.loading-hint {
  color: #6e7681;
  font-size: 0.875rem;
  margin: 0;
}
</style>
