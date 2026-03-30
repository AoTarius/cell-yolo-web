<template>
  <Transition name="fade">
    <div
      v-if="aiStore.isChatOpen"
      class="fixed inset-0 z-50"
      @click.self="closeChat"
    >
      <!-- 背景遮罩 -->
      <div class="ai-dialog-overlay"></div>

      <!-- 对话框主体 -->
      <div class="ai-dialog-container">
        <!-- 顶部 -->
        <ChatHeader />

        <!-- 消息区域 -->
        <div class="ai-messages-area">
          <div class="ai-messages-wrapper">
            <MessageList />
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="ai-input-area">
          <div class="ai-input-wrapper">
            <ChatInput />
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { useAIStore } from '@/stores/aiStore'
import ChatHeader from '@/components/ai/ChatHeader.vue'
import MessageList from '@/components/ai/MessageList.vue'
import ChatInput from '@/components/ai/ChatInput.vue'

const aiStore = useAIStore()

const closeChat = () => {
  aiStore.closeChat()
}
</script>

<style scoped>
/* 背景遮罩 */
.ai-dialog-overlay {
  position: absolute;
  inset: 0;
  backdrop-filter: blur(4px);
  background: var(--bg-overlay);
}

/* 对话框容器 */
.ai-dialog-container {
  position: absolute;
  inset: 2rem;
  border-radius: 0.75rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-xl);
  background: var(--ai-dialog-bg);
}

/* 消息区域 */
.ai-messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.ai-messages-wrapper {
  max-width: 64rem;
  margin: 0 auto;
}

/* 输入区域 */
.ai-input-area {
  padding: 1rem;
  border-top: 1px solid var(--ai-header-border);
  background: var(--ai-header-bg);
}

.ai-input-wrapper {
  max-width: 64rem;
  margin: 0 auto;
}

/* 淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>