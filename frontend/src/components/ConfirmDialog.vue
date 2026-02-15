<script setup lang="ts">
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
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
}

.dialog-container {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  max-width: 440px;
  width: 100%;
  overflow: hidden;
  transition: all 0.3s ease;
}

:global(:root:not(.dark)) .dialog-container {
  background: #fff;
  border-color: #e0e0e0;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #333;
}

:global(:root:not(.dark)) .dialog-header {
  border-bottom: 1px solid #e0e0e0;
}

.dialog-header h3 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #fff;
}

:global(:root:not(.dark)) .dialog-header h3 {
  color: #333;
}

.btn-close {
  background: transparent;
  border: none;
  color: #8b949e;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

:global(:root:not(.dark)) .btn-close {
  color: #666;
}

.btn-close:hover {
  background: rgba(139, 148, 158, 0.1);
  color: #c9d1d9;
}

:global(:root:not(.dark)) .btn-close:hover {
  background: rgba(102, 102, 102, 0.1);
  color: #333;
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
  background: rgba(248, 113, 113, 0.1);
  color: #f87171;
}

.icon-warning {
  background: rgba(251, 191, 36, 0.1);
  color: #fbbf24;
}

.icon-info {
  background: rgba(88, 166, 255, 0.1);
  color: #58a6ff;
}

.dialog-message {
  flex: 1;
  margin: 0;
  font-size: 1rem;
  line-height: 1.5;
  color: #c9d1d9;
}

:global(:root:not(.dark)) .dialog-message {
  color: #333;
}

.dialog-footer {
  padding: 1rem 1.5rem;
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  border-top: 1px solid #333;
}

:global(:root:not(.dark)) .dialog-footer {
  border-top: 1px solid #e0e0e0;
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
  color: #c9d1d9;
  border: 1px solid #30363d;
}

:global(:root:not(.dark)) .btn-cancel {
  color: #333;
  border-color: #ccc;
}

.btn-cancel:hover {
  background: rgba(48, 54, 61, 0.1);
  border-color: #8b949e;
}

:global(:root:not(.dark)) .btn-cancel:hover {
  background: rgba(204, 204, 204, 0.1);
  border-color: #999;
}

.btn-danger {
  background: #dc2626;
  color: white;
}

.btn-danger:hover {
  background: #ef4444;
}

.btn-warning {
  background: #d97706;
  color: white;
}

.btn-warning:hover {
  background: #f59e0b;
}

.btn-info {
  background: #007acc;
  color: white;
}

.btn-info:hover {
  background: #005a9e;
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