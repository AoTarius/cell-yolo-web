<script setup lang="ts">
import '@/assets/styles/colors.css'
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { useAnalysisStore } from '@/stores/analysisStore'

const router = useRouter()
const { showToast } = useToast()
const analysisStore = useAnalysisStore()

// ==================== 模型对比相关 ====================
const compareTaskIdA = ref('')
const compareTaskIdB = ref('')
const isLoadingTasks = ref(false)

interface CompareTaskOption {
  task_id: string
  task_name: string
  video_name: string
  model_name: string
  total_frames: number
}

const completedTaskOptions = computed<CompareTaskOption[]>(() => {
  return analysisStore.records
    .filter((record) => record.status === 'completed' && record.task_id)
    .map((record) => ({
      task_id: record.task_id,
      task_name: record.task_name || record.task_id,
      video_name: record.video_name || '未知视频',
      model_name: record.model_name || record.result?.model_name || '未命名模型',
      total_frames: Number(record.result?.total_frames || 0),
    }))
})

const selectedTaskA = computed(() => {
  return completedTaskOptions.value.find((task) => task.task_id === compareTaskIdA.value) || null
})

const availableTaskBOptions = computed(() => {
  if (!selectedTaskA.value) return []

  return completedTaskOptions.value.filter((task) => {
    return (
      task.task_id !== selectedTaskA.value?.task_id
      && task.video_name === selectedTaskA.value?.video_name
      && task.model_name !== selectedTaskA.value?.model_name
    )
  })
})

const selectedTaskB = computed(() => {
  return availableTaskBOptions.value.find((task) => task.task_id === compareTaskIdB.value) || null
})

const canStartModelCompare = computed(() => {
  return Boolean(selectedTaskA.value && selectedTaskB.value)
})

// ==================== 模型对比函数 ====================
async function loadCompareTasks() {
  isLoadingTasks.value = true
  try {
    await analysisStore.loadHistoryTasks()
  } finally {
    isLoadingTasks.value = false
  }
}

function startModelCompare() {
  if (!canStartModelCompare.value) {
    showToast('请选择两个同视频且不同模型的任务', 'warning')
    return
  }

  const recordA = analysisStore.records.find((item) => item.task_id === compareTaskIdA.value)
  const recordB = analysisStore.records.find((item) => item.task_id === compareTaskIdB.value)

  if (!recordA || !recordB) {
    showToast('未找到所选任务，请刷新后重试', 'error')
    return
  }

  analysisStore.compareRecords = [recordA, recordB]
  router.push({
    name: 'compareResult',
    query: {
      syncFrames: '1',
      compareMode: 'model',
    },
  })
}

// 组件挂载时加载任务列表
onMounted(() => {
  loadCompareTasks()
})
</script>

<template>
  <div class="compare-card">
    <h3>模型效果对比</h3>
    <p class="compare-tip">选择同一个视频下的两个不同模型任务，进入同步帧对比。</p>

    <div class="compare-field">
      <label for="compare-task-a">任务 A</label>
      <select
        id="compare-task-a"
        v-model="compareTaskIdA"
        class="compare-select"
        :disabled="isLoadingTasks"
      >
        <option value="">请选择任务 A</option>
        <option
          v-for="task in completedTaskOptions"
          :key="task.task_id"
          :value="task.task_id"
        >
          {{ task.task_name }} | {{ task.video_name }} | {{ task.model_name }}
        </option>
      </select>
    </div>

    <div class="compare-field">
      <label for="compare-task-b">任务 B</label>
      <select
        id="compare-task-b"
        v-model="compareTaskIdB"
        class="compare-select"
        :disabled="isLoadingTasks || !selectedTaskA"
      >
        <option value="">请选择任务 B</option>
        <option
          v-for="task in availableTaskBOptions"
          :key="task.task_id"
          :value="task.task_id"
        >
          {{ task.task_name }} | {{ task.video_name }} | {{ task.model_name }}
        </option>
      </select>
    </div>

    <p v-if="selectedTaskA" class="compare-hint-text">
      当前视频：{{ selectedTaskA.video_name }}
    </p>
    <p v-if="selectedTaskA && availableTaskBOptions.length === 0" class="compare-warning-text">
      当前任务找不到可对比的"同视频不同模型"任务。
    </p>

    <button
      class="btn-start-compare"
      :disabled="isLoadingTasks || !canStartModelCompare"
      @click="startModelCompare"
    >
      {{ isLoadingTasks ? '加载任务中...' : '开始模型对比' }}
    </button>
  </div>
</template>

<style scoped>
.compare-card {
  padding: 1rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-card);
  height: 100%;
}

:global(:root:not(.dark)) .compare-card {
  border-color: var(--border-color-light);
  background: var(--bg-card-light);
}

.compare-card h3 {
  margin: 0;
  font-size: 1rem;
  color: var(--text-primary);
}

:global(:root:not(.dark)) .compare-card h3 {
  color: var(--text-primary-light);
}

.compare-tip {
  margin: 0.5rem 0 1rem 0;
  font-size: 0.875rem;
  color: var(--text-muted);
}

:global(:root:not(.dark)) .compare-tip {
  color: var(--text-muted-light);
}

.compare-field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 0.75rem;
}

.compare-field label {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

:global(:root:not(.dark)) .compare-field label {
  color: var(--text-primary-light);
}

.compare-select {
  width: 100%;
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-input);
  color: var(--text-secondary);
}

:global(:root:not(.dark)) .compare-select {
  border-color: var(--border-color-light);
  background: var(--bg-input-light);
  color: var(--text-primary-light);
}

.compare-select:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.compare-hint-text,
.compare-warning-text {
  margin: 0.25rem 0;
  font-size: 0.8rem;
}

.compare-hint-text {
  color: var(--text-muted);
}

:global(:root:not(.dark)) .compare-hint-text {
  color: var(--text-muted-light);
}

.compare-warning-text {
  color: var(--danger-light);
}

.btn-start-compare {
  margin-top: 0.75rem;
  width: 100%;
  padding: 0.65rem 0.9rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--accent-blue);
  color: #fff;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-start-compare:hover:not(:disabled) {
  background: var(--accent-blue-hover);
}

.btn-start-compare:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
</style>