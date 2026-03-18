<script setup lang="ts">
import { ref } from 'vue'
import '@/assets/styles/colors.css'

export interface SortCondition {
  id: string
  field: SortField
  direction: SortDirection
}

export type SortField = 'createdAt' | 'updatedAt' | 'taskName' | 'modelName'
export type SortDirection = 'asc' | 'desc'

interface Props {
  visible: boolean
  currentSort?: SortCondition[]
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'sort', conditions: SortCondition[]): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 排序条件列表
const sortConditions = ref<SortCondition[]>(
  props.currentSort && props.currentSort.length > 0
    ? [...props.currentSort]
    : [
        {
          id: '1',
          field: 'createdAt',
          direction: 'desc'
        }
      ]
)

// 字段定义
const fieldDefinitions = {
  createdAt: {
    label: '创建时间',
    icon: 'fa-calendar',
    dbField: 'created_at'
  },
  updatedAt: {
    label: '更新时间',
    icon: 'fa-clock',
    dbField: 'updated_at'
  },
  taskName: {
    label: '任务名称',
    icon: 'fa-tag',
    dbField: 'task_name'
  },
  modelName: {
    label: '模型名称',
    icon: 'fa-microchip',
    dbField: 'model_name'
  }
}

// 排序方向定义
const directionDefinitions = {
  asc: { label: '顺序', icon: 'fa-arrow-up' },
  desc: { label: '倒序', icon: 'fa-arrow-down' }
}

// 关闭排序器
function closeSort() {
  emit('update:visible', false)
}

// 添加排序条件
function addSortCondition() {
  const newId = String(sortConditions.value.length + 1)
  sortConditions.value.push({
    id: newId,
    field: 'createdAt',
    direction: 'desc'
  })
}

// 删除排序条件
function removeSortCondition(id: string) {
  const index = sortConditions.value.findIndex(c => c.id === id)
  if (index > -1) {
    sortConditions.value.splice(index, 1)
  }
}

// 上移排序条件
function moveUp(id: string) {
  const index = sortConditions.value.findIndex(c => c.id === id)
  if (index > 0) {
    const temp = sortConditions.value[index]!
    sortConditions.value[index] = sortConditions.value[index - 1]!
    sortConditions.value[index - 1] = temp
  }
}

// 下移排序条件
function moveDown(id: string) {
  const index = sortConditions.value.findIndex(c => c.id === id)
  if (index < sortConditions.value.length - 1) {
    const temp = sortConditions.value[index]!
    sortConditions.value[index] = sortConditions.value[index + 1]!
    sortConditions.value[index + 1] = temp
  }
}

// 应用排序
function applySort() {
  emit('sort', sortConditions.value)
  closeSort()
}

// 重置排序
function resetSort() {
  sortConditions.value = [
    {
      id: '1',
      field: 'createdAt',
      direction: 'desc'
    }
  ]
  emit('sort', sortConditions.value)
  closeSort()
}
</script>

