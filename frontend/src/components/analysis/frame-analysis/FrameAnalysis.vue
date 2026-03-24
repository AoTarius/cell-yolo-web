<script setup lang="ts">
import '@/assets/styles/colors.css'
import { ref, computed, watch, onMounted } from 'vue'
import type { AnalysisRecord, CellData } from '@/stores/analysisStore'
import { useAnalysisStore } from '@/stores/analysisStore'

const props = defineProps<{
  record: AnalysisRecord
}>()

const store = useAnalysisStore()

// 响应式的当前帧号
const currentFrameIndex = ref(0)

// 图片加载状态
const isImageLoading = ref(false)

// 当前显示的图片 URL
const displayedImageUrl = ref('')

// 当前帧的细胞数据
const currentFrameCells = ref<CellData[]>([])

// 细胞数据加载状态
const isLoadingCells = ref(false)

// 任务的所有细胞数据缓存
const allCellsCache = ref<CellData[]>([])

// 当前帧细胞数据类型（用于显示）
interface FrameCellInfo {
  track_id: number
  position: { x: number; y: number }
  area: number
  velocity: { vx: number; vy: number; speed: number }
  bounding_box: { x: number; y: number; width: number; height: number }
  conf: number
  class_id: number
  visibility: number
  perimeter?: number
  circularity?: number
  aspect_ratio?: number
}

// 加载任务的所有细胞数据到缓存
async function loadAllCells() {
  if (!props.record?.task_id) {
    return
  }

  // 如果已经有缓存，直接使用
  if (allCellsCache.value.length > 0) {
    return
  }

  isLoadingCells.value = true
  try {
    allCellsCache.value = await store.loadCellsByTask(props.record.task_id)
    console.log(`[逐帧分析] 加载任务细胞数据: ${props.record.task_id}, 细胞数量: ${allCellsCache.value.length}`)
  } catch (error) {
    console.error('加载细胞数据失败:', error)
    allCellsCache.value = []
  } finally {
    isLoadingCells.value = false
  }
}

// 加载当前帧的细胞数据
function loadCurrentFrameCells() {
  if (!props.record?.task_id || allCellsCache.value.length === 0) {
    currentFrameCells.value = []
    return
  }

  const currentFrameNum = currentFrameIndex.value + 1

  // 从缓存中筛选当前帧的细胞数据
  const frameCells: FrameCellInfo[] = []

  allCellsCache.value.forEach(cell => {
    // 查找该细胞在当前帧的数据
    const frameData = cell.frames.find(f => f.frame_number === currentFrameNum)
    if (frameData) {
      // 获取该细胞的详细指标（找到对应帧的指标）
      const frameIndex = cell.frames.findIndex(f => f.frame_number === currentFrameNum)
      const metrics = cell.rawMetrics?.[frameIndex] || {}

      frameCells.push({
        track_id: parseInt(cell.cell_id),
        position: frameData.position,
        area: frameData.area,
        velocity: frameData.velocity,
        bounding_box: frameData.bounding_box,
        conf: cell.avg_conf, // 使用平均置信度
        class_id: cell.cellClass ?? 0,
        visibility: cell.avgVisibility ?? 1.0,
        perimeter: metrics.shape?.perimeter,
        circularity: metrics.shape?.circularity,
        aspect_ratio: metrics.shape?.aspect_ratio
      })
    }
  })

  currentFrameCells.value = frameCells.map(cell => ({
    cell_id: String(cell.track_id),
    first_frame: currentFrameNum,
    last_frame: currentFrameNum,
    frame_count: 1,
    avg_width: cell.bounding_box.width,
    avg_height: cell.bounding_box.height,
    avg_conf: cell.conf,
    avg_velocity: cell.velocity.speed,
    frames: [{
      frame_number: currentFrameNum,
      position: cell.position,
      area: cell.area,
      velocity: cell.velocity,
      bounding_box: cell.bounding_box
    }],
    rawMetrics: [{}],
    avgVisibility: cell.visibility,
    cellClass: cell.class_id
  }))

  console.log(`[逐帧分析] 第 ${currentFrameNum} 帧的细胞数量: ${frameCells.length}`)
}

// 下一帧
function handleNextFrame() {
  const totalFrames = props.record.result?.total_frames ?? 0
  if (currentFrameIndex.value < totalFrames - 1) {
    currentFrameIndex.value++
    loadImage()
    loadCurrentFrameCells()
  }
}

