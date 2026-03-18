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
  <div class="cell-population-chart">
    <h3>细胞群体图表</h3>
    <div class="content-wrapper">
      <!-- 侧边栏按钮区域 -->
      <div class="sidebar">
        <button
          v-for="chart in charts"
          :key="chart"
          :class="['chart-button', { active: selectedChart === chart }]"
          @click="selectChart(chart)"
        >
          {{ chart === 1 ? '细胞3D轨迹图' : `图表${chart}` }}
        </button>
      </div>

      <!-- 主内容区域 -->
      <div class="main-content">
        <div class="visualization-placeholder">
          <!-- 图表1：3D轨迹图 -->
          <template v-if="selectedChart === 1">
            <svg
              class="placeholder-icon"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
              ></path>
            </svg>
            <p>3D 轨迹图 (X-Y-Time)</p>
            <p class="placeholder-hint">此处将展示细胞运动轨迹的三维可视化</p>
          </template>

          <!-- 图表2-6：图标分析 -->
          <template v-else>
            <svg
              class="placeholder-icon"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              ></path>
            </svg>
            <p>细胞图表分析 - 图表{{ selectedChart }}</p>
            <p class="placeholder-hint">此处将展示细胞的图表化分析结果</p>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cell-population-chart {
  margin-bottom: 2rem;
}

.cell-population-chart h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .cell-population-chart h3 {
  color: var(--text-primary-light);
}

.content-wrapper {
  display: flex;
  gap: 0;
}

/* 侧边栏样式 */
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 0;
  min-width: 80px;
}

.chart-button {
  padding: 0.75rem 1rem;
  background: var(--bg-card);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: 0;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
  height: 60px;
  width: 100%;
}

:global(:root:not(.dark)) .chart-button {
  background: var(--bg-card-light);
  color: var(--text-primary-light);
  border-color: var(--border-color-light);
}

.chart-button:hover {
  background: var(--alpha-badge);
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

:global(:root:not(.dark)) .chart-button:hover {
  background: var(--upload-hover-bg);
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.chart-button.active {
  background: var(--alpha-badge);
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

:global(:root:not(.dark)) .chart-button.active {
  background: var(--upload-hover-bg);
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

/* 主内容区域 */
.main-content {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: flex-start;
}

.visualization-placeholder {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 0;
  padding: 4rem 2rem;
  text-align: center;
  color: var(--text-muted);
  transition: background 0.3s, border-color 0.3s;
  width: 100%;
  aspect-ratio: 1 / 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

:global(:root:not(.dark)) .visualization-placeholder {
  background: var(--bg-card-light);
  border: 2px solid var(--border-color-light);
  color: var(--text-muted-light);
}

.placeholder-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 1rem;
  color: var(--border-color);
  transition: color 0.3s;
}

:global(:root:not(.dark)) .placeholder-icon {
  color: var(--border-color-light);
}

.visualization-placeholder p {
  margin: 0.5rem 0;
  font-size: 1rem;
  color: var(--text-secondary);
  transition: color 0.3s;
}

:global(:root:not(.dark)) .visualization-placeholder p {
  color: var(--text-primary-light);
}

.placeholder-hint {
  font-size: 0.875rem !important;
  color: var(--text-disabled) !important;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .placeholder-hint {
  color: var(--text-disabled-light) !important;
}
</style>