<template>
  <Transition name="fade">
    <div v-if="visible" class="sort-overlay" @click="closeSort">
      <div class="sort-modal" @click.stop>
        <div class="sort-header">
          <h3 class="sort-title">
            <svg
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
              class="sort-icon"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12"
              ></path>
            </svg>
            排序设置
          </h3>
          <button class="btn-close" @click="closeSort" title="关闭">
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

        <div class="sort-content">
          <div
            v-for="(condition, index) in sortConditions"
            :key="condition.id"
            class="sort-row"
          >
            <!-- 优先级标识 -->
            <div class="sort-priority">
              <span class="priority-badge">{{ index + 1 }}</span>
            </div>

            <!-- 字段选择 -->
            <div class="sort-field">
              <svg
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
                class="field-icon"
              >
                <path
                  v-if="condition.field === 'createdAt'"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                ></path>
                <path
                  v-else-if="condition.field === 'updatedAt'"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                ></path>
                <path
                  v-else-if="condition.field === 'taskName'"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                ></path>
                <path
                  v-else-if="condition.field === 'modelName'"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
                ></path>
              </svg>
              <select v-model="condition.field" class="field-select">
                <option value="createdAt">创建时间</option>
                <option value="updatedAt">更新时间</option>
                <option value="taskName">任务名称</option>
                <option value="modelName">模型名称</option>
              </select>
            </div>

            <!-- 排序方向 -->
            <div class="sort-direction">
              <select v-model="condition.direction" class="direction-select">
                <option value="asc">顺序</option>
                <option value="desc">倒序</option>
              </select>
              <svg
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
                class="direction-icon"
                :class="{ 'icon-asc': condition.direction === 'asc', 'icon-desc': condition.direction === 'desc' }"
              >
                <path
                  v-if="condition.direction === 'asc'"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M5 15l7-7 7 7"
                ></path>
                <path
                  v-else
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 9l-7 7-7-7"
                ></path>
              </svg>
            </div>

            <!-- 操作按钮 -->
            <div class="sort-actions">
              <button
                class="btn-move"
                @click="moveUp(condition.id)"
                :disabled="index === 0"
                title="上移"
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
                    d="M5 15l7-7 7 7"
                  ></path>
                </svg>
              </button>
              <button
                class="btn-move"
                @click="moveDown(condition.id)"
                :disabled="index === sortConditions.length - 1"
                title="下移"
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
                    d="M19 9l-7 7-7-7"
                  ></path>
                </svg>
              </button>
              <button
                class="btn-remove"
                @click="removeSortCondition(condition.id)"
                :disabled="sortConditions.length === 1"
                title="删除"
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
                    d="M6 18L18 6M6 6l12 12"
                  ></path>
                </svg>
              </button>
            </div>
          </div>

          <!-- 添加排序条件按钮 -->
          <button class="btn-add" @click="addSortCondition" v-if="sortConditions.length < 3">
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
                d="M12 6v6m0 0v6m0-6h6m-6 0H6"
              ></path>
            </svg>
            添加排序条件
          </button>
        </div>

        <div class="sort-footer">
          <button class="btn-reset" @click="resetSort">
            <svg
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
              class="reset-icon"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              ></path>
            </svg>
            重置
          </button>
          <button class="btn-apply" @click="applySort">
            应用排序
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.sort-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.sort-modal {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

:global(:root:not(.dark)) .sort-modal {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.sort-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

:global(:root:not(.dark)) .sort-header {
  border-color: var(--border-color-light);
}

.sort-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

:global(:root:not(.dark)) .sort-title {
  color: var(--text-primary-light);
}

.sort-icon {
  width: 20px;
  height: 20px;
  color: var(--accent-blue);
}

.btn-close {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--bg-record-hover);
  border: 1px solid var(--border-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

:global(:root:not(.dark)) .btn-close {
  background: var(--bg-record-hover-light);
  border-color: var(--border-tertiary-light);
  color: var(--text-secondary-light);
}

.btn-close:hover {
  background: var(--danger-bg);
  border-color: var(--danger-light);
  color: var(--danger-light);
}

.btn-close svg {
  width: 18px;
  height: 18px;
}

.sort-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.sort-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem;
  background: var(--bg-record);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  transition: all 0.2s;
}

:global(:root:not(.dark)) .sort-row {
  background: var(--bg-record-light);
  border-color: var(--border-color-light);
}

.sort-row:hover {
  background: var(--bg-record-hover);
  border-color: var(--border-tertiary);
}

:global(:root:not(.dark)) .sort-row:hover {
  background: var(--bg-record-hover-light);
  border-color: var(--border-tertiary-light);
}

.sort-priority {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
}

.priority-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--accent-blue);
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sort-field {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.field-icon {
  width: 16px;
  height: 16px;
  color: var(--text-muted);
  flex-shrink: 0;
}

:global(:root:not(.dark)) .field-icon {
  color: var(--text-muted-light);
}

.field-select {
  flex: 1;
  height: 32px;
  padding: 0 0.5rem;
  background: var(--bg-input);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all 0.2s;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%238c8c8c'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.5rem center;
  background-size: 16px;
  padding-right: 2rem;
}

:global(:root:not(.dark)) .field-select {
  background: var(--bg-input-light);
  color: var(--text-secondary-light);
  border-color: var(--border-color-light);
}

.field-select:hover {
  border-color: var(--accent-blue);
}

.field-select:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px var(--alpha-focus-ring);
}

.sort-direction {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100px;
}

.direction-select {
  flex: 1;
  height: 32px;
  padding: 0 0.5rem;
  background: var(--bg-input);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all 0.2s;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%238c8c8c'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.5rem center;
  background-size: 16px;
  padding-right: 2rem;
}

:global(:root:not(.dark)) .direction-select {
  background: var(--bg-input-light);
  color: var(--text-secondary-light);
  border-color: var(--border-color-light);
}

.direction-select:hover {
  border-color: var(--accent-blue);
}

.direction-select:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px var(--alpha-focus-ring);
}

