<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAnalysisStore, type AnalysisRecord } from '@/stores/analysisStore'
import Sidebar from '@/components/common/layout/Sidebar.vue'
import '@/assets/styles/colors.css'

const router = useRouter()
const store = useAnalysisStore()

// 选中的对比记录（最多两条）
const selectedRecords = ref<AnalysisRecord[]>([])

// 添加记录到对比列表
function addRecordToCompare(record: AnalysisRecord) {
  if (selectedRecords.value.length < 2) {
    selectedRecords.value.push(record)
  }
}

// 从对比列表中移除记录
function removeRecordFromCompare(index: number) {
  selectedRecords.value.splice(index, 1)
}

// 是否可以点击确定按钮
const canConfirm = computed(() => selectedRecords.value.length === 2)

// 点击确定按钮
function handleConfirm() {
  if (selectedRecords.value.length === 2) {
    store.goToCompareResult(selectedRecords.value[0], selectedRecords.value[1], router)
  }
}

// 暴露方法给 Sidebar 调用
defineExpose({
  addRecordToCompare
})
</script>

<template>
  <div class="compare-view">
    <Sidebar :compare-mode="true" @select-record="addRecordToCompare" />

    <main class="main-panel">
      <div class="compare-content">
        <div class="compare-header">
          <h1>对比分析</h1>
          <p class="compare-description">从左侧历史栏选择两条历史条目进行对比分析</p>
          <p class="compare-description">再次点击【对比分析】快速退出对比模式</p>
        </div>

        <div class="compare-items">
          <div
            v-for="(record, index) in selectedRecords"
            :key="index"
            class="compare-item"
          >
            <div class="item-info">
              <div class="item-label">{{ index === 0 ? '记录 A' : '记录 B' }}</div>
              <div class="item-name">{{ record.task_name }}</div>
              <div class="item-details">
                <span class="detail-item">
                  <svg
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                    class="detail-icon"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
                    ></path>
                  </svg>
                  {{ record.model_name || 'N/A' }}
                </span>
              </div>
            </div>
            <button class="btn-remove" @click="removeRecordFromCompare(index)" title="取消选中">
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
                  d="M6 18L18 6M6 6l12 12"
                ></path>
              </svg>
            </button>
          </div>

          <!-- 提示信息 -->
          <div v-if="selectedRecords.length === 0" class="compare-placeholder">
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
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              ></path>
            </svg>
            <p>请从左侧历史栏选择两条历史条目</p>
          </div>

          <!-- 只选中了一条记录的提示 -->
          <div v-if="selectedRecords.length === 1" class="compare-placeholder">
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
                d="M12 6v6m0 0v6m0-6h6m-6 0H6"
              ></path>
            </svg>
            <p>请再选择一条历史条目</p>
          </div>
        </div>

        <!-- 确定按钮 -->
        <div class="compare-actions">
          <button
            class="btn-confirm"
            :class="{ disabled: !canConfirm }"
            :disabled="!canConfirm"
            @click="handleConfirm"
          >
            确定
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.compare-view {
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
  align-items: center;
}

.compare-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 2rem;
  overflow-y: auto;
  align-content: center;
}

.compare-header {
  text-align: center;
  margin-bottom: 2rem;
}

.compare-header h1 {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
}

.compare-description {
  font-size: 1rem;
  color: var(--text-muted);
  margin: 0;
}

.compare-items {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.compare-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
  background: var(--bg-record);
  border: 1px solid var(--border-secondary);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.compare-item:hover {
  background: var(--bg-record-hover);
  border-color: var(--border-tertiary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.item-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--accent-purple);
  font-weight: 600;
}

.item-name {
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--text-primary);
}

.item-details {
  display: flex;
  gap: 1.5rem;
  margin-top: 0.25rem;
}

.detail-item {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.detail-icon {
  width: 14px;
  height: 14px;
}

.btn-remove {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  background: var(--bg-record-hover);
  border: 1px solid var(--border-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.btn-remove:hover {
  background: var(--danger-bg);
  border-color: var(--danger-light);
  color: var(--danger-light);
}

.btn-remove svg {
  width: 18px;
  height: 18px;
}

.compare-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 4rem 2rem;
  background: var(--bg-record);
  border: 2px dashed var(--border-tertiary);
  border-radius: 8px;
  color: var(--text-muted);
}

.placeholder-icon {
  width: 64px;
  height: 64px;
  opacity: 0.5;
}

.compare-placeholder p {
  font-size: 1rem;
  margin: 0;
}

.compare-actions {
  display: flex;
  justify-content: center;
  padding-top: 2rem;
}

.btn-confirm {
  padding: 0.875rem 3rem;
  background: var(--accent-purple);
  color: var(--text-primary);
  border: 1px solid var(--accent-purple);
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
  border: 1px solid var(--border-color);
}

.btn-confirm:hover:not(.disabled) {
  background: var(--accent-purple-hover);
  border-color: var(--accent-purple-hover);
  border: 1px solid var(--border-color);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

.btn-confirm:active:not(.disabled) {
  transform: translateY(0);
}

.btn-confirm.disabled {
  background: var(--bg-disabled);
  color: var(--text-disabled);
  border-color: var(--border-tertiary);
  cursor: not-allowed;
  box-shadow: none;
}

/* 滚动条样式 */
.compare-content::-webkit-scrollbar {
  width: 8px;
}

.compare-content::-webkit-scrollbar-track {
  background: var(--bg-main);
}

.compare-content::-webkit-scrollbar-thumb {
  background: var(--border-tertiary);
  border-radius: 4px;
}

.compare-content::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>