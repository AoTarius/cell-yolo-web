<script setup lang="ts">
import '@/assets/styles/colors.css'
import { ref } from 'vue'

// 当前选中的图表
const selectedChart = ref<number>(1)

// 图表列表
const charts = [1, 2, 3, 4, 5, 6]

// 选择图表
function selectChart(chartNumber: number) {
  selectedChart.value = chartNumber
}
</script>

<template>
  
</template>