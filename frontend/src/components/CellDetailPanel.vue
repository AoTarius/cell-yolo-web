<script setup lang="ts">
import { computed } from 'vue'
import type { CellData } from '@/stores/analysisStore'

const props = defineProps<{
  cellData: CellData
}>()

const emit = defineEmits<{
  back: []
}>()

// 计算属性：首次出现帧
const firstFrame = computed(() => {
  return props.cellData.frames.length > 0 ? props.cellData.frames[0]?.frame_number ?? 0 : 0
})

// 计算属性：最后出现帧
const lastFrame = computed(() => {
  const len = props.cellData.frames.length
  return len > 0 ? props.cellData.frames[len - 1]?.frame_number ?? 0 : 0
})

// 计算属性：存活帧数
const frameCount = computed(() => {
  return props.cellData.frames.length
})

// 计算属性：平均速度
const avgSpeed = computed(() => {
  if (props.cellData.frames.length === 0) return 0
  const totalSpeed = props.cellData.frames.reduce((sum, f) => sum + f.velocity.speed, 0)
  return totalSpeed / props.cellData.frames.length
})

// 计算属性：总移动距离
const totalDistance = computed(() => {
  if (props.cellData.frames.length === 0) return 0
  return props.cellData.frames.reduce((sum, f) => sum + f.velocity.speed, 0)
})

// 计算属性：平均面积
const avgArea = computed(() => {
  if (props.cellData.frames.length === 0) return 0
  const totalArea = props.cellData.frames.reduce((sum, f) => sum + f.area, 0)
  return totalArea / props.cellData.frames.length
})
</script>

<template>
  <div class="cell-detail-panel">
    <!-- 返回按钮 -->
    <div class="detail-header">
      <button class="btn-back" @click="emit('back')">
        <svg
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M10 19l-7-7m0 0l7-7m-7 7h18"
          ></path>
        </svg>
        返回
      </button>
      <h2>细胞详情 - {{ cellData.cell_id }}</h2>
    </div>

    <!-- 细胞详情内容 -->
    <div class="detail-content">
      <!-- 基本信息卡片 -->
      <div class="info-section">
        <h3>基本信息</h3>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">细胞ID</span>
            <span class="info-value">{{ cellData.cell_id }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">首次出现</span>
            <span class="info-value">第 {{ firstFrame }} 帧</span>
          </div>
          <div class="info-item">
            <span class="info-label">最后出现</span>
            <span class="info-value">第 {{ lastFrame }} 帧</span>
          </div>
          <div class="info-item">
            <span class="info-label">存活帧数</span>
            <span class="info-value">{{ frameCount }} 帧</span>
          </div>
          <div class="info-item">
            <span class="info-label">平均速度</span>
            <span class="info-value">{{ avgSpeed.toFixed(2) }} px/frame</span>
          </div>
          <div class="info-item">
            <span class="info-label">移动距离</span>
            <span class="info-value">{{ totalDistance.toFixed(1) }} px</span>
          </div>
          <div class="info-item">
            <span class="info-label">平均面积</span>
            <span class="info-value">{{ avgArea.toFixed(1) }} px²</span>
          </div>
        </div>
      </div>

      <!-- 轨迹图占位 -->
      <div class="trajectory-section">
        <h3>运动轨迹</h3>
        <div class="trajectory-placeholder">
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
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            ></path>
          </svg>
          <p>细胞运动轨迹图</p>
          <p class="placeholder-hint">此处将展示该细胞的详细运动轨迹</p>
        </div>
      </div>

      <!-- 位置数据表格占位 -->
      <div class="position-section">
        <h3>位置数据</h3>
        <div class="table-wrapper">
          <table class="position-table">
            <thead>
              <tr>
                <th>帧号</th>
                <th>X 坐标</th>
                <th>Y 坐标</th>
                <th>面积</th>
                <th>速度</th>
                <th>VX</th>
                <th>VY</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="frame in cellData.frames" :key="frame.frame_number">
                <td>{{ frame.frame_number }}</td>
                <td>{{ frame.position.x.toFixed(2) }}</td>
                <td>{{ frame.position.y.toFixed(2) }}</td>
                <td>{{ frame.area.toFixed(1) }}</td>
                <td>{{ frame.velocity.speed.toFixed(2) }}</td>
                <td>{{ frame.velocity.vx.toFixed(2) }}</td>
                <td>{{ frame.velocity.vy.toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 统计信息占位 -->
      <div class="stats-section">
        <h3>统计分析</h3>
        <div class="stats-placeholder">
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
              d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"
            ></path>
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"
            ></path>
          </svg>
          <p>统计图表</p>
          <p class="placeholder-hint">此处将展示速度分布、方向变化等统计图表</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cell-detail-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #0d1117;
  overflow: hidden;
}

.detail-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #21262d;
  background: #161b22;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.btn-back {
  padding: 0.5rem 1rem;
  background: #21262d;
  color: #c9d1d9;
  border: 1px solid #30363d;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-back:hover {
  background: #30363d;
  border-color: #8b949e;
}

.btn-back svg {
  width: 16px;
  height: 16px;
}

.detail-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.detail-content {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.info-section,
.trajectory-section,
.position-section,
.stats-section {
  margin-bottom: 2rem;
}

.info-section h3,
.trajectory-section h3,
.position-section h3,
.stats-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #fff;
  margin: 0 0 1rem 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.info-item {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-label {
  font-size: 0.875rem;
  color: #8b949e;
}

.info-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #fff;
}

.trajectory-placeholder,
.stats-placeholder {
  background: #161b22;
  border: 2px dashed #30363d;
  border-radius: 8px;
  padding: 4rem 2rem;
  text-align: center;
  color: #8b949e;
}

.placeholder-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 1rem;
  color: #30363d;
}

.trajectory-placeholder p,
.stats-placeholder p {
  margin: 0.5rem 0;
  font-size: 1rem;
  color: #c9d1d9;
}

.placeholder-hint {
  font-size: 0.875rem !important;
  color: #6e7681 !important;
}

.table-wrapper {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  overflow: hidden;
}

.position-table {
  width: 100%;
  border-collapse: collapse;
}

.position-table th {
  background: #21262d;
  padding: 0.75rem 1rem;
  text-align: left;
  font-size: 0.875rem;
  font-weight: 600;
  color: #8b949e;
  border-bottom: 1px solid #30363d;
}

.position-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #21262d;
  color: #c9d1d9;
  font-size: 0.875rem;
}

.position-table tbody tr:hover {
  background: #0d1117;
}

/* 滚动条样式 */
.detail-content::-webkit-scrollbar {
  width: 10px;
}

.detail-content::-webkit-scrollbar-track {
  background: #0d1117;
}

.detail-content::-webkit-scrollbar-thumb {
  background: #30363d;
  border-radius: 5px;
}

.detail-content::-webkit-scrollbar-thumb:hover {
  background: #484f58;
}
</style>
