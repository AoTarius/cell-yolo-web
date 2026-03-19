<script setup lang="ts">
import '@/assets/styles/colors.css'
import { computed, watch } from 'vue'

interface Props {
  visible: boolean
  title?: string
  message?: string
  confirmText?: string
  cancelText?: string
  type?: 'danger' | 'warning' | 'info'
}

const props = withDefaults(defineProps<Props>(), {
  title: '确认操作',
  message: '确定要执行此操作吗？',
  confirmText: '确认',
  cancelText: '取消',
  type: 'info'
})

const emit = defineEmits<{
  'update:visible': [value: boolean]
  confirm: []
  cancel: []
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (value: boolean) => emit('update:visible', value)
})

function handleConfirm() {
  emit('confirm')
  dialogVisible.value = false
}

function handleCancel() {
  emit('cancel')
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
        <div class="dialog-container" :class="`dialog-${type}`">
          <div class="dialog-header">
            <h3>{{ title }}</h3>
            <button class="btn-close" @click="handleCancel" aria-label="关闭">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>

          <div class="dialog-body">
            <div v-if="type === 'danger'" class="dialog-icon icon-danger">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
              </svg>
            </div>
            <div v-else-if="type === 'warning'" class="dialog-icon icon-warning">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
              </svg>
            </div>
            <div v-else class="dialog-icon icon-info">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>

            <p class="dialog-message">{{ message }}</p>
          </div>

          <div class="dialog-footer">
            <button class="btn btn-cancel" @click="handleCancel">
              {{ cancelText }}
            </button>
            <button 
              class="btn" 
              :class="`btn-${type}`" 
              @click="handleConfirm"
            >
              {{ confirmText }}
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
  max-width: 440px;
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
  align-items: flex-start;
  gap: 1rem;
}

.dialog-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dialog-icon svg {
  width: 24px;
  height: 24px;
}

.icon-danger {
  background: var(--danger-bg);
  color: var(--danger-light);
}

.icon-warning {
  background: var(--warning-bg);
  color: var(--warning-light);
}

.icon-info {
  background: var(--alpha-focus);
  color: var(--accent-blue);
}

.dialog-message {
  flex: 1;
  margin: 0;
  font-size: 1rem;
  line-height: 1.5;
  color: var(--text-secondary);
}

:global(:root:not(.dark)) .dialog-message {
  color: var(--text-primary-light);
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

.btn-danger {
  background: var(--danger);
  color: white;
}

.btn-danger:hover {
  background: var(--danger-hover);
}

.btn-warning {
  background: var(--warning);
  color: white;
}

.btn-warning:hover {
  background: var(--warning-hover);
}

.btn-info {
  background: var(--accent-info);
  color: white;
}

.btn-info:hover {
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