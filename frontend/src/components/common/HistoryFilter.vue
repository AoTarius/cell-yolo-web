<script setup lang="ts">
import { ref, computed } from 'vue'
import '@/assets/styles/colors.css'

export interface FilterCondition {
  id: string
  field: FilterField
  operator: FilterOperator
  value: string | string[]
  enabled: boolean
}

export type FilterField = 'status' | 'createTime' | 'modelType' | 'fileName' | 'cellCount'
export type FilterOperator = 'equals' | 'notEquals' | 'contains' | 'notContains' | 'greaterThan' | 'lessThan' | 'greaterThanOrEqual' | 'lessThanOrEqual' | 'between'

interface Props {
  visible: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'filter', conditions: FilterCondition[]): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 筛选条件列表
const filterConditions = ref<FilterCondition[]>([
  {
    id: '1',
    field: 'fileName',
    operator: 'contains',
    value: '',
    enabled: false
  },
  {
    id: '2',
    field: 'status',
    operator: 'equals',
    value: '',
    enabled: false
  },
  {
    id: '3',
    field: 'createTime',
    operator: 'equals',
    value: '',
    enabled: false
  },
  {
    id: '4',
    field: 'modelType',
    operator: 'equals',
    value: '',
    enabled: false
  },
  {
    id: '5',
    field: 'cellCount',
    operator: 'equals',
    value: '',
    enabled: false
  }
])

// 字段定义
const fieldDefinitions = {
  fileName: {
    label: '文件名',
    icon: 'fa-file-video',
    operators: ['contains', 'notContains']
  },
  status: {
    label: '状态',
    icon: 'fa-circle-check',
    operators: ['equals', 'notEquals']
  },
  createTime: {
    label: '创建时间',
    icon: 'fa-calendar',
    operators: ['equals', 'notEquals', 'greaterThan', 'lessThan', 'greaterThanOrEqual', 'lessThanOrEqual', 'between']
  },
  modelType: {
    label: '模型类型',
    icon: 'fa-microchip',
    operators: ['equals', 'notEquals']
  },
  cellCount: {
    label: '细胞数量',
    icon: 'fa-dna',
    operators: ['equals', 'notEquals', 'greaterThan', 'lessThan', 'greaterThanOrEqual', 'lessThanOrEqual', 'between']
  }
}

// 操作符定义
const operatorDefinitions = {
  equals: { label: '等于' },
  notEquals: { label: '不等于' },
  contains: { label: '包含' },
  notContains: { label: '不包含' },
  greaterThan: { label: '大于' },
  lessThan: { label: '小于' },
  greaterThanOrEqual: { label: '大于等于' },
  lessThanOrEqual: { label: '小于等于' },
  between: { label: '介于' }
}

// 状态选项
const statusOptions = [
  { value: 'completed', label: '已完成' },
  { value: 'processing', label: '分析中' },
  { value: 'failed', label: '失败' },
  { value: 'pending', label: '等待中' }
]

// 模型类型选项
const modelTypeOptions = [
  { value: 'yolov8s-seg', label: 'YOLOv8s-seg' },
  { value: 'custom', label: '自定义模型' }
]

// 关闭筛选器
function closeFilter() {
  emit('update:visible', false)
}

// 切换条件启用状态
function toggleCondition(condition: FilterCondition) {
  condition.enabled = !condition.enabled
}

// 应用筛选
function applyFilter() {
  const enabledConditions = filterConditions.value.filter(c => c.enabled && c.value !== '')
  emit('filter', enabledConditions)
  closeFilter()
}

// 重置筛选
function resetFilter() {
  filterConditions.value.forEach(condition => {
    condition.enabled = false
    condition.value = ''
    // 重置为默认操作符
    switch (condition.field) {
      case 'fileName':
        condition.operator = 'contains'
        break
      case 'createTime':
      case 'cellCount':
        condition.operator = 'equals'
        break
      default:
        condition.operator = 'equals'
    }
  })
  emit('filter', [])
}

// 获取字段的操作符选项
function getOperatorsForField(field: FilterField): FilterOperator[] {
  return fieldDefinitions[field].operators as FilterOperator[]
}

// 获取值输入类型
function getValueInputType(field: FilterField): string {
  switch (field) {
    case 'createTime':
      return 'date'
    case 'cellCount':
      return 'number'
    default:
      return 'text'
  }
}

// 判断是否需要选择器
function needsSelector(field: FilterField): boolean {
  return field === 'status' || field === 'modelType'
}

// 获取选择器选项
function getSelectorOptions(field: FilterField) {
  switch (field) {
    case 'status':
      return statusOptions
    case 'modelType':
      return modelTypeOptions
    default:
      return []
  }
}

// 判断是否需要日期选择器
function needsDatePicker(field: FilterField): boolean {
  return field === 'createTime'
}

