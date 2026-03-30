<template>
  <div class="flex gap-2 py-2 items-center">
    <div
      v-for="(dot, index) in 3"
      :key="index"
      class="w-2 h-2 rounded-full"
      style="background: var(--ai-typing-dot)"
      :style="{ animationDelay: index * 0.2 + 's' }"
    ></div>
    <span class="text-sm ml-2" style="color: var(--text-muted)">正在输入...</span>
  </div>
</template>

<style scoped>
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

div > div {
  animation: bounce 1.4s infinite ease-in-out;
}
</style>