// 上一帧
function handlePrevFrame() {
  if (currentFrameIndex.value > 0) {
    currentFrameIndex.value--
    loadImage()
    loadCurrentFrameCells()
  }
}

// 回到第一帧
function handleGoToFirstFrame() {
  currentFrameIndex.value = 0
  loadImage()
  loadCurrentFrameCells()
}

// 跳转到指定帧
function handleJumpToFrame(frameStr: string) {
  const frame = parseInt(frameStr, 10)
  const total = props.record.result?.total_frames ?? 0

  if (!isNaN(frame) && frame >= 1 && frame <= total) {
    currentFrameIndex.value = frame - 1
    loadImage()
    loadCurrentFrameCells()
  }
}

// 加载图片
function loadImage() {
  if (!props.record?.task_id) {
    return
  }

  // 添加时间戳参数避免浏览器缓存
  const timestamp = Date.now()
  const newUrl = `/api/frame/${props.record.task_id}/${currentFrameIndex.value}/?t=${timestamp}`
  isImageLoading.value = true

  const img = new Image()
  img.onload = () => {
    displayedImageUrl.value = newUrl
    isImageLoading.value = false
    loadCurrentFrameCells()
  }
  img.onerror = () => {
    console.error('帧图片加载失败:', newUrl)
    isImageLoading.value = false
  }
  img.src = newUrl
}

// 检查并加载图片
async function checkAndLoadImage() {
  if ((props.record?.result?.total_frames ?? 0) > 0 && props.record.task_id) {
    currentFrameIndex.value = 0
    // 先加载所有细胞数据到缓存
    await loadAllCells()
    // 然后加载图片
    loadImage()
  }
}

// 监听 record 变化，初始化加载第一帧
watch(() => props.record, (newRecord) => {
  checkAndLoadImage()
}, { deep: true })

// 监听任务ID变化，清空缓存并重新加载
watch(() => props.record?.task_id, (newTaskId, oldTaskId) => {
  if (newTaskId && newTaskId !== oldTaskId) {
    allCellsCache.value = []
    currentFrameCells.value = []
  }
})

// 监听帧号变化，更新细胞数据
watch(() => currentFrameIndex.value, () => {
  loadCurrentFrameCells()
})

// 组件挂载时加载图片
onMounted(() => {
  checkAndLoadImage()
})

// 计算属性：当前帧号（从1开始显示）
const currentFrameNumber = computed(() => currentFrameIndex.value + 1)

// 计算属性：总帧数
const totalFrames = computed(() => props.record.result?.total_frames ?? 0)

// 根据置信度返回对应的样式类
function getConfClass(conf: number): string {
  if (conf >= 0.9) return 'conf-high'
  if (conf >= 0.7) return 'conf-medium'
  return 'conf-low'
}
</script>

