import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ChatMessage {
  id: string | 'streaming'
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export const useAIStore = defineStore('ai', () => {
  // 对话框状态
  const isChatOpen = ref(false)

  // 对话状态
  const currentRole = ref<string>('cell-analyst')
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)
  
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
  
  return {
    isChatOpen,
    currentRole,
    messages,
    isLoading,
    openChat,
    closeChat,
    selectRole,
    addMessage,
    updateMessage,
    clearMessages
  }
})