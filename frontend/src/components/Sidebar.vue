<script setup lang="ts">
import { useAnalysisStore } from '@/stores/analysisStore'

const store = useAnalysisStore()

function formatDate(date: Date) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h1>细胞跟踪分析</h1>
      <button class="btn-new-analysis" @click="store.createNewAnalysis()">
        <span class="icon">+</span>
        新建分析
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
          @click="store.selectRecord(record.task_id)"
        >
          <div class="record-header">
            <span class="record-name">{{ record.video_name }}</span>
            <span class="record-status" :class="`status-${record.status}`">
              {{
                record.status === 'completed'
                  ? '已完成'
                  : record.status === 'processing'
                    ? `处理中 ${record.progress}%`
                    : record.status
              }}
            </span>
          </div>
          <div class="record-video">任务ID: {{ record.task_id }}</div>
          <div class="record-time">{{ formatDate(record.start_time) }}</div>
        </div>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 280px;
  height: 100vh;
  background: #1e1e1e;
  color: #e0e0e0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #333;
}

.sidebar-header {
  padding: 1.5rem;
  border-bottom: 1px solid #333;
}

.sidebar-header h1 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
  color: #fff;
}

.btn-new-analysis {
  width: 100%;
  padding: 0.75rem 1rem;
  background: #007acc;
  color: white;
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
  background: #005a9e;
}

.btn-new-analysis .icon {
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
  color: #888;
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
  background: #252525;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.record-item:hover {
  background: #2d2d2d;
  border-color: #444;
}

.record-item.active {
  background: #264f78;
  border-color: #007acc;
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
  color: #fff;
}

.record-status {
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-weight: 500;
}

.status-completed {
  background: #0e5a2b;
  color: #4ade80;
}

.status-processing {
  background: #5a4a0e;
  color: #fbbf24;
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
  color: #777;
}

/* 滚动条样式 */
.sidebar-content::-webkit-scrollbar {
  width: 8px;
}

.sidebar-content::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.sidebar-content::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 4px;
}

.sidebar-content::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>
