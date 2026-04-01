<script setup lang="ts">
import '@/assets/styles/colors.css'
import { onMounted } from 'vue'
import Sidebar from '@/components/common/layout/Sidebar.vue'
import VideoManage from './VideoManage.vue'
import ModelManage from './ModelManage.vue'
import CompareCard from './CompareCard.vue'

onMounted(() => {
  // 页面初始化
})
</script>

<template>
  <div class="resource-view">
    <Sidebar />

    <main class="main-panel">
      <div class="content-container">
        <!-- 左侧：视频管理 -->
        <div class="content-section video-section">
          <VideoManage />
        </div>
        <div class="divider" style="width: 1px; background: var(--border-color);"></div>
        <!-- 中间：模型管理 -->
        <div class="content-section model-section">
          <ModelManage />
        </div>

        <!-- 右侧：模型效果对比 -->
        <div class="content-section compare-section">
          <CompareCard />
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.resource-view {
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

.content-container {
  flex: 1;
  display: flex;
  flex-direction: row;
  gap: 1.5rem;
  padding: 2rem;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
}

.content-section {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.video-section {
  flex: 2;
}

.model-section {
  flex: 2;
}

.compare-section {
  flex: 1;
}
</style>