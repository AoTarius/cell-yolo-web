<script setup lang="ts">
import '@/assets/styles/colors.css'
import { computed, onMounted, watch, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAnalysisStore } from '@/stores/analysisStore'
import Sidebar from '@/components/common/Sidebar.vue'

const props = defineProps<{
  taskId?: string // 可选的 taskId，用于内嵌模式
  embedded?: boolean // 是否为内嵌模式（不显示侧边栏）
}>()

const route = useRoute()
const router = useRouter()
const store = useAnalysisStore()

// 从路由或 props 获取 taskId
const currentTaskId = computed(() => props.taskId || (route.params.taskId as string))

const isLoading = ref(true)

const record = computed(() => {
  return store.records.find((r) => r.task_id === currentTaskId.value) || null
})

function getStageLabel(stage: string): string {
  const stageMap: Record<string, string> = {
    'extracting': '分解视频',
    'processing': 'YOLO 推理',
    'packaging': '生成结果',
    'status': '状态更新',
    'complete': '完成'
  }
  return stageMap[stage] || '处理中'
}

function getStageIndex(stage: string): number {
  const stageOrder = ['extracting', 'processing', 'packaging', 'complete']
  return stageOrder.indexOf(stage)
}

// 加载历史任务并检查任务是否存在
onMounted(async () => {
  // 只在独立页面模式下执行加载逻辑
  if (!props.embedded) {
    // 加载历史任务（现在后端支持返回处理中的任务）
    await store.loadHistoryTasks()

    // 标记加载完成
    isLoading.value = false

    // 检查任务是否存在
    if (!record.value) {
      // 任务不存在，可能是因为刷新页面导致 store 清空
      // 返回主页显示默认界面
      router.push('/')
      return
    }

    // 如果找到任务，返回主页显示默认界面
    // 用户可以点击侧边栏的任务重新进入进度页面
    router.push('/')
  } else {
    // 内嵌模式，不需要加载历史任务
    isLoading.value = false
  }
})

// 监听 record 变化
watch(record, (newRecord) => {
  // 只在加载完成后才检查，避免加载过程中误判
  if (!isLoading.value && !newRecord) {
    // 任务被删除或不存在，显示友好提示
    console.error('任务不存在，请重新上传视频')
  }
})

// 查看结果
function viewResult() {
  if (record.value) {
    store.selectRecord(record.value.task_id)
  }
}

// 返回主页
function goBack() {
  router.push('/')
}
</script>

