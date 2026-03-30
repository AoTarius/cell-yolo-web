<template>
  <div class="space-y-4">
    <!-- 消息列表 -->
    <div
      v-for="(message, index) in aiStore.messages"
      :key="message.id"
      :class="['flex gap-3', message.role === 'user' ? 'flex-row-reverse' : 'flex-row']"
      class="message-enter"
    >
      <!-- 头像 -->
      <div
        class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
        :style="{ background: message.role === 'user' ? 'var(--ai-user-avatar)' : 'var(--ai-assistant-avatar)' }"
      >
        <component :is="message.role === 'user' ? User : Bot" :size="20" style="color: white" />
      </div>

      <!-- 消息内容 -->
      <div
        class="max-w-2xl px-4 py-3 rounded-2xl"
        :style="{
          background: message.role === 'user' ? 'var(--ai-user-bg)' : 'var(--ai-assistant-bg)',
          color: message.role === 'user' ? 'var(--ai-user-text)' : 'var(--ai-assistant-text)',
          borderRadius: message.role === 'user' ? '12px 12px 0 12px' : '12px 12px 12px 0'
        }"
      >
        <!-- Markdown渲染 -->
        <div
          v-if="message.content"
          class="prose prose-invert prose-sm max-w-none markdown-content"
          v-html="renderMarkdown(message.content)"
        ></div>

        <!-- 加载动画 -->
        <TypingIndicator v-else-if="message.id === 'streaming'" />
      </div>
    </div>

    <!-- 空状态提示 -->
    <div v-if="aiStore.messages.length === 0" class="text-center py-12" style="color: var(--text-muted)">
      <Bot :size="48" class="mx-auto mb-4" style="opacity: 0.5" />
      <p class="text-lg">开始与AI助手对话吧！</p>
      <p class="text-sm mt-2">输入你的问题，细胞分析专家会为你解答</p>
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
  breaks: true, // 支持GitHub风格的换行
  gfm: true,    // 启用GitHub Flavored Markdown
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
/* 简单的淡入动画 */
.message-enter {
  animation: fadeIn 0.3s ease-out;
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