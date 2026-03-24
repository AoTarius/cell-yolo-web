<script setup lang="ts">
import '@/assets/styles/colors.css'
import { computed, onMounted, ref, watch } from 'vue'
import { useAnalysisStore } from '@/stores/analysisStore'
import type { CellData } from '@/stores/analysisStore'

const store = useAnalysisStore()

const props = defineProps<{
  cellData: CellData
  cellId?: string
}>()

const emit = defineEmits<{
  back: []
}>()

// 从数据库加载的细胞详情数据
const dbCellDetail = ref<CellData | null>(null)
const isLoading = ref(false)

// 加载细胞详情数据
async function loadCellDetailData() {
  if (!props.cellId || !store.selectedRecord?.task_id) {
    return
  }

  isLoading.value = true
  try {
    dbCellDetail.value = await store.loadCellDetail(store.selectedRecord.task_id, props.cellId)
  } catch (error) {
    console.error('加载细胞详情失败:', error)
  } finally {
    isLoading.value = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadCellDetailData()
})

// 监听细胞ID变化，重新加载数据
watch(() => props.cellId, (newCellId, oldCellId) => {
  if (newCellId && newCellId !== oldCellId) {
    loadCellDetailData()
  }
})

// 使用数据库加载的数据，如果没有则使用传入的 cellData（兼容性）
const displayCellData = computed(() => {
  return dbCellDetail.value || props.cellData
})

// 计算属性：首次出现帧
const firstFrame = computed(() => {
  return displayCellData.value.frames.length > 0 ? displayCellData.value.frames[0]?.frame_number ?? 0 : 0
})

// 计算属性：最后出现帧
const lastFrame = computed(() => {
  const len = displayCellData.value.frames.length
  return len > 0 ? displayCellData.value.frames[len - 1]?.frame_number ?? 0 : 0
})

// 计算属性：存活帧数
const frameCount = computed(() => {
  return displayCellData.value.frames.length
})

// 计算属性：平均速度
const avgSpeed = computed(() => {
  if (displayCellData.value.frames.length === 0) return 0
  const totalSpeed = displayCellData.value.frames.reduce((sum, f) => sum + f.velocity.speed, 0)
  return totalSpeed / displayCellData.value.frames.length
})

// 计算属性：总移动距离
const totalDistance = computed(() => {
  if (displayCellData.value.frames.length === 0) return 0
  return displayCellData.value.frames.reduce((sum, f) => sum + f.velocity.speed, 0)
})

// 计算属性：平均面积
const avgArea = computed(() => {
  if (displayCellData.value.frames.length === 0) return 0
  const totalArea = displayCellData.value.frames.reduce((sum, f) => sum + f.area, 0)
  return totalArea / displayCellData.value.frames.length
})

// 计算属性：平均可见性
const avgVisibility = computed(() => {
  return displayCellData.value.avgVisibility ?? 1.0
})

// 计算属性：细胞类别
const cellClass = computed(() => {
  return displayCellData.value.cellClass ?? 0
})

// 形状特征计算属性
const shapeMetrics = computed(() => {
  if (!displayCellData.value.rawMetrics || displayCellData.value.rawMetrics.length === 0) {
    return {
      avgPerimeter: 0,
      avgCircularity: 0,
      avgAspectRatio: 0,
      avgSpreadingIndex: 0,
      avgShapeChangeRate: 0,
      avgProtrusionActivityIndex: 0
    }
  }

  const metrics = displayCellData.value.rawMetrics
  const perimeter = metrics.map(m => m.shape?.perimeter ?? 0)
  const circularity = metrics.map(m => m.shape?.circularity ?? 0)
  const aspectRatio = metrics.map(m => m.shape?.aspect_ratio ?? 0)
  const spreadingIndex = metrics.map(m => m.shape?.spreading_index ?? 0)
  const shapeChangeRate = metrics.map(m => m.shape?.shape_change_rate ?? 0)
  const protrusionActivity = metrics.map(m => m.shape?.protrusion_activity_index ?? 0)

  return {
    avgPerimeter: perimeter.reduce((a, b) => a + b, 0) / perimeter.length,
    avgCircularity: circularity.reduce((a, b) => a + b, 0) / circularity.length,
    avgAspectRatio: aspectRatio.reduce((a, b) => a + b, 0) / aspectRatio.length,
    avgSpreadingIndex: spreadingIndex.reduce((a, b) => a + b, 0) / spreadingIndex.length,
    avgShapeChangeRate: shapeChangeRate.reduce((a, b) => a + b, 0) / shapeChangeRate.length,
    avgProtrusionActivityIndex: protrusionActivity.reduce((a, b) => a + b, 0) / protrusionActivity.length
  }
})