<template>
  <div class="progress-view" :class="{ 'embedded-mode': embedded }">
    <Sidebar v-if="!embedded" />

    <main class="main-panel" :class="{ 'has-sidebar': !embedded }">
      <div class="progress-container">
      <!-- 任务不存在的情况 -->
      <div v-if="!record && !isLoading" class="error-container">
        <svg
          class="error-icon"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          ></path>
        </svg>
        <h2>任务不存在</h2>
        <p class="error-message">找不到该分析任务，可能是因为页面刷新导致的。</p>
        <p class="error-hint">请重新上传视频开始新的分析。</p>
        <button class="btn-primary" @click="goBack">返回主页</button>
      </div>

      <!-- 正常进度显示 -->
      <template v-else>
      <!-- 标题 -->
      <div class="progress-header">
        <h2>分析进度</h2>
        <p class="video-name" v-if="record">{{ record.video_name }}</p>
      </div>

      <!-- 进度条 -->
      <div class="progress-section">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${record?.progress || 0}%` }"></div>
        </div>
        <p class="progress-text">{{ record?.progress || 0 }}%</p>
      </div>

      <!-- 当前状态信息 -->
      <div class="status-info" v-if="record">
        <div class="status-item">
          <span class="status-label">当前阶段：</span>
          <span class="status-value">{{ getStageLabel(record.stage || '') }}</span>
        </div>
        <div class="status-item" v-if="record.message">
          <span class="status-label">详细信息：</span>
          <span class="status-value">{{ record.message }}</span>
        </div>
        <div class="status-item" v-if="record.currentFrame !== null && record.totalFrames !== null">
          <span class="status-label">帧进度：</span>
          <span class="status-value">{{ record.currentFrame }} / {{ record.totalFrames }}</span>
        </div>
      </div>

      <!-- 处理步骤 -->
      <div class="steps-section">
        <div class="step-item" :class="{ active: getStageIndex(record?.stage || '') >= 0, current: getStageIndex(record?.stage || '') === 0 }">
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
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              ></path>
            </svg>
          </div>
          <div class="step-content">
            <p class="step-title">视频处理中</p>
            <p class="step-desc">使用 YOLOv8 进行细胞分割...</p>
          </div>
        </div>

        <div class="step-item" :class="{ active: getStageIndex(record?.stage || '') >= 1, current: getStageIndex(record?.stage || '') === 1 }">
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
          <div class="step-content">
            <p class="step-title">轨迹跟踪</p>
            <p class="step-desc">使用 DeepSORT 追踪细胞运动...</p>
          </div>
        </div>

        <div class="step-item" :class="{ active: getStageIndex(record?.stage || '') >= 2, current: getStageIndex(record?.stage || '') === 2 }">
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
          <div class="step-content">
            <p class="step-title">数据生成</p>
            <p class="step-desc">生成可视化数据和统计信息...</p>
          </div>
        </div>
      </div>

      <!-- 提示信息 -->
      <div class="hint-section">
        <p class="hint-text">这可能需要几分钟时间，请稍候...</p>
        <p class="hint-subtext" v-if="record?.status === 'completed'">✓ 分析已完成！</p>
        <div class="hint-actions" v-if="record?.status === 'completed'">
          <button class="btn-primary" @click="viewResult">查看结果</button>
          <button class="btn-secondary" @click="goBack">返回主页</button>
        </div>
      </div>
      </template>
      </div>
    </main>
  </div>
</template>

<style scoped>
.progress-view {
  display: flex;
  height: 100%;
  width: 100%;
  overflow: hidden;
  background: var(--bg-main);
  color: var(--text-secondary);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    sans-serif;
}

/* 独立页面模式下，progress-view 占满屏幕 */
.progress-view:not(.embedded-mode) {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  width: 100vw;
}

.main-panel {
  flex: 1;
  display: flex;
  overflow: hidden;
  align-items: center;
  justify-content: center;
}

.main-panel.has-sidebar {
  flex: 1;
}

:global(:root:not(.dark)) .progress-view {
  background: var(--bg-main-light);
  color: var(--text-primary-light);
}

.progress-container {
  max-width: 600px;
  width: 100%;
  text-align: center;
  padding: 2rem;
  overflow-y: auto;
}

.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 2rem;
}

.error-icon {
  width: 80px;
  height: 80px;
  color: var(--danger-light);
  margin-bottom: 1.5rem;
}

.error-container h2 {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .error-container h2 {
  color: var(--text-primary-light);
}

.error-message {
  font-size: 1rem;
  color: var(--text-muted);
  margin: 0 0 0.5rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .error-message {
  color: var(--text-muted-light);
}

.error-hint {
  font-size: 0.875rem;
  color: var(--text-disabled);
  margin: 0 0 2rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .error-hint {
  color: var(--text-disabled-light);
}

.progress-header {
  margin-bottom: 2rem;
}

.progress-header h2 {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .progress-header h2 {
  color: var(--text-primary-light);
}

.video-name {
  color: var(--text-muted);
  font-size: 1rem;
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .video-name {
  color: var(--text-muted-light);
}

.progress-section {
  margin-bottom: 2rem;
}

.progress-bar {
  height: 12px;
  background: var(--bg-input);
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 0.75rem;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .progress-bar {
  background: var(--bg-input-light);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--success), var(--success-hover));
  transition: width 0.3s ease;
  border-radius: 6px;
}

.progress-text {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--success);
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .progress-text {
  color: var(--success-light);
}

.status-info {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  text-align: left;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .status-info {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
}

.status-item:not(:last-child) {
  border-bottom: 1px solid var(--bg-input);
  transition: border-color 0.3s;
}

:global(:root:not(.dark)) .status-item:not(:last-child) {
  border-bottom-color: var(--border-color-light);
}

.status-label {
  color: var(--text-muted);
  font-size: 0.9rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .status-label {
  color: var(--text-muted-light);
}

.status-value {
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 500;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .status-value {
  color: var(--text-primary-light);
}

.steps-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  text-align: left;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .steps-section {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

.step-item {
  display: flex;
  gap: 1rem;
  padding: 1rem 0;
  opacity: 0.4;
  transition: opacity 0.3s;
}

.step-item:not(:last-child) {
  border-bottom: 1px solid var(--bg-input);
  transition: border-color 0.3s;
}

:global(:root:not(.dark)) .step-item:not(:last-child) {
  border-bottom-color: var(--border-color-light);
}

.step-item.active {
  opacity: 1;
}

.step-item.current {
  opacity: 1;
}

.step-item.current .step-icon {
  color: var(--warning);
}

.step-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  color: var(--text-disabled);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .step-icon {
  color: var(--border-color-light);
}

.step-icon svg {
  width: 24px;
  height: 24px;
}

.step-content {
  flex: 1;
}

.step-title {
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-secondary);
  margin: 0 0 0.25rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .step-title {
  color: var(--text-primary-light);
}

.step-desc {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .step-desc {
  color: var(--text-muted-light);
}

.hint-section {
  text-align: center;
}

.hint-text {
  color: var(--text-disabled);
  font-size: 0.875rem;
  margin: 0 0 0.5rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .hint-text {
  color: var(--text-disabled-light);
}

.hint-subtext {
  color: var(--success);
  font-size: 0.875rem;
  font-weight: 500;
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .hint-subtext {
  color: var(--success-light);
}

.hint-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 1rem;
}

.btn-primary,
.btn-secondary {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background: var(--success);
  color: white;
}

.btn-primary:hover {
  background: var(--success-hover);
}

:global(:root:not(.dark)) .btn-primary {
  background: var(--success-light);
}

:global(:root:not(.dark)) .btn-primary:hover {
  background: var(--success-hover);
}

.btn-secondary {
  background: var(--bg-input);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background: var(--border-color);
  border-color: var(--border-hover);
}

:global(:root:not(.dark)) .btn-secondary {
  background: var(--bg-hover);
  color: var(--text-primary-light);
  border-color: var(--border-color-light);
}

:global(:root:not(.dark)) .btn-secondary:hover {
  background: var(--bg-input-light);
  border-color: var(--border-hover-light);
}
</style>