import { ref } from 'vue'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface ToastItem {
  id: string
  type: ToastType
  message: string
  duration?: number
}

// 全局 Toast 状态
const toasts = ref<ToastItem[]>([])

// 显示 Toast
export function showToast(message: string, type: ToastType = 'info', duration: number = 3000) {
  const id = Date.now().toString()
  toasts.value.push({
    id,
    type,
    message,
    duration
  })

  // 自动移除
  if (duration > 0) {
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  return id
}

// 移除 Toast
export function removeToast(id: string) {
  const index = toasts.value.findIndex(t => t.id === id)
  if (index > -1) {
    toasts.value.splice(index, 1)
  }
}

// 获取 Toast 列表
export function useToast() {
  return {
    toasts,
    showToast,
    removeToast
  }
}