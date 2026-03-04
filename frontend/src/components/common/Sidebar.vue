<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAnalysisStore, type AnalysisRecord } from '@/stores/analysisStore'
import { useToast } from '@/composables/useToast'
import ConfirmDialog from './ConfirmDialog.vue'
import '@/assets/styles/colors.css'

const store = useAnalysisStore()
const router = useRouter()
const route = useRoute()
const { showToast } = useToast()

// 组件挂载时加载历史记录
onMounted(async () => {
  await store.loadHistoryTasks()
})

const showDeleteDialog = ref(false)
const taskToDelete = ref<string | null>(null)

// 主题切换
const isDark = ref(true)

// 初始化主题
onMounted(async () => {
  await store.loadHistoryTasks()
  
  // 从localStorage读取主题设置
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'light') {
    isDark.value = false
    document.documentElement.classList.remove('dark')
  } else {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
})

// 切换主题
function toggleTheme() {
  isDark.value = !isDark.value
  if (isDark.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

function formatDate(date: Date) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function handleRecordClick(record: AnalysisRecord) {
  // 如果不在主页，先跳转回主页
  if (route.path !== '/') {
    router.push('/').then(() => {
      store.selectRecord(record.task_id)
      // 等待 DOM 更新后滚动到顶部
      nextTick(() => {
        scrollToTop()
      })
    })
  } else {
    store.selectRecord(record.task_id)
    // 等待 DOM 更新后滚动到顶部
    nextTick(() => {
      scrollToTop()
    })
  }
}

// 滚动到顶部
function scrollToTop() {
  const resultContent = document.querySelector('.result-content')
  if (resultContent) {
    resultContent.scrollTop = 0
  }
}

function showDeleteConfirm(taskId: string, event: Event) {
  event.stopPropagation() // 阻止触发记录选择
  taskToDelete.value = taskId
  showDeleteDialog.value = true
}

async function handleDeleteConfirm() {
  if (taskToDelete.value) {
    try {
      await store.deleteRecord(taskToDelete.value)
      showToast('任务已成功删除', 'success')
    } catch (error) {
      console.error('删除失败:', error)
      showToast('删除任务失败', 'error')
    } finally {
      taskToDelete.value = null
    }
  }
}

function handleDeleteCancel() {
  taskToDelete.value = null
}

function handleNewAnalysis() {
  // 如果不在主页，先跳转回主页
  if (route.path !== '/') {
    router.push('/').then(() => {
      store.createNewAnalysis()
    })
  } else {
    store.createNewAnalysis()
  }
}

function handleModelUpload() {
  router.push('/model-upload')
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h1>细胞跟踪分析</h1>
      <button class="btn-new-analysis" @click="handleNewAnalysis">
        <span class="icon">+</span>
        新建分析
      </button>
      <button class="btn-upload-model" @click="handleModelUpload">
        <span class="icon">+</span>
        上传模型
      </button>
    </div>

    <div class="sidebar-content">
      <h2 class="section-title">历史记录</h2>
      <div class="records-list">
        <div
          v-for="record in store.records"
          :key="record.task_id"
          class="record-item"
          :class="{ active: store.selectedId === record.task_id }"
          @click="handleRecordClick(record)"
        >
          <div class="record-header">
            <span class="record-name">{{ record.video_name }}</span>
            <div class="status-indicator">
              <span class="status-dot" :class="`dot-${record.status}`"></span>
              <span class="record-status" :class="`status-${record.status}`">
                {{
                  record.status === 'completed'
                    ? '已完成'
                    : record.status === 'processing'
                      ? '分析中'
                      : record.status
                }}
              </span>
            </div>
          </div>
          <div class="record-video">任务ID: {{ record.task_id }}</div>
          <div class="record-footer">
            <span class="record-time">{{ formatDate(record.start_time) }}</span>
            <span class="model-badge">
              <svg
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
                class="model-icon"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
                ></path>
              </svg>
              {{ record.result?.model_name || 'N/A' }}
            </span>
            <button
              class="btn-delete"
              @click="showDeleteConfirm(record.task_id, $event)"
              title="删除记录"
              :disabled="record.status === 'processing'"
            >
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
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                ></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <ConfirmDialog
      v-model:visible="showDeleteDialog"
      title="删除记录"
      message="确定要删除这条记录吗？此操作将删除所有相关文件（包括原始视频、处理结果等），且无法恢复。"
      type="danger"
      confirm-text="删除"
      cancel-text="取消"
      @confirm="handleDeleteConfirm"
      @cancel="handleDeleteCancel"
    />

    <!-- 底部状态栏 -->
    <div class="sidebar-footer">
      <button class="btn-theme-toggle" title="切换主题" @click="toggleTheme">
        <svg
          class="theme-icon"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            v-if="!isDark"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M20.354 15.354A9 9 0 018.646 3.646 9 9 0 0012.708-3.646 9 9 0 01-2.708 3.646M3 12a9 9 0 0112.708-3.646M9 21V9a9 9 0 00-9-9m9 12a9 9 0 01-9-9m6 2a7 7 0 01-7 7m0 0v-3m0 0a7 7 0 017 7m0 0h3m0 0v-3"
          ></path>
          <path
            v-else
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
          ></path>
        </svg>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 320px;
  height: 100vh;
  background: var(--bg-sidebar);
  color: var(--text-secondary);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-secondary);
}

.sidebar-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-secondary);
}

.sidebar-header h1 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
  color: var(--text-primary);
}

.btn-new-analysis {
  width: 100%;
  padding: 0.75rem 1rem;
  background: var(--accent-info);
  color: var(--text-primary);
  border: none;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: background 0.2s;
}

.btn-new-analysis:hover {
  background: var(--accent-info-hover);
}

.btn-new-analysis .icon {
  font-size: 1.25rem;
  font-weight: 300;
}

.btn-upload-model {
  width: 100%;
  padding: 0.75rem 1rem;
  background: var(--btn-upload);
  color: var(--text-primary);
  border: none;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: background 0.2s;
  margin-top: 0.75rem;
}

.btn-upload-model:hover {
  background: var(--btn-upload-hover);
}

.btn-upload-model .icon {
  font-size: 1.25rem;
  font-weight: 300;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.section-title {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin: 0 0 0.75rem 0.5rem;
  font-weight: 600;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.record-item {
  padding: 0.75rem;
  background: var(--bg-record);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.record-item:hover {
  background: var(--bg-record-hover);
  border-color: var(--border-tertiary);
}

.record-item.active {
  background: var(--bg-record-active);
  border-color: var(--accent-blue);
}

.record-item.active .btn-delete:hover:not(:disabled) {
  background: var(--alpha-hover);
  color: var(--danger-light);
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.record-name {
  font-weight: 500;
  font-size: 0.95rem;
  color: var(--text-primary);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-completed {
  background: var(--success-light);
  box-shadow: var(--shadow-success);
}

.dot-processing {
  background: var(--warning);
  box-shadow: var(--shadow-warning);
  animation: pulse-orange 2s ease-in-out infinite;
}

@keyframes pulse-orange {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.record-status {
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-weight: 500;
}

.status-completed {
  background: var(--success-bg);
  color: var(--success-light);
}

.status-processing {
  background: var(--warning-bg);
  color: var(--warning);
}

.record-video {
  font-size: 0.85rem;
  color: #b0b0b0;
  margin-bottom: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-time {
  font-size: 0.75rem;
  color: var(--text-disabled);
}

.model-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.6rem;
  background: var(--alpha-badge);
  border: 1px solid var(--alpha-badge-hover);
  border-radius: 4px;
  color: var(--accent-blue);
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.2s;
}

:global(:root:not(.dark)) .model-badge {
  background: var(--alpha-badge);
  border-color: var(--alpha-badge-hover);
  color: var(--accent-blue);
}

.model-badge:hover {
  background: var(--alpha-badge-hover);
  border-color: var(--alpha-badge-hover);
  filter: brightness(1.1);
}

:global(:root:not(.dark)) .model-badge:hover {
  background: var(--alpha-badge-hover);
  border-color: var(--alpha-badge-hover);
  filter: brightness(1.1);
}

.model-icon {
  width: 12px;
  height: 12px;
}

.record-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.25rem;
}

.btn-delete {
  background: transparent;
  border: none;
  color: var(--text-disabled);
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
}

.record-item:hover .btn-delete {
  opacity: 1;
}

.btn-delete:hover:not(:disabled) {
  background: var(--alpha-hover);
  color: var(--danger-light);
}

.btn-delete:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.btn-delete svg {
  width: 16px;
  height: 16px;
}

/* 滚动条样式 */
.sidebar-content::-webkit-scrollbar {
  width: 8px;
}

.sidebar-content::-webkit-scrollbar-track {
  background: var(--bg-sidebar);
}

.sidebar-content::-webkit-scrollbar-thumb {
  background: var(--border-tertiary);
  border-radius: 4px;
}

.sidebar-content::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* 底部状态栏 */
.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid var(--border-secondary);
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.btn-theme-toggle {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--bg-record-hover);
  border: 1px solid var(--border-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-theme-toggle:hover {
  background: #3d3d3d;
  border-color: var(--border-hover);
  transform: scale(1.05);
}

.btn-theme-toggle:active {
  transform: scale(0.95);
}

.theme-icon {
  width: 24px;
  height: 24px;
  transition: all 0.3s ease;
}
</style>