<template>
  <div class="frame-analysis">
    <div class="detail-content">
      <!-- 左侧：帧图片显示 -->
      <div class="detail-video-section">
        <h3>逐帧查看</h3>
        <div class="detail-video-wrapper">
          <div class="detail-video-container">
            <img
              v-if="record.result && totalFrames > 0 && displayedImageUrl"
              :src="displayedImageUrl"
              class="detail-video-player"
              alt="当前帧"
              :class="{ 'loading': isImageLoading }"
            />
            <div v-else class="detail-video-placeholder">
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
              <p class="placeholder-text">暂无帧数据</p>
            </div>
          </div>

          <!-- 帧控制栏 -->
          <div v-if="record.result && totalFrames > 0" class="detail-video-controls">
            <button class="detail-btn-control" @click="handleGoToFirstFrame">
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
                  d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
                ></path>
              </svg>
              第一帧
            </button>
            <button class="detail-btn-control" @click="handlePrevFrame">
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
                  d="M15 19l-7-7 7-7"
                ></path>
              </svg>
              上一帧
            </button>
            <div class="frame-counter">
              <input
                type="number"
                :value="currentFrameNumber"
                :min="1"
                :max="totalFrames"
                @input="handleJumpToFrame(($event.target as HTMLInputElement).value)"
                @blur="handleJumpToFrame(($event.target as HTMLInputElement).value)"
                @keyup.enter="handleJumpToFrame(($event.target as HTMLInputElement).value)"
                class="frame-input"
              />
              <span class="frame-separator">/</span>
              <span class="frame-total">{{ totalFrames }}</span>
              <span class="frame-label">帧</span>
            </div>
            <button class="detail-btn-control" @click="handleNextFrame">
              下一帧
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
                  d="M9 5l7 7-7 7"
                ></path>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- 竖向分隔线 -->
      <div class="detail-divider"></div>

      <!-- 右侧：逐帧分析 - 当前帧细胞信息 -->
      <div class="detail-info-section">
        <div class="info-header">
          <h3>逐帧分析</h3>
          <span v-if="record.result && totalFrames > 0" class="cell-count">
            第 {{ currentFrameNumber }} 帧 - 共 {{ currentFrameCells.length }} 个细胞
          </span>
        </div>

        <!-- 加载状态 -->
        <div v-if="isLoadingCells" class="loading-state">
          <svg class="loading-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
          <p>加载细胞数据中...</p>
        </div>

        <!-- 无数据状态 -->
        <div v-else-if="!record.result || totalFrames === 0" class="detail-placeholder">
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
              d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"
            ></path>
          </svg>
          <p>暂无帧数据</p>
        </div>

        <!-- 当前帧无细胞 -->
        <div v-else-if="currentFrameCells.length === 0" class="no-cells-state">
          <svg class="no-cells-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <p>当前帧未检测到细胞</p>
        </div>

        <!-- 细胞信息表格 -->
        <div v-else class="cells-table-container">
          <table class="cells-table">
            <thead>
              <tr>
                <th>细胞ID</th>
                <th>位置 (X, Y)</th>
                <th>面积</th>
                <th>速度</th>
                <th>方向 (VX, VY)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="cell in currentFrameCells" :key="cell.cell_id">
                <td class="cell-id">{{ cell.cell_id }}</td>
                <td>{{ cell.frames[0]?.position.x.toFixed(1) }}, {{ cell.frames[0]?.position.y.toFixed(1) }}</td>
                <td>{{ cell.frames[0]?.area.toFixed(1) }}</td>
                <td>{{ cell.frames[0]?.velocity.speed.toFixed(2) }}</td>
                <td>{{ cell.frames[0]?.velocity.vx.toFixed(2) }}, {{ cell.frames[0]?.velocity.vy.toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.frame-analysis {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
}

.detail-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 1rem;
  padding: 2rem;
  overflow: hidden;
}

.detail-video-section {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.detail-video-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-video-section h3 {
  color: var(--text-primary-light);
}

.detail-video-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-height: 0;
}

.detail-video-container {
  background: var(--bg-main);
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.3s;
  align-self: flex-start;
  display: flex;
  align-items: center;
  justify-content: center;
}

:global(:root:not(.dark)) .detail-video-container {
  background: var(--bg-main-light);
  border-color: var(--border-color-light);
}

.detail-video-player {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: contain;
  transition: opacity 0.15s ease-in-out;
}

.detail-video-player.loading {
  opacity: 0.7;
}

.detail-video-controls {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .detail-video-controls {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

.detail-btn-control {
  flex: 1;
  padding: 0.5rem 0.75rem;
  background: var(--bg-input);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  white-space: nowrap;
}

:global(:root:not(.dark)) .detail-btn-control {
  background: var(--bg-card-light);
  color: var(--text-primary-light);
  border-color: var(--border-color-light);
}

.detail-btn-control:hover {
  background: var(--bg-hover);
  border-color: var(--text-muted);
}

:global(:root:not(.dark)) .detail-btn-control:hover {
  background: var(--bg-main-light);
  border-color: var(--text-disabled-light);
}

.detail-btn-control svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.frame-counter {
  flex: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .frame-counter {
  color: var(--text-primary-light);
}

.frame-input {
  width: 50px;
  padding: 0.25rem 0.375rem;
  background: var(--bg-input);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
  text-align: center;
  transition: all 0.2s;
  outline: none;
}

:global(:root:not(.dark)) .frame-input {
  background: var(--bg-card-light);
  color: var(--text-primary-light);
  border-color: var(--border-color-light);
}

.frame-input:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px var(--alpha-focus-ring);
}

:global(:root:not(.dark)) .frame-input:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px var(--alpha-focus-ring);
}

.frame-input:hover:not(:focus) {
  border-color: var(--border-hover);
}

:global(:root:not(.dark)) .frame-input:hover:not(:focus) {
  border-color: var(--border-hover-light);
}

.frame-separator {
  color: var(--text-disabled);
  font-weight: 400;
}

:global(:root:not(.dark)) .frame-separator {
  color: var(--text-muted-light);
}

.frame-total {
  color: var(--text-muted);
  font-weight: 400;
}

:global(:root:not(.dark)) .frame-total {
  color: var(--text-muted-light);
}

.frame-label {
  color: var(--text-disabled);
  font-weight: 400;
}

:global(:root:not(.dark)) .frame-label {
  color: var(--text-muted-light);
}

.detail-video-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--alpha-toast);
  transition: background 0.3s;
}

