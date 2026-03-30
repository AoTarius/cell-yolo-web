<template>
  <div class="ai-header">
    <!-- 左侧：AI信息 -->
    <div class="ai-header-left">
      <div class="ai-avatar ai-avatar-assistant">
        <Bot :size="24" />
      </div>
      <div class="ai-header-info">
        <h2 class="ai-title">AI助手</h2>
        <p class="ai-subtitle">细胞分析专家</p>
      </div>
    </div>

    <!-- 右侧：关闭按钮 -->
    <button class="ai-close-btn" @click="closeChat" title="关闭对话框">
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

<style scoped>
.ai-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--ai-header-border);
  background: var(--ai-header-bg);
  border-bottom: var(--ai-border-color) 1px solid;
}

.ai-header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.ai-avatar {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.ai-avatar-assistant {
  background: var(--ai-assistant-avatar);
}

.ai-header-info {
  display: flex;
  flex-direction: column;
}

.ai-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.ai-subtitle {
  font-size: 0.875rem;
  margin: 0;
  color: var(--text-muted);
}

.ai-close-btn {
  transition: all 0.2s;
  padding: 0.5rem;
  border-radius: 0.5rem;
  border: var(--ai-border-color) 1px solid;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-close-btn:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}
</style>