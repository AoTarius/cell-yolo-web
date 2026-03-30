<template>
  <div class="flex items-center justify-between px-6 py-4" style="border-bottom: 1px solid var(--ai-header-border); background: var(--ai-header-bg)">
    <!-- 左侧：AI信息 -->
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-full flex items-center justify-center" style="background: var(--ai-assistant-avatar)">
        <Bot :size="24" style="color: white" />
      </div>
      <div>
        <h2 class="text-lg font-semibold" style="color: var(--text-primary)">AI助手</h2>
        <p class="text-sm" style="color: var(--text-muted)">细胞分析专家</p>
      </div>
    </div>

    <!-- 右侧：关闭按钮 -->
    <button
      @click="closeChat"
      class="transition-colors p-2 rounded-lg"
      style="color: var(--text-muted)"
      title="关闭对话框"
      @mouseover="$el.style.color = 'var(--text-primary)'; $el.style.background = 'var(--bg-hover)'"
      @mouseout="$el.style.color = 'var(--text-muted)'; $el.style.background = 'transparent'"
    >
      <X :size="24" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { Bot, X } from 'lucide-vue-next'
import { useAIStore } from '@/stores/aiStore'

const aiStore = useAIStore()

const closeChat = () => {
  aiStore.closeChat()
}
</script>