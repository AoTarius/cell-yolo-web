<template>
  <div class="ai-messages-container">
    <!-- 消息列表 -->
    <div
      v-for="(message, index) in aiStore.messages"
      :key="message.id"
      :class="['ai-message', message.role === 'user' ? 'ai-message-user' : 'ai-message-assistant']"
    >
      <!-- 头像 -->
      <div
        :class="['ai-avatar', message.role === 'user' ? 'ai-avatar-user' : 'ai-avatar-assistant']"
      >
        <component :is="message.role === 'user' ? User : Bot" :size="20" />
      </div>

      <!-- 消息内容 -->
      <div
        :class="['ai-message-content', message.role === 'user' ? 'ai-message-content-user' : 'ai-message-content-assistant']"
      >
        <!-- Markdown渲染 -->
        <div
          v-if="message.content"
          class="markdown-content"
          v-html="renderMarkdown(message.content)"
        ></div>

        <!-- 加载动画 -->
        <TypingIndicator v-else-if="message.id === 'streaming'" />
      </div>
    </div>

    <!-- 空状态提示 -->
    <div v-if="aiStore.messages.length === 0" class="ai-empty-state">
      <Bot :size="48" class="ai-empty-icon" />
      <p class="ai-empty-title">开始与AI助手对话吧！</p>
      <p class="ai-empty-desc">输入你的问题，细胞分析专家会为你解答</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Bot, User } from 'lucide-vue-next'
import { marked } from 'marked'
import { useAIStore } from '@/stores/aiStore'
import TypingIndicator from './TypingIndicator.vue'

// 配置marked选项
marked.setOptions({
  breaks: true,
  gfm: true,
})

const aiStore = useAIStore()

// Markdown渲染
const renderMarkdown = (content: string) => {
  try {
    return marked.parse(content)
  } catch (error) {
    console.error('Markdown解析错误:', error)
    return content
  }
}
</script>

<style scoped>
/* 消息容器 */
.ai-messages-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* 消息项 */
.ai-message {
  display: flex;
  gap: 0.75rem;
  animation: fadeIn 0.3s ease-out;
  border-bottom: var(--ai-border-color) 1px solid;
}

.ai-message-user {
  flex-direction: row-reverse;
}

.ai-message-assistant {
  flex-direction: row;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 头像 */
.ai-avatar {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: white;
}

.ai-avatar-user {
  background: var(--ai-user-avatar);
}

.ai-avatar-assistant {
  background: var(--ai-assistant-avatar);
}

/* 消息内容 */
.ai-message-content {
  max-width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 1rem;
  color: inherit;
}

.ai-message-content-user {
  background: var(--ai-user-bg);
  color: var(--ai-user-text);
  border-radius: 0.75rem 0.75rem 0 0.75rem;
}

.ai-message-content-assistant {
  background: var(--ai-assistant-bg);
  color: var(--ai-assistant-text);
  border-radius: 0.75rem 0.75rem 0.75rem 0;
}

/* 空状态 */
.ai-empty-state {
  text-align: center;
  padding: 3rem 0;
  color: var(--text-muted);
}

.ai-empty-icon {
  margin: 0 auto 1rem;
  opacity: 0.5;
}

.ai-empty-title {
  font-size: 1.125rem;
  margin: 0;
}

.ai-empty-desc {
  font-size: 0.875rem;
  margin: 0.5rem 0 0;
}

/* Markdown样式 */
.markdown-content {
  line-height: 1.6;
  color: inherit;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  margin-top: 1em;
  margin-bottom: 0.5em;
  font-weight: 600;
  color: var(--text-primary);
}

.markdown-content :deep(h1) { font-size: 1.5em; }
.markdown-content :deep(h2) { font-size: 1.3em; }
.markdown-content :deep(h3) { font-size: 1.15em; }

.markdown-content :deep(p) {
  margin: 0.5em 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

.markdown-content :deep(li) {
  margin: 0.25em 0;
}

.markdown-content :deep(code) {
  background: var(--bg-input);
  padding: 0.2em 0.4em;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: 'Courier New', monospace;
}

.markdown-content :deep(pre) {
  background: var(--bg-card);
  padding: 1em;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0.5em 0;
}

.markdown-content :deep(pre code) {
  background: transparent;
  padding: 0;
  border-radius: 0;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid var(--accent-blue);
  padding-left: 1em;
  margin: 0.5em 0;
  opacity: 0.8;
}

.markdown-content :deep(a) {
  color: var(--accent-blue);
  text-decoration: underline;
}

.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.5em 0;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid var(--border-secondary);
  padding: 0.5em;
}

.markdown-content :deep(th) {
  background: var(--bg-input);
}

.markdown-content :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-secondary);
  margin: 1em 0;
}

.markdown-content :deep(img) {
  max-width: 100%;
  border-radius: 4px;
}
</style>