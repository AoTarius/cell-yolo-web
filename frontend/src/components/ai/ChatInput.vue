<template>
  <div class="ai-input-container">
    <!-- 输入框 -->
    <div class="ai-input-wrapper">
      <textarea
        ref="textareaRef"
        v-model="inputContent"
        @keydown="handleKeyDown"
        @input="autoResize"
        @focus="isFocused = true"
        @blur="isFocused = false"
        placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
        class="ai-textarea"
        :class="{ 'ai-textarea-focused': isFocused }"
        :style="{ height: computedHeight }"
        :disabled="aiStore.isLoading"
        rows="1"
      ></textarea>

      <!-- 字数统计 -->
      <div
        class="ai-char-count"
        :class="{ 'ai-char-count-warning': inputContent.length > 2800 }"
      >
        {{ inputContent.length }} / 3000
      </div>
    </div>

    <!-- 发送/停止按钮 -->
    <button
      @click="handleSend"
      :disabled="!canSend"
      class="ai-send-btn"
      :class="{ 'ai-send-btn-loading': aiStore.isLoading, 'ai-send-btn-disabled': !canSend }"
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
import { sendChatMessageStream, checkAIConfig } from '@/api/aiApi'
import { showToast } from '@/composables/useToast'

const aiStore = useAIStore()
const textareaRef = ref<HTMLTextAreaElement>()
const inputContent = ref('')
const textareaHeight = ref(50)
const isFocused = ref(false)
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

// 检查 API 配置
const checkApiConfiguration = async (): Promise<boolean> => {
  // 如果已经检查过且配置有效，直接返回
  if (aiStore.apiConfigStatus.checked && aiStore.apiConfigStatus.configured) {
    return true
  }

  try {
    const status = await checkAIConfig()
    aiStore.setApiConfigStatus({
      configured: status.configured,
      message: status.message,
      checked: true
    })

    if (!status.configured) {
      showToast('请设置 API 密钥后再进行对话', 'warning', 5000)
      return false
    }

    return true
  } catch (error) {
    console.error('检查 API 配置失败:', error)
    showToast('检查 API 配置失败，请稍后重试', 'error', 3000)
    return false
  }
}

// 发送消息
const handleSend = async () => {
  if (!canSend.value) return

  // 检查 API 配置
  const isConfigured = await checkApiConfiguration()
  if (!isConfigured) {
    return
  }

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

<style scoped>
.ai-input-container {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.ai-input-wrapper {
  flex: 1;
  position: relative;
}

.ai-textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 0.75rem;
  border: 1px solid var(--ai-input-border);
  background: var(--ai-input-bg);
  color: var(--ai-input-text);
  resize: none;
  transition: all 0.2s;
  outline: none;
  font-family: inherit;
}

.ai-textarea::placeholder {
  color: var(--ai-input-placeholder);
}

.ai-textarea-focused {
  border-color: var(--ai-input-focus);
}

.ai-textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ai-char-count {
  position: absolute;
  bottom: 0.5rem;
  right: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  transition: color 0.2s;
}

.ai-char-count-warning {
  color: var(--danger-light);
}

.ai-send-btn {
  padding: 0.75rem 1.5rem;
  border-radius: 0.75rem;
  font-weight: 500;
  border: none;
  background: var(--accent-blue);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 3.75rem;
  transition: all 0.2s;
}

.ai-send-btn-loading {
  background: var(--danger);
}

.ai-send-btn-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ai-send-btn:not(.ai-send-btn-disabled):hover {
  opacity: 0.9;
}
</style>