// 运动特征计算属性
const motionMetrics = computed(() => {
  if (!displayCellData.value.rawMetrics || displayCellData.value.rawMetrics.length === 0) {
    return {
      avgMigrationSpeed: 0,
      avgMSD: 0,
      avgPersistenceIndex: 0,
      avgTurningAngle: 0
    }
  }

  const metrics = displayCellData.value.rawMetrics
  const migrationSpeed = metrics.map(m => m.motion?.migration_speed ?? 0)
  const msd = metrics.map(m => m.motion?.mean_square_displacement ?? 0)
  const persistenceIndex = metrics.map(m => m.motion?.persistence_index ?? 0)
  const turningAngle = metrics.map(m => m.motion?.turning_angle ?? 0)

  return {
    avgMigrationSpeed: migrationSpeed.reduce((a, b) => a + b, 0) / migrationSpeed.length,
    avgMSD: msd.reduce((a, b) => a + b, 0) / msd.length,
    avgPersistenceIndex: persistenceIndex.reduce((a, b) => a + b, 0) / persistenceIndex.length,
    avgTurningAngle: turningAngle.reduce((a, b) => a + b, 0) / turningAngle.length
  }
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
      <h2>细胞详情 - {{ displayCellData.cell_id }}</h2>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-state">
      <svg class="loading-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
      </svg>
      <p>加载细胞详情中...</p>
    </div>

    <!-- 细胞详情内容 -->
    <div v-else class="detail-content">
      <!-- 基本信息卡片 -->
      <div class="info-section">
        <h3>基本信息</h3>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">细胞ID</span>
            <span class="info-value">{{ displayCellData.cell_id }}</span>
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

      <!-- 形状特征区域 -->
      <div class="info-section shape-section">
        <h3>形状特征</h3>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">周长</span>
            <span class="info-value">{{ shapeMetrics.avgPerimeter.toFixed(2) }} px</span>
          </div>
          <div class="info-item">
            <span class="info-label">圆形度</span>
            <span class="info-value">{{ shapeMetrics.avgCircularity.toFixed(3) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">长宽比</span>
            <span class="info-value">{{ shapeMetrics.avgAspectRatio.toFixed(3) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">扩散指数</span>
            <span class="info-value">{{ shapeMetrics.avgSpreadingIndex.toFixed(3) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">形状变化率</span>
            <span class="info-value">{{ shapeMetrics.avgShapeChangeRate.toFixed(4) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">突起活动指数</span>
            <span class="info-value">{{ shapeMetrics.avgProtrusionActivityIndex.toFixed(4) }}</span>
          </div>
        </div>
      </div>

      <!-- 运动特征区域 -->
      <div class="info-section motion-section">
        <h3>运动特征</h3>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">迁移速度</span>
            <span class="info-value">{{ motionMetrics.avgMigrationSpeed.toFixed(2) }} px/frame</span>
          </div>
          <div class="info-item">
            <span class="info-label">均方位移 (MSD)</span>
            <span class="info-value">{{ motionMetrics.avgMSD.toFixed(2) }} px²</span>
          </div>
          <div class="info-item">
            <span class="info-label">持续性指数</span>
            <span class="info-value">{{ motionMetrics.avgPersistenceIndex.toFixed(3) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">平均转向角</span>
            <span class="info-value">{{ motionMetrics.avgTurningAngle.toFixed(1) }}°</span>
          </div>
        </div>
      </div>

      <!-- 轨迹图和统计分析 - 三栏布局 -->
      <div class="analysis-grid">
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

        <!-- 竖向分隔线 -->
        <div class="analysis-divider"></div>

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
              <tr v-for="frame in displayCellData.frames" :key="frame.frame_number">
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

    </div>
  </div>
</template>

<style scoped>
.cell-detail-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-main);
  overflow: hidden;
}

.detail-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid var(--bg-input);
  background: var(--bg-card);
  display: flex;
  align-items: center;
  gap: 1rem;
}

.btn-back {
  padding: 0.5rem 1rem;
  background: var(--bg-input);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-back:hover {
  background: var(--bg-cover);
  border-color: var(--border-hover);
}

.btn-back svg {
  width: 16px;
  height: 16px;
}

.detail-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  gap: 1rem;
}

.loading-icon {
  width: 48px;
  height: 48px;
  animation: spin 1s linear infinite;
  color: var(--accent-blue);
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.loading-state p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 1rem;
}

.detail-content {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.info-section,
.position-section {
  margin-bottom: 2rem;
}

.info-section h3,
.trajectory-section h3,
.position-section h3,
.stats-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
}

/* 形状特征区域 */
.shape-section {
  border-left: 4px solid var(--accent-green);
  padding-left: 1rem;
}

:global(:root:not(.dark)) .shape-section {
  border-left-color: var(--accent-green-light);
}

.shape-section h3 {
  color: var(--accent-green);
}

:global(:root:not(.dark)) .shape-section h3 {
  color: var(--accent-green-light);
}

/* 运动特征区域 */
.motion-section {
  border-left: 4px solid var(--accent-blue);
  padding-left: 1rem;
}

:global(:root:not(.dark)) .motion-section {
  border-left-color: var(--accent-blue-light);
}

.motion-section h3 {
  color: var(--accent-blue);
}

:global(:root:not(.dark)) .motion-section h3 {
  color: var(--accent-blue-light);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.info-item {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-label {
  font-size: 0.875rem;
  color: var(--text-muted);
}

.info-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

/* 三栏布局容器 */
.analysis-grid {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 1rem;
  margin-bottom: 2rem;
}

.trajectory-section,
.stats-section {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.analysis-divider {
  width: 1px;
  background: var(--border-color);
  height: 100%;
  align-self: stretch;
}

.trajectory-placeholder,
.stats-placeholder {
  background: var(--bg-card);
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  padding: 4rem 2rem;
  text-align: center;
  color: var(--text-muted);
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.placeholder-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 1rem;
  color: var(--border-color);
}

.trajectory-placeholder p,
.stats-placeholder p {
  margin: 0.5rem 0;
  font-size: 1rem;
  color: var(--text-secondary);
}

.placeholder-hint {
  font-size: 0.875rem !important;
  color: var(--text-disabled) !important;
}

.table-wrapper {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.position-table {
  width: 100%;
  border-collapse: collapse;
}

.position-table th {
  background: var(--bg-input);
  padding: 0.75rem 1rem;
  text-align: left;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-color);
}

.position-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--bg-input);
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.position-table tbody tr:hover {
  background: var(--bg-main);
}

/* 滚动条样式 */
.detail-content::-webkit-scrollbar {
  width: 10px;
}

.detail-content::-webkit-scrollbar-track {
  background: var(--bg-main);
}

.detail-content::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 5px;
}

.detail-content::-webkit-scrollbar-thumb:hover {
  background: var(--border-hover);
}
</style>