// 判断是否需要数字输入
function needsNumberInput(field: FilterField): boolean {
  return field === 'cellCount'
}

// 判断是否需要区间输入（介于）
function needsRangeInput(operator: FilterOperator): boolean {
  return operator === 'between'
}

// 处理区间值变化
function handleRangeValueChange(condition: FilterCondition, index: number, newValue: string) {
  if (!Array.isArray(condition.value)) {
    condition.value = ['', '']
  }
  ;(condition.value as string[])[index] = newValue
}
</script>

<template>
  <Transition name="fade">
    <div v-if="visible" class="filter-overlay" @click="closeFilter">
      <div class="filter-modal" @click.stop>
        <div class="filter-header">
          <h3 class="filter-title">
            <svg
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
              class="filter-icon"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
              ></path>
            </svg>
            筛选条件
          </h3>
          <button class="btn-close" @click="closeFilter" title="关闭">
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

        <div class="filter-content">
          <div
            v-for="condition in filterConditions"
            :key="condition.id"
            class="filter-row"
            :class="{ disabled: !condition.enabled }"
          >
            <!-- 启用/禁用复选框 -->
            <div class="filter-checkbox">
              <input
                type="checkbox"
                :id="`enable-${condition.id}`"
                v-model="condition.enabled"
                class="checkbox-input"
              />
              <label :for="`enable-${condition.id}`" class="checkbox-label">
                <svg
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                  class="field-icon"
                >
                  <path
                    v-if="condition.field === 'fileName'"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                  ></path>
                  <path
                    v-else-if="condition.field === 'status'"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  ></path>
                  <path
                    v-else-if="condition.field === 'createTime'"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                  ></path>
                  <path
                    v-else-if="condition.field === 'modelType'"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
                  ></path>
                  <path
                    v-else-if="condition.field === 'cellCount'"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"
                  ></path>
                </svg>
              </label>
            </div>

            <!-- 字段标签 -->
            <div class="filter-field-label">
              {{ fieldDefinitions[condition.field].label }}
            </div>

            <!-- 操作符选择 -->
            <div class="filter-operator">
              <select
                v-model="condition.operator"
                class="operator-select"
                :disabled="!condition.enabled"
              >
                <option
                  v-for="op in getOperatorsForField(condition.field)"
                  :key="op"
                  :value="op"
                >
                  {{ operatorDefinitions[op].label }}
                </option>
              </select>
            </div>

            <!-- 值输入 -->
            <div class="filter-value">
              <!-- 选择器（状态、模型类型） -->
              <select
                v-if="needsSelector(condition.field)"
                v-model="condition.value"
                class="value-select"
                :disabled="!condition.enabled"
              >
                <option value="">请选择</option>
                <option
                  v-for="option in getSelectorOptions(condition.field)"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>

              <!-- 日期选择器 -->
              <input
                v-else-if="needsDatePicker(condition.field)"
                v-if="!needsRangeInput(condition.operator)"
                v-model="condition.value"
                type="date"
                class="value-input"
                :disabled="!condition.enabled"
              />

              <!-- 日期区间 -->
              <div
                v-else-if="needsDatePicker(condition.field) && needsRangeInput(condition.operator)"
                class="range-inputs"
              >
                <input
                  :value="(condition.value as string[])[0] || ''"
                  @input="handleRangeValueChange(condition, 0, ($event.target as HTMLInputElement).value)"
                  type="date"
                  class="value-input range-start"
                  :disabled="!condition.enabled"
                  placeholder="开始日期"
                />
                <span class="range-separator">至</span>
                <input
                  :value="(condition.value as string[])[1] || ''"
                  @input="handleRangeValueChange(condition, 1, ($event.target as HTMLInputElement).value)"
                  type="date"
                  class="value-input range-end"
                  :disabled="!condition.enabled"
                  placeholder="结束日期"
                />
              </div>

              <!-- 数字输入 -->
              <input
                v-else-if="needsNumberInput(condition.field)"
                v-if="!needsRangeInput(condition.operator)"
                v-model="condition.value"
                type="number"
                class="value-input"
                :disabled="!condition.enabled"
                placeholder="请输入数字"
              />

              <!-- 数字区间 -->
              <div
                v-else-if="needsNumberInput(condition.field) && needsRangeInput(condition.operator)"
                class="range-inputs"
              >
                <input
                  :value="(condition.value as string[])[0] || ''"
                  @input="handleRangeValueChange(condition, 0, ($event.target as HTMLInputElement).value)"
                  type="number"
                  class="value-input range-start"
                  :disabled="!condition.enabled"
                  placeholder="最小值"
                />
                <span class="range-separator">至</span>
                <input
                  :value="(condition.value as string[])[1] || ''"
                  @input="handleRangeValueChange(condition, 1, ($event.target as HTMLInputElement).value)"
                  type="number"
                  class="value-input range-end"
                  :disabled="!condition.enabled"
                  placeholder="最大值"
                />
              </div>

              <!-- 文本输入 -->
              <input
                v-else
                v-model="condition.value"
                type="text"
                class="value-input"
                :disabled="!condition.enabled"
                placeholder="请输入"
              />
            </div>
          </div>
        </div>

        <div class="filter-footer">
          <button class="btn-reset" @click="resetFilter">
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
          <button class="btn-apply" @click="applyFilter">
            应用筛选
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.filter-overlay {
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

.filter-modal {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  width: 90%;
  max-width: 550px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

:global(:root:not(.dark)) .filter-modal {
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

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

:global(:root:not(.dark)) .filter-header {
  border-color: var(--border-color-light);
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

:global(:root:not(.dark)) .filter-title {
  color: var(--text-primary-light);
}

.filter-icon {
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

.filter-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--bg-record);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  transition: all 0.2s;
}

:global(:root:not(.dark)) .filter-row {
  background: var(--bg-record-light);
  border-color: var(--border-color-light);
}

.filter-row:hover:not(.disabled) {
  background: var(--bg-record-hover);
  border-color: var(--border-tertiary);
}

:global(:root:not(.dark)) .filter-row:hover:not(.disabled) {
  background: var(--bg-record-hover-light);
  border-color: var(--border-tertiary-light);
}

.filter-row.disabled {
  opacity: 0.5;
}

.filter-checkbox {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.checkbox-input {
  display: none;
}

.checkbox-label {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
  border: 2px solid var(--border-tertiary);
  background: var(--bg-input);
}

:global(:root:not(.dark)) .checkbox-label {
  border-color: var(--border-tertiary-light);
  background: var(--bg-input-light);
}

.checkbox-input:checked + .checkbox-label {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
}

.checkbox-label:hover {
  border-color: var(--accent-blue);
}

.checkbox-label svg {
  width: 14px;
  height: 14px;
  color: white;
  opacity: 0;
  transition: opacity 0.2s;
}

.checkbox-input:checked + .checkbox-label svg {
  opacity: 1;
}

.field-icon {
  width: 16px;
  height: 16px;
}

.filter-field-label {
  width: 60px;
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 500;
  flex-shrink: 0;
  user-select: none;
  -webkit-user-select: none; /* Safari/Chrome */
}

:global(:root:not(.dark)) .filter-field-label {
  color: var(--text-muted-light);
}

.filter-operator {
  width: 84px;
  flex-shrink: 0;
}

.operator-select {
  width: 100%;
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

:global(:root:not(.dark)) .operator-select {
  background: var(--bg-input-light);
  color: var(--text-secondary-light);
  border-color: var(--border-color-light);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%238c8c8c'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
}

.operator-select:hover:not(:disabled) {
  border-color: var(--accent-blue);
}

.operator-select:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px var(--alpha-focus-ring);
}

.operator-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.filter-value {
  flex: 1;
  min-width: 0;
}

.value-select,
.value-input {
  width: 100%;
  height: 32px;
  padding: 0 0.75rem;
  background: var(--bg-input);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 0.8125rem;
  transition: all 0.2s;
}

:global(:root:not(.dark)) .value-select,
:global(:root:not(.dark)) .value-input {
  background: var(--bg-input-light);
  color: var(--text-secondary-light);
  border-color: var(--border-color-light);
}

.value-select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%238c8c8c'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.5rem center;
  background-size: 16px;
  padding-right: 2rem;
}

:global(:root:not(.dark)) .value-select {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%238c8c8c'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
}

.value-select:hover:not(:disabled),
.value-input:hover:not(:disabled) {
  border-color: var(--accent-blue);
}

.value-select:focus,
.value-input:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px var(--alpha-focus-ring);
}

.value-select:disabled,
.value-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.range-inputs {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.range-start,
.range-end {
  flex: 1;
}

.range-separator {
  font-size: 0.8125rem;
  color: var(--text-muted);
  white-space: nowrap;
}

:global(:root:not(.dark)) .range-separator {
  color: var(--text-muted-light);
}

.filter-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  border-top: 1px solid var(--border-color);
}

:global(:root:not(.dark)) .filter-footer {
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
.filter-content::-webkit-scrollbar {
  width: 8px;
}

.filter-content::-webkit-scrollbar-track {
  background: var(--bg-card);
}

:global(:root:not(.dark)) .filter-content::-webkit-scrollbar-track {
  background: var(--bg-card-light);
}

.filter-content::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

:global(:root:not(.dark)) .filter-content::-webkit-scrollbar-thumb {
  background: var(--border-color-light);
}

.filter-content::-webkit-scrollbar-thumb:hover {
  background: var(--border-hover);
}

:global(:root:not(.dark)) .filter-content::-webkit-scrollbar-thumb:hover {
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