.direction-icon {
  width: 14px;
  height: 14px;
  color: var(--text-muted);
  transition: transform 0.2s;
}

:global(:root:not(.dark)) .direction-icon {
  color: var(--text-muted-light);
}

.direction-icon.icon-asc {
  transform: rotate(0deg);
}

.direction-icon.icon-desc {
  transform: rotate(180deg);
}

.sort-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.btn-move {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

:global(:root:not(.dark)) .btn-move {
  background: var(--bg-input-light);
  border-color: var(--border-color-light);
  color: var(--text-secondary-light);
}

.btn-move:hover:not(:disabled) {
  background: var(--bg-record-hover);
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

:global(:root:not(.dark)) .btn-move:hover:not(:disabled) {
  background: var(--bg-record-hover-light);
}

.btn-move:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.btn-move svg {
  width: 14px;
  height: 14px;
}

.btn-remove {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: var(--danger-bg);
  border: 1px solid var(--danger-light);
  color: var(--danger-light);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.btn-remove:hover:not(:disabled) {
  background: var(--danger);
  border-color: var(--danger);
  color: white;
}

.btn-remove:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.btn-remove svg {
  width: 14px;
  height: 14px;
}

.btn-add {
  width: 100%;
  padding: 0.625rem 1rem;
  background: transparent;
  color: var(--accent-blue);
  border: 1px dashed var(--accent-blue);
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-add:hover {
  background: var(--accent-blue);
  color: white;
  border-style: solid;
}

.btn-add svg {
  width: 16px;
  height: 16px;
}

.sort-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  border-top: 1px solid var(--border-color);
}

:global(:root:not(.dark)) .sort-footer {
  border-color: var(--border-color-light);
}

.btn-reset {
  flex: 1;
  padding: 0.625rem 1rem;
  background: var(--bg-record-hover);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

:global(:root:not(.dark)) .btn-reset {
  background: var(--bg-record-hover-light);
  color: var(--text-secondary-light);
  border-color: var(--border-color-light);
}

.btn-reset:hover {
  background: var(--bg-hover);
  border-color: var(--text-muted);
}

:global(:root:not(.dark)) .btn-reset:hover {
  background: var(--bg-main-light);
  border-color: var(--text-disabled-light);
}

.btn-reset svg {
  width: 16px;
  height: 16px;
}

.btn-apply {
  flex: 1;
  padding: 0.625rem 1rem;
  background: var(--accent-blue);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-apply:hover {
  background: var(--accent-blue-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

.btn-apply:active {
  transform: translateY(0);
}

/* 滚动条样式 */
.sort-content::-webkit-scrollbar {
  width: 8px;
}

.sort-content::-webkit-scrollbar-track {
  background: var(--bg-card);
}

:global(:root:not(.dark)) .sort-content::-webkit-scrollbar-track {
  background: var(--bg-card-light);
}

.sort-content::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

:global(:root:not(.dark)) .sort-content::-webkit-scrollbar-thumb {
  background: var(--border-color-light);
}

.sort-content::-webkit-scrollbar-thumb:hover {
  background: var(--border-hover);
}

:global(:root:not(.dark)) .sort-content::-webkit-scrollbar-thumb:hover {
  background: var(--border-hover-light);
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>