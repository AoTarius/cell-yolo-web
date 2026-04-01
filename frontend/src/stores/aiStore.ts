import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ChatMessage {
  id: string | 'streaming'
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface AIConfigStatus {
  configured: boolean
  message: string
  checked: boolean
}

export const useAIStore = defineStore('ai', () => {
  // 对话框状态
  const isChatOpen = ref(false)

  // 对话状态
  const currentRole = ref<string>('cell-analyst')
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)

  // API 配置状态
  const apiConfigStatus = ref<AIConfigStatus>({
    configured: false,
    message: '',
    checked: false
  })

  // 对话操作
  const openChat = () => {
    isChatOpen.value = true
  }

  const closeChat = () => {
    isChatOpen.value = false
  }

  const selectRole = (roleId: string) => {
    currentRole.value = roleId
  }

  const addMessage = (message: ChatMessage) => {
    messages.value.push(message)
  }

  const updateMessage = (id: string, content: string) => {
    const msg = messages.value.find(m => m.id === id)
    if (msg) {
      msg.content = content
    }
  }

  const clearMessages = () => {
    messages.value = []
  }

  const setApiConfigStatus = (status: Partial<AIConfigStatus>) => {
    apiConfigStatus.value = { ...apiConfigStatus.value, ...status }
  }

  return {
    isChatOpen,
    currentRole,
    messages,
    isLoading,
    apiConfigStatus,
    openChat,
    closeChat,
    selectRole,
    addMessage,
    updateMessage,
    clearMessages,
    setApiConfigStatus
  }
})