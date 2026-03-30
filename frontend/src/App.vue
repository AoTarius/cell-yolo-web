<script setup lang="ts">
import { RouterView } from 'vue-router'
import Toast from '@/components/common/feedback/Toast.vue'
import FloatingWindow from '@/components/ai/FloatingWindow.vue'
</script>

<template>
  <RouterView />
  <Toast />
  <FloatingWindow />
</template>

<style scoped>
/* App 只作为容器，不添加额外样式 */
</style>
