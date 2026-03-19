<script setup lang="ts">
import '@/assets/styles/colors.css'
import { computed, watch, ref } from 'vue'

interface Props {
  visible: boolean
  modelPath?: string
  outputPath?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelPath: '',
  outputPath: ''
})

const emit = defineEmits<{
  'update:visible': [value: boolean]
  save: [modelPath: string, outputPath: string]
  'browse-model': []
  'browse-output': []
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (value: boolean) => emit('update:visible', value)
})

const localModelPath = ref(props.modelPath)
const localOutputPath = ref(props.outputPath)

// 监听 props 变化，更新本地状态
watch(() => props.visible, (visible) => {
  if (visible) {
    localModelPath.value = props.modelPath
    localOutputPath.value = props.outputPath
  }
})

function handleSave() {
  if (localModelPath.value.trim() && localOutputPath.value.trim()) {
    emit('save', localModelPath.value.trim(), localOutputPath.value.trim())
    dialogVisible.value = false
  }
}

function handleCancel() {
  dialogVisible.value = false
}

// ESC 键关闭
function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.visible) {
    handleCancel()
  }
}

// 监听 visible 变化，添加/移除键盘事件监听
watch(() => props.visible, (visible) => {
  if (visible) {
    document.addEventListener('keydown', handleKeydown)
  } else {
    document.removeEventListener('keydown', handleKeydown)
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div v-if="visible" class="dialog-overlay" @click.self="handleCancel">
        <div class="dialog-container">
          <div class="dialog-header">
            <h3>设置</h3>
            <button class="btn-close" @click="handleCancel" aria-label="关闭">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>

          <div class="dialog-body">
            <!-- 模型存储路径 -->
            <div class="setting-item">
              <label class="setting-label">
                <span class="label-text">本地模型存储路径</span>
              </label>
              <div class="path-input-group">
                <input
                  v-model="localModelPath"
                  type="text"
                  class="path-input"
                  placeholder="请输入模型存储路径"
                />
                <button class="btn-browse" @click="$emit('browse-model')" title="浏览文件夹">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>
                  </svg>
                  浏览
                </button>
              </div>
            </div>

            <!-- 任务存储路径 -->
            <div class="setting-item">
              <label class="setting-label">
                <span class="label-text">本地任务存储路径</span>
              </label>
              <div class="path-input-group">
                <input
                  v-model="localOutputPath"
                  type="text"
                  class="path-input"
                  placeholder="请输入任务存储路径"
                />
                <button class="btn-browse" @click="$emit('browse-output')" title="浏览文件夹">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>
                  </svg>
                  浏览
                </button>
              </div>
            </div>
          </div>

          <div class="dialog-footer">
            <button class="btn btn-cancel" @click="handleCancel">
              取消
            </button>
            <button class="btn btn-save" @click="handleSave">
              保存
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: var(--bg-overlay);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
}

.dialog-container {
  background: var(--bg-sidebar);
  border: 1px solid var(--border-secondary);
  border-radius: 12px;
  box-shadow: var(--shadow-xl);
  max-width: 540px;
  width: 100%;
  overflow: hidden;
  transition: all 0.3s ease;
}

:global(:root:not(.dark)) .dialog-container {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
  box-shadow: var(--shadow-xl-light);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-secondary);
}

:global(:root:not(.dark)) .dialog-header {
  border-bottom: 1px solid var(--border-color-light);
}

.dialog-header h3 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
}

:global(:root:not(.dark)) .dialog-header h3 {
  color: var(--text-primary-light);
}

.btn-close {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

:global(:root:not(.dark)) .btn-close {
  color: var(--text-muted-light);
}

.btn-close:hover {
  background: var(--alpha-hover);
  color: var(--text-secondary);
}

:global(:root:not(.dark)) .btn-close:hover {
  background: var(--alpha-hover-light);
  color: var(--text-primary-light);
}

.btn-close svg {
  width: 20px;
  height: 20px;
}

.dialog-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.label-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}

:global(:root:not(.dark)) .label-text {
  color: var(--text-primary-light);
}

.path-input-group {
  display: flex;
  gap: 0.5rem;
}

.path-input {
  flex: 1;
  padding: 0.625rem 0.875rem;
  background: var(--bg-record);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 0.875rem;
  color: var(--text-primary);
  transition: all 0.2s;
}

:global(:root:not(.dark)) .path-input {
  background: var(--bg-input-light);
  border-color: var(--border-color-light);
  color: var(--text-primary-light);
}

.path-input::placeholder {
  color: var(--text-muted);
}

:global(:root:not(.dark)) .path-input::placeholder {
  color: var(--text-muted-light);
}

.path-input:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px var(--alpha-focus);
}

:global(:root:not(.dark)) .path-input:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px var(--alpha-focus-light);
}

.btn-browse {
  padding: 0.625rem 1rem;
  background: var(--bg-record-hover);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  white-space: nowrap;
}

:global(:root:not(.dark)) .btn-browse {
  background: var(--bg-button-light);
  border-color: var(--border-color-light);
  color: var(--text-primary-light);
}

.btn-browse:hover {
  background: var(--bg-hover);
  border-color: var(--border-hover);
}

:global(:root:not(.dark)) .btn-browse:hover {
  background: var(--bg-hover-light);
  border-color: var(--border-hover-light);
}

.btn-browse svg {
  width: 16px;
  height: 16px;
}

.dialog-footer {
  padding: 1rem 1.5rem;
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  border-top: 1px solid var(--border-secondary);
}

:global(:root:not(.dark)) .dialog-footer {
  border-top: 1px solid var(--border-color-light);
}

.btn {
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-cancel {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

:global(:root:not(.dark)) .btn-cancel {
  color: var(--text-primary-light);
  border-color: var(--border-color-light);
}

.btn-cancel:hover {
  background: var(--alpha-hover);
  border-color: var(--text-muted);
}

:global(:root:not(.dark)) .btn-cancel:hover {
  background: var(--alpha-hover-light);
  border-color: var(--text-disabled-light);
}

.btn-save {
  background: var(--accent-info);
  color: white;
}

.btn-save:hover {
  background: var(--accent-info-hover);
}

/* 动画效果 */
.dialog-enter-active,
.dialog-leave-active {
  transition: all 0.3s ease;
}

.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
}

.dialog-enter-from .dialog-container,
.dialog-leave-to .dialog-container {
  transform: scale(0.95) translateY(-10px);
}

.dialog-enter-to .dialog-container,
.dialog-leave-from .dialog-container {
  transform: scale(1) translateY(0);
}
</style>