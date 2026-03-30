<template>
  <div class="ai-typing-indicator">
    <div
      v-for="(dot, index) in 3"
      :key="index"
      class="ai-typing-dot"
      :style="{ animationDelay: index * 0.2 + 's' }"
    ></div>
    <span class="ai-typing-text">正在输入...</span>
  </div>
</template>

<style scoped>
.ai-typing-indicator {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem 0;
  align-items: center;
}

.ai-typing-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: var(--ai-typing-dot);
  animation: bounce 1.4s infinite ease-in-out;
}

.ai-typing-text {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-left: 0.5rem;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  40% {
    transform: translateY(-8px);
    opacity: 1;
  }
}
</style>