:global(:root:not(.dark)) .detail-video-placeholder {
  background: var(--alpha-toast-light);
}

.detail-video-placeholder .placeholder-icon {
  width: 64px;
  height: 64px;
  color: var(--text-muted);
  margin-bottom: 1rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-video-placeholder .placeholder-icon {
  color: var(--text-disabled-light);
}

.detail-video-placeholder .placeholder-text {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-video-placeholder .placeholder-text {
  color: var(--text-primary-light);
}

.detail-info-section {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.detail-info-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-info-section h3 {
  color: var(--text-primary-light);
}

.detail-divider {
  width: 1px;
  background: var(--border-color);
  height: 100%;
  align-self: stretch;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .detail-divider {
  background: var(--border-color-light);
}

.detail-placeholder {
  text-align: center;
  padding: 4rem 2rem;
  max-width: 500px;
}

.detail-placeholder .placeholder-icon {
  width: 80px;
  height: 80px;
  color: var(--border-color);
  margin: 0 auto 1.5rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-placeholder .placeholder-icon {
  color: var(--border-color-light);
}

.detail-placeholder > p {
  font-size: 1rem;
  color: var(--text-muted);
  margin: 0 0 0.5rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-placeholder > p {
  color: var(--text-muted-light);
}

.detail-placeholder .placeholder-hint {
  font-size: 0.875rem;
  color: var(--text-disabled) !important;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .detail-placeholder .placeholder-hint {
  color: var(--text-disabled-light) !important;
}

/* 信息头部 */
.info-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.cell-count {
  font-size: 0.875rem;
  color: var(--text-muted);
  font-weight: 500;
}

:global(:root:not(.dark)) .cell-count {
  color: var(--text-muted-light);
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  gap: 1rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
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

/* 无细胞状态 */
.no-cells-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  gap: 1rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.no-cells-icon {
  width: 64px;
  height: 64px;
  color: var(--text-muted);
}

.no-cells-state p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 1rem;
}

/* 细胞表格容器 */
.cells-table-container {
  flex: 1;
  overflow: auto;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  min-height: 0;
}

.cells-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.cells-table thead {
  position: sticky;
  top: 0;
  z-index: 10;
}

.cells-table th {
  background: var(--bg-input);
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  color: var(--text-muted);
  border-bottom: 2px solid var(--border-color);
  white-space: nowrap;
}

:global(:root:not(.dark)) .cells-table th {
  background: var(--bg-hover);
  border-bottom-color: var(--border-color-light);
  color: var(--text-muted-light);
}

.cells-table td {
  padding: 0.625rem 1rem;
  border-bottom: 1px solid var(--bg-input);
  color: var(--text-secondary);
  white-space: nowrap;
}

:global(:root:not(.dark)) .cells-table td {
  border-bottom-color: var(--border-color-light);
  color: var(--text-primary-light);
}

.cells-table tbody tr:hover {
  background: var(--bg-main);
}

:global(:root:not(.dark)) .cells-table tbody tr:hover {
  background: var(--bg-main-light);
}

.cells-table .cell-id {
  font-weight: 600;
  color: var(--accent-blue);
}

/* 置信度样式 */
.cells-table .conf {
  font-family: 'Monaco', 'Consolas', monospace;
  font-weight: 600;
}

.cells-table .conf-high {
  color: var(--accent-green);
}

:global(:root:not(.dark)) .cells-table .conf-high {
  color: var(--accent-green-light);
}

.cells-table .conf-medium {
  color: var(--accent-orange);
}

:global(:root:not(.dark)) .cells-table .conf-medium {
  color: var(--accent-orange-light);
}

.cells-table .conf-low {
  color: var(--accent-red);
}

:global(:root:not(.dark)) .cells-table .conf-low {
  color: var(--accent-red-light);
}

/* 滚动条样式 */
.cells-table-container::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.cells-table-container::-webkit-scrollbar-track {
  background: var(--bg-main);
}

.cells-table-container::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 5px;
}

.cells-table-container::-webkit-scrollbar-thumb:hover {
  background: var(--border-hover);
}

.cells-table-container::-webkit-scrollbar-corner {
  background: var(--bg-main);
}
</style>