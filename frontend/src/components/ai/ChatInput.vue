<template>
  <div class="flex gap-3 items-end">
    <!-- 输入框 -->
    <div class="flex-1 relative">
      <textarea
        ref="textareaRef"
        v-model="inputContent"
        @keydown="handleKeyDown"
        @input="autoResize"
        placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
        class="w-full px-4 py-3 rounded-xl border resize-none transition-all"
        :style="{
          height: computedHeight,
          background: 'var(--ai-input-bg)',
          color: 'var(--ai-input-text)',
          border: '1px solid var(--ai-input-border)',
          outline: 'none'
        }"
        :disabled="aiStore.isLoading"
        rows="1"
      ></textarea>
      
      <!-- 字数统计 -->
      <div
        class="absolute bottom-2 right-2 text-xs transition-colors"
        :style="{ color: inputContent.length > 2800 ? 'var(--danger-light)' : 'var(--text-muted)' }"
      >
        {{ inputContent.length }} / 3000
      </div>
    </div>
    
    <!-- 发送/停止按钮 -->
    <button
      @click="handleSend"
      :disabled="!canSend"
      class="px-6 py-3 rounded-xl font-medium transition-all flex items-center justify-center min-w-[60px]"
      :style="{
        background: aiStore.isLoading ? 'var(--danger)' : 'var(--accent-blue)',
        color: 'white',
        opacity: canSend ? 1 : 0.5,
        cursor: canSend ? 'pointer' : 'not-allowed'
      }"
      :title="aiStore.isLoading ? '停止生成' : '发送消息'"
    >
      <template v-if="aiStore.isLoading">
        <Square :size="20" />
      </template>
      <template v-else>
        <Send :size="20" />
      </template>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Send, Square } from 'lucide-vue-next'
import { useAIStore } from '@/stores/aiStore'
import { sendChatMessageStream } from '@/api/aiApi'

const aiStore = useAIStore()
const textareaRef = ref<HTMLTextAreaElement>()
const inputContent = ref('')
const textareaHeight = ref(50)
const minRows = 1
const maxRows = 5
const rowHeight = 50

// 计算高度（带单位）
const computedHeight = computed(() => `${textareaHeight.value}px`)

// 自动调整高度
const autoResize = () => {
  const textarea = textareaRef.value
  if (!textarea) return
  
  const newHeight = Math.min(
    Math.max(textarea.scrollHeight, rowHeight),
    rowHeight * maxRows
  )
  textareaHeight.value = newHeight
}

// 键盘事件
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// 是否可以发送
const canSend = computed(() => {
  return inputContent.value.trim().length > 0 && 
         inputContent.value.length <= 3000 &&
         !aiStore.isLoading
})

// 发送消息
const handleSend = async () => {
  if (!canSend.value) return
  
  const content = inputContent.value.trim()
  inputContent.value = ''
  textareaHeight.value = rowHeight
  
  // 添加用户消息
  aiStore.addMessage({
    id: Date.now().toString(),
    role: 'user',
    content,
    timestamp: new Date()
  })
  
  // 添加临时AI消息
  aiStore.addMessage({
    id: 'streaming',
    role: 'assistant',
    content: '',
    timestamp: new Date()
  })
  
  aiStore.isLoading = true
  
  try {
    // 流式获取AI回复
    const finalContent = await sendChatMessageStream(
      content,
      aiStore.currentRole,
      (partialContent) => {
        // 实时更新消息
        aiStore.updateMessage('streaming', partialContent)
      }
    )
    
    // 替换临时消息为正式消息
    const messages = aiStore.messages
    const streamingIndex = messages.findIndex(m => m.id === 'streaming')
    if (streamingIndex !== -1) {
      messages[streamingIndex] = {
        id: Date.now().toString(),
        role: 'assistant',
        content: finalContent,
        timestamp: new Date()
      }
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    // 显示错误消息
    aiStore.updateMessage('streaming', '抱歉，发送消息时出错了。请检查网络连接或稍后重试。')
  } finally {
    aiStore.isLoading = false
  }
}

// 重置高度
watch(inputContent, () => {
  if (inputContent.value === '') {
    textareaHeight.value = rowHeight
  }
})
</script>