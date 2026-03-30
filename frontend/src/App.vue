<script setup lang="ts">
import { RouterView } from 'vue-router'
import Toast from '@/components/common/feedback/Toast.vue'
import AIChatDialog from '@/components/common/dialog/AIChatDialog.vue'
</script>

<template>
  <RouterView />
  <Toast />
  <AIChatDialog />
</template>

<style scoped>
/* App 只作为容器，不添加额外样式 */
</style>
