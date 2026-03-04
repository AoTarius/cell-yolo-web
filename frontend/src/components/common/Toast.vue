<script setup lang="ts">
import '@/assets/styles/colors.css'
import { useToast } from '@/composables/useToast'

const { toasts, removeToast } = useToast()

// 获取 Toast 图标
const getIcon = (type: 'success' | 'error' | 'info' | 'warning') => {
  switch (type) {
    case 'success':
      return '✓'
    case 'error':
      return '✕'
    case 'warning':
      return '⚠'
    case 'info':
      return 'ℹ'
  }
}

// 获取 Toast 颜色样式
const getToastClass = (type: 'success' | 'error' | 'info' | 'warning') => {
  const baseClass = 'toast-item'
  switch (type) {
    case 'success':
      return `${baseClass} toast-success`
    case 'error':
      return `${baseClass} toast-error`
    case 'warning':
      return `${baseClass} toast-warning`
    case 'info':
      return `${baseClass} toast-info`
  }
}
</script>

<template>
  <div class="toast-container">
    <TransitionGroup name="toast">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="getToastClass(toast.type)"
        @click="removeToast(toast.id)"
      >
        <span class="toast-icon">{{ getIcon(toast.type) }}</span>
        <span class="toast-message">{{ toast.message }}</span>
        <button class="toast-close" @click.stop="removeToast(toast.id)">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
}

.toast-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: var(--bg-toast);
  border-radius: 8px;
  box-shadow: var(--shadow-md);
  pointer-events: auto;
  min-width: 320px;
  max-width: 420px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.3s;
}

:global(:root:not(.dark)) .toast-item {
  background: var(--bg-toast-light);
  box-shadow: var(--shadow-md-light);
}

.toast-success {
  border-color: var(--success);
  background: linear-gradient(135deg, rgba(35, 134, 54, 0.1) 0%, var(--bg-toast) 100%);
}

:global(:root:not(.dark)) .toast-success {
  border-color: var(--success-light);
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, var(--bg-toast-light) 100%);
}

.toast-error {
  border-color: var(--danger);
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.1) 0%, var(--bg-toast) 100%);
}

:global(:root:not(.dark)) .toast-error {
  border-color: var(--danger-hover);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, var(--bg-toast-light) 100%);
}

.toast-warning {
  border-color: var(--warning);
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, var(--bg-toast) 100%);
}

:global(:root:not(.dark)) .toast-warning {
  border-color: var(--warning-hover);
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.1) 0%, var(--bg-toast-light) 100%);
}

.toast-info {
  border-color: var(--accent-info);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, var(--bg-toast) 100%);
}

:global(:root:not(.dark)) .toast-info {
  border-color: var(--accent-blue);
  background: linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, var(--bg-toast-light) 100%);
}

.toast-item:hover {
  transform: translateX(-4px);
  box-shadow: var(--shadow-lg);
}

:global(:root:not(.dark)) .toast-item:hover {
  box-shadow: var(--shadow-lg-light);
}

.toast-icon {
  font-size: 20px;
  font-weight: bold;
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toast-success .toast-icon {
  color: var(--success);
}

:global(:root:not(.dark)) .toast-success .toast-icon {
  color: var(--success-light);
}

.toast-error .toast-icon {
  color: var(--danger);
}

:global(:root:not(.dark)) .toast-error .toast-icon {
  color: var(--danger-hover);
}

.toast-warning .toast-icon {
  color: var(--warning);
}

:global(:root:not(.dark)) .toast-warning .toast-icon {
  color: var(--warning-hover);
}

.toast-info .toast-icon {
  color: var(--accent-info);
}

:global(:root:not(.dark)) .toast-info .toast-icon {
  color: var(--accent-blue);
}

.toast-message {
  flex: 1;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.5;
}

:global(:root:not(.dark)) .toast-message {
  color: var(--text-primary-light);
}

.toast-close {
  padding: 4px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

:global(:root:not(.dark)) .toast-close {
  color: var(--text-disabled-light);
}

.toast-close:hover {
  background: var(--alpha-hover);
  color: var(--text-secondary);
}

:global(:root:not(.dark)) .toast-close:hover {
  background: var(--alpha-hover-light);
  color: var(--text-primary-light);
}

/* 过渡动画 */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.toast-move {
  transition: transform 0.3s ease;
}
</style>