<template>
  <Transition name="fade">
    <div
      v-if="aiStore.isChatOpen"
      class="fixed inset-0 z-50"
      @click.self="closeChat"
    >
      <!-- 背景遮罩 -->
      <div class="absolute inset-0 backdrop-blur-sm" style="background: var(--bg-overlay)"></div>

      <!-- 对话框主体 -->
      <div class="absolute inset-4 rounded-xl overflow-hidden flex flex-col shadow-2xl" style="background: var(--ai-dialog-bg)">
        <!-- 顶部 -->
        <ChatHeader />

        <!-- 消息区域 -->
        <div class="flex-1 overflow-y-auto p-4">
          <div class="max-w-4xl mx-auto">
            <MessageList />
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="p-4" style="border-top: 1px solid var(--ai-header-border); background: var(--ai-header-bg)">
          <div class="max-w-4xl mx-auto">
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
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>