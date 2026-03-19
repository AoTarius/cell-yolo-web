<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAnalysisStore } from '@/stores/analysisStore'
import { useUserStore } from '@/stores/userStore'
import Sidebar from '@/components/common/Sidebar.vue'
import ProgressView from '@/views/ProgressView.vue'
import AnalysisResult from '@/components/analysis/AnalysisResult.vue'
import '@/assets/styles/colors.css'

const store = useAnalysisStore()
const userStore = useUserStore()

// 组件挂载时加载历史任务
onMounted(async () => {
  // 只有已登录用户才加载任务列表
  if (userStore.currentUser) {
    await store.loadHistoryTasks()
  }
})

// 当前显示的主面板
const currentPanel = computed(() => {
  if (store.selectedRecord) {
    if (store.selectedRecord.status === 'processing') {
      return 'loading'
    }
    if (store.selectedRecord.status === 'completed') {
      return 'result'
    }
  }
  return 'welcome'
})
</script>

<template>
  <div class="cell-tracking-view">
    <Sidebar />

    <main class="main-panel">
      <!-- 欢迎面板 -->
      <div v-if="currentPanel === 'welcome'" class="welcome-panel">
        <div class="welcome-content">
          <svg
            class="welcome-icon"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
            ></path>
          </svg>
          <h1>细胞跟踪分析平台</h1>
          <p>点击左侧 "新建分析" 开始上传视频，或选择历史记录查看结果</p>
        </div>
      </div>

      <!-- 加载面板 -->
      <ProgressView
        v-else-if="currentPanel === 'loading'"
        :task-id="store.selectedRecord?.task_id"
        :embedded="true"
      />

      <!-- 结果面板 -->
      <AnalysisResult v-else-if="currentPanel === 'result'" :record="store.selectedRecord!" />
    </main>
  </div>
</template>

<style scoped>
.cell-tracking-view {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: var(--bg-main);
  color: var(--text-secondary);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    sans-serif;
  position: fixed;
  top: 0;
  left: 0;
}

.main-panel {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.welcome-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.welcome-content {
  text-align: center;
  max-width: 500px;
}

.welcome-icon {
  width: 120px;
  height: 120px;
  color: var(--accent-blue);
  margin: 0 auto 2rem;
}

.welcome-content h1 {
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
}

.welcome-content p {
  font-size: 1.1rem;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.6;
}
</style>