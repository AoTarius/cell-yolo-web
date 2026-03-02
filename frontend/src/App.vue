<script setup lang="ts">
import { RouterView } from 'vue-router'
import Toast from '@/components/common/Toast.vue'
</script>

<template>
  <RouterView />
  <Toast />
</template>

<style scoped>
/* App 只作为容器，不添加额外样式 */
</style>
