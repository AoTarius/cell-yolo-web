import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

export type AnalysisStatus = 'uploading' | 'processing' | 'completed' | 'failed'

// ==========================================
// 类型定义（保持原有）
// ==========================================
export interface Position {
  x: number
  y: number
}

export interface Velocity {
  vx: number
  vy: number
  speed: number
}

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
}

export interface CellFrameData {
  frame_number: number
  position: Position
  area: number
  velocity: Velocity
  bounding_box: BoundingBox
}

export interface CellData {
  cell_id: string
  first_frame: number
  last_frame: number
  frame_count: number
  avg_width: number
  avg_height: number
  avg_conf: number
  avg_velocity: number
  frames: CellFrameData[]
  rawMetrics?: any[]
  avgVisibility?: number
  cellClass?: number
}

export interface ProcessResult {
  output_video_path: string
  cell_count: number
  total_frames: number
  video_duration: number
  model_name: string
  cells: CellData[]
}

export interface AnalysisRecord {
  task_id: string
  task_name?: string
  video_name: string
  video_path: string
  status: AnalysisStatus
  progress: number
  start_time: Date
  end_time?: Date
  result?: ProcessResult
  model_name?: string
  stage?: string
  message?: string
  currentFrame?: number
  totalFrames?: number
}

// ==========================================
// Store 定义
// ==========================================
export const useAnalysisStore = defineStore('analysis', () => {
  // ==========================================
  // 状态
  // ==========================================
  const records = ref<AnalysisRecord[]>([])
  const selectedId = ref<string | null>(null)
  const sortConditions = ref<Array<{ id: string; field: string; direction: string }>>([
    { id: '1', field: 'createdAt', direction: 'desc' }
  ])
  const selectedCellId = ref<string | null>(null)
  const compareRecords = ref<AnalysisRecord[]>([])

  // 缓存机制
  const cellsCache = new Map<string, CellData[]>()
  const cellDetailCache = new Map<string, CellData>()

  // ==========================================
  // 图表专用缓存（新增）
  // ==========================================
  const chartDataCache = ref<Map<string, {
    cells: CellData[],
    filteredCells: CellData[],
    config: any,
    timestamp: number
  }>>(new Map())

  const CACHE_TTL = 5 * 60 * 1000 // 5分钟

  // ==========================================
  // 计算属性
  // ==========================================
  const selectedRecord = computed(() => {
    if (!selectedId.value) return null
    return records.value.find((r) => r.task_id === selectedId.value) || null
  })

  const selectedCellData = computed(() => {
    if (!selectedCellId.value || !selectedRecord.value?.result?.cells) {
      return null
    }
    return selectedRecord.value.result.cells.find(
      (cell) => cell.cell_id === selectedCellId.value
    ) || null
  })

  // ==========================================
  // 基础操作函数（保持原有）
  // ==========================================
  function selectRecord(id: string) {
    selectedId.value = id
    selectedCellId.value = null
    clearCellsCache()
    clearChartDataCache() // 同时清空图表缓存
  }

  function clearCellsCache() {
    cellsCache.clear()
  }

  function clearCellDetailCache() {
    cellDetailCache.clear()
  }

  function clearAllCaches() {
    cellsCache.clear()
    cellDetailCache.clear()
    clearChartDataCache()
  }

  function clearChartDataCache() {
    chartDataCache.value.clear()
  }

  function setSortConditions(conditions: Array<{ id: string; field: string; direction: string }>) {
    sortConditions.value = conditions
  }

  function clearSelection() {
    selectedId.value = null
    selectedCellId.value = null
  }

  function selectCell(cellId: string) {
    selectedCellId.value = cellId
  }

  function backToResultList() {
    selectedCellId.value = null
  }

  function goToCompareResult(recordA: AnalysisRecord | undefined, recordB: AnalysisRecord | undefined, router: any) {
    if (!recordA || !recordB) {
      console.error('缺少对比记录')
      return
    }
    compareRecords.value = [recordA, recordB]
    router.push({ name: 'compareResult' })
  }

  function backToCompareList(router: any) {
    compareRecords.value = []
    router.push({ name: 'compare' })
  }

  // ==========================================
  // 历史任务加载（保持原有）
  // ==========================================
  async function loadHistoryTasks() {
    try {
      const { useUserStore } = await import('./userStore')
      const userStore = useUserStore()

      if (!userStore.currentUser?.username) {
        console.error('未登录用户，无法加载任务列表')
        records.value = []
        return
      }

      const response = await axios.get('/api/tasks/', {
        params: {
          username: userStore.currentUser.username,
          sort_by: JSON.stringify(sortConditions.value)
        }
      })
      const historyTasks = response.data.tasks || []

      const convertedRecords: AnalysisRecord[] = historyTasks.map((task: any) => {
        const modelNameFromDB = task.model_display_name || ''
        const taskNameFromDB = task.task_name || null

        if (task.status === 'processing') {
          return {
            task_id: task.task_id,
            task_name: taskNameFromDB,
            video_name: task.video_name || 'Unknown',
            video_path: task.original_video_path || '',
            status: 'processing' as AnalysisStatus,
            progress: task.progress || 0,
            start_time: new Date(task.created_at),
            model_name: modelNameFromDB,
          }
        } else {
          const result: ProcessResult = {
            output_video_path: task.result?.annotated_video_path || '',
            cell_count: task.result?.cell_count || 0,
            total_frames: task.result?.total_frames || 0,
            video_duration: task.result?.video_duration || 0,
            model_name: task.result?.model_name || 'best_split.pt',
            cells: task.result?.cells || [],
          }

          return {
            task_id: task.task_id,
            task_name: taskNameFromDB,
            video_name: task.video_name || 'Unknown',
            video_path: task.result?.original_video_path || '',
            status: 'completed' as AnalysisStatus,
            progress: 100,
            start_time: new Date(task.created_at),
            end_time: new Date(),
            result,
            model_name: modelNameFromDB,
          }
        }
      })

      records.value = convertedRecords
    } catch (error) {
      console.error('加载历史任务失败:', error)
      records.value = []
    }
  }

  // ==========================================
  // 记录管理（保持原有）
  // ==========================================
  function addRecord(videoName: string, _videoFile: File) {
    const taskId = `task_${Date.now()}`
    const newRecord: AnalysisRecord = {
      task_id: taskId,
      video_name: videoName,
      video_path: `/uploads/${videoName}`,
      status: 'processing',
      progress: 0,
      start_time: new Date(),
    }
    records.value.unshift(newRecord)
    selectedId.value = newRecord.task_id

    const progressInterval = setInterval(() => {
      const record = records.value.find((r) => r.task_id === taskId)
      if (record && record.progress < 100) {
        record.progress += 10
      }
    }, 300)

    setTimeout(() => {
      clearInterval(progressInterval)
      const record = records.value.find((r) => r.task_id === taskId)
      if (record) {
        record.status = 'completed'
        record.progress = 100
        record.end_time = new Date()
        const cellCount = Math.floor(Math.random() * 50) + 10
        const totalFrames = Math.floor(Math.random() * 300) + 100
        record.result = {
          output_video_path: `/outputs/${videoName.replace(/\.[^/.]+$/, '')}_annotated.mp4`,
          cell_count: cellCount,
          total_frames: totalFrames,
          video_duration: totalFrames / 30,
          model_name: 'best_split.pt',
          cells: [],
        }
      }
    }, 3000)
  }

  function addUploadedRecord(record: AnalysisRecord) {
    records.value.unshift(record)
    selectedId.value = record.task_id
  }

  function updateTaskStatus(taskId: string, updates: { status?: AnalysisStatus; progress?: number }) {
    const record = records.value.find((r) => r.task_id === taskId)
    if (record) {
      if (updates.status !== undefined) record.status = updates.status
      if (updates.progress !== undefined) record.progress = updates.progress
      if (updates.status === 'completed') record.end_time = new Date()
    }
  }

  function updateTaskResult(taskId: string, result: ProcessResult) {
    const record = records.value.find((r) => r.task_id === taskId)
    if (record) {
      record.result = result
      record.status = 'completed'
      record.progress = 100
      record.end_time = new Date()
    }
  }

  async function deleteRecord(taskId: string) {
    try {
      await axios.delete(`/api/delete/${taskId}/`)
      const index = records.value.findIndex((r) => r.task_id === taskId)
      if (index !== -1) records.value.splice(index, 1)
      if (selectedId.value === taskId) selectedId.value = null
      return true
    } catch (error: any) {
      console.error('删除记录失败:', error)
      throw new Error(error.response?.data?.error || '删除失败')
    }
  }

  function addProcessingRecord(record: AnalysisRecord) {
    records.value.unshift(record)
  }

  function updateTaskProgress(
    taskId: string,
    updates: { progress?: number; stage?: string; message?: string; currentFrame?: number; totalFrames?: number }
  ) {
    const record = records.value.find((r) => r.task_id === taskId)
    if (record) {
      if (updates.progress !== undefined) record.progress = updates.progress
      if (updates.stage !== undefined) record.stage = updates.stage
      if (updates.message !== undefined) record.message = updates.message
      if (updates.currentFrame !== undefined) record.currentFrame = updates.currentFrame
      if (updates.totalFrames !== undefined) record.totalFrames = updates.totalFrames
    }
  }

  // ==========================================
  // 轮询控制（保持原有）
  // ==========================================
  let pollIntervalId: number | null = null

  function startGlobalPolling() {
    if (pollIntervalId !== null) return

    pollIntervalId = window.setInterval(async () => {
      const processingTasks = records.value.filter((r) => r.status === 'processing')
      if (processingTasks.length === 0) return

      const pollPromises = processingTasks.map(async (task) => {
        try {
          const response = await axios.get(`/api/status/${task.task_id}/`)
          const data = response.data

          updateTaskProgress(task.task_id, {
            progress: data.progress || 0,
            stage: data.stage || '',
            message: data.message || '',
            currentFrame: data.current_frame || null,
            totalFrames: data.total_frames || null,
          })

          if (data.status === 'completed') {
            updateTaskStatus(task.task_id, { status: 'completed', progress: 100 })
            const resultResponse = await axios.get(`/api/result/${task.task_id}/`)
            const result = resultResponse.data
            const record = records.value.find((r) => r.task_id === task.task_id)
            if (record) {
              if (result.original_video_path) record.video_path = result.original_video_path
              record.result = {
                output_video_path: result.annotated_video_path || '',
                cell_count: result.cell_count || 0,
                total_frames: result.total_frames || 0,
                video_duration: result.video_duration || 0,
                model_name: result.model_name || 'best_split.pt',
                cells: result.cells || [],
              }
              record.end_time = new Date()
            }
          } else if (data.status === 'failed') {
            updateTaskStatus(task.task_id, { status: 'failed' })
          }
        } catch (error) {
          console.error(`轮询任务 ${task.task_id} 失败:`, error)
        }
      })

      await Promise.all(pollPromises)
    }, 2000)
  }

  function stopGlobalPolling() {
    if (pollIntervalId !== null) {
      clearInterval(pollIntervalId)
      pollIntervalId = null
    }
  }

  startGlobalPolling()

  // ==========================================
  // 数据聚合函数（保持原有）
  // ==========================================
  function aggregateCells(rawCells: any[]): CellData[] {
    const cellGroups = new Map<number, any[]>()

    for (const cell of rawCells) {
      const trackId = cell.track_id
      if (!cellGroups.has(trackId)) {
        cellGroups.set(trackId, [])
      }
      cellGroups.get(trackId)!.push(cell)
    }

    const aggregatedCells: CellData[] = []

    for (const [trackId, cells] of cellGroups.entries()) {
      const frames = cells.map((c: any) => c.frame)
      const widths = cells.map((c: any) => c.bb_width)
      const heights = cells.map((c: any) => c.bb_height)
      const confidences = cells.map((c: any) => c.conf)
      const velocities = cells.map((c: any) => c.speed || 0)
      const visibilities = cells.map((c: any) => c.visibility ?? 1)

      const firstFrame = Math.min(...frames)
      const lastFrame = Math.max(...frames)
      const frameCount = frames.length
      const avgWidth = widths.reduce((a: number, b: number) => a + b, 0) / widths.length
      const avgHeight = heights.reduce((a: number, b: number) => a + b, 0) / heights.length
      const avgConf = confidences.reduce((a: number, b: number) => a + b, 0) / confidences.length
      const avgVelocity = velocities.reduce((a: number, b: number) => a + b, 0) / velocities.length
      const avgVisibility = visibilities.reduce((a: number, b: number) => a + b, 0) / visibilities.length
      const cellClass = cells[0]?.class_id ?? 0

      const framesData: CellFrameData[] = cells.map((c: any) => {
        const metrics = c.metrics_json || {}
        return {
          frame_number: c.frame,
          position: {
            x: metrics.center?.cx ?? (c.bb_left + c.bb_width / 2),
            y: metrics.center?.cy ?? (c.bb_top + c.bb_height / 2)
          },
          area: c.area || (c.bb_width * c.bb_height),
          velocity: {
            vx: metrics.motion?.vx ?? 0,
            vy: metrics.motion?.vy ?? 0,
            speed: metrics.motion?.migration_speed ?? c.speed ?? 0
          },
          bounding_box: {
            x: metrics.bbox?.left ?? c.bb_left,
            y: metrics.bbox?.top ?? c.bb_top,
            width: metrics.bbox?.width ?? c.bb_width,
            height: metrics.bbox?.height ?? c.bb_height
          }
        }
      })

      const rawMetrics = cells.map((c: any) => c.metrics_json || {})

      aggregatedCells.push({
        cell_id: String(trackId),
        first_frame: firstFrame,
        last_frame: lastFrame,
        frame_count: frameCount,
        avg_width: avgWidth,
        avg_height: avgHeight,
        avg_conf: avgConf,
        avg_velocity: avgVelocity,
        frames: framesData,
        rawMetrics: rawMetrics,
        avgVisibility: avgVisibility,
        cellClass: cellClass
      })
    }

    aggregatedCells.sort((a, b) => {
      const aId = parseInt(a.cell_id.replace(/\D/g, '') || '0', 10)
      const bId = parseInt(b.cell_id.replace(/\D/g, '') || '0', 10)
      return aId - bId
    })

    return aggregatedCells
  }

  // ==========================================
  // 细胞数据加载（保持原有）
  // ==========================================
  async function loadCellsByTask(taskId: string): Promise<CellData[]> {
    if (cellsCache.has(taskId)) {
      return cellsCache.get(taskId)!
    }

    try {
      const response = await axios.get(`/api/cells/${taskId}/`)
      if (response.data.success && response.data.data) {
        const cells = aggregateCells(response.data.data)
        cellsCache.set(taskId, cells)
        return cells
      }
      return []
    } catch (error) {
      console.error('加载细胞数据失败:', error)
      return []
    }
  }

  type RawCellFrame = {
    frame: number
    track_id: number
    bb_left: number
    bb_top: number
    bb_width: number
    bb_height: number
    conf: number
    class_id: number
    visibility: number | null
    area: number
    speed: number
    tracking_persistence: number
    metrics_json: any
  }

  function transformCellData(rawFrames: RawCellFrame[]): CellData {
    if (rawFrames.length === 0) {
      throw new Error('No frame data provided')
    }

    const frames = rawFrames.map(r => r.frame)
    const widths = rawFrames.map(r => r.bb_width)
    const heights = rawFrames.map(r => r.bb_height)
    const confidences = rawFrames.map(r => r.conf)
    const velocities = rawFrames.map(r => r.speed || 0)
    const visibilities = rawFrames.map(r => r.visibility ?? 1)

    const firstFrame = Math.min(...frames)
    const lastFrame = Math.max(...frames)
    const frameCount = frames.length
    const avgWidth = widths.reduce((a, b) => a + b, 0) / widths.length
    const avgHeight = heights.reduce((a, b) => a + b, 0) / heights.length
    const avgConf = confidences.reduce((a, b) => a + b, 0) / confidences.length
    const avgVelocity = velocities.reduce((a, b) => a + b, 0) / velocities.length
    const avgVisibility = visibilities.reduce((a, b) => a + b, 0) / visibilities.length
    const cellClass = rawFrames[0]!.class_id

    const framesData: CellFrameData[] = rawFrames.map(r => {
      const metrics = r.metrics_json || {}
      return {
        frame_number: r.frame,
        position: {
          x: metrics.center?.cx ?? (r.bb_left + r.bb_width / 2),
          y: metrics.center?.cy ?? (r.bb_top + r.bb_height / 2)
        },
        area: r.area || (r.bb_width * r.bb_height),
        velocity: {
          vx: metrics.motion?.vx ?? 0,
          vy: metrics.motion?.vy ?? 0,
          speed: metrics.motion?.migration_speed ?? r.speed ?? 0
        },
        bounding_box: {
          x: metrics.bbox?.left ?? r.bb_left,
          y: metrics.bbox?.top ?? r.bb_top,
          width: metrics.bbox?.width ?? r.bb_width,
          height: metrics.bbox?.height ?? r.bb_height
        }
      }
    })

    return {
      cell_id: String(rawFrames[0]!.track_id),
      first_frame: firstFrame,
      last_frame: lastFrame,
      frame_count: frameCount,
      avg_width: avgWidth,
      avg_height: avgHeight,
      avg_conf: avgConf,
      avg_velocity: avgVelocity,
      frames: framesData,
      rawMetrics: rawFrames.map(r => r.metrics_json || {}),
      avgVisibility,
      cellClass
    }
  }

  async function loadCellDetail(taskId: string, trackId: string): Promise<CellData | null> {
    const cacheKey = `${taskId}_${trackId}`
    if (cellDetailCache.has(cacheKey)) {
      return cellDetailCache.get(cacheKey)!
    }

    try {
      const response = await axios.get(`/api/cells/${taskId}/${trackId}/`)
      if (response.data.success && response.data.data) {
        const cellDetail = transformCellData(response.data.data)
        cellDetailCache.set(cacheKey, cellDetail)
        return cellDetail
      }
      return null
    } catch (error) {
      console.error('加载细胞详情失败:', error)
      return null
    }
  }

  // ==========================================
  // 图表专用函数（新增，全部在 store 内部）
  // ==========================================

  // 图表数据获取（带缓存）
  async function getCellsForChart(taskId: string, forceRefresh = false): Promise<CellData[]> {
    const cached = chartDataCache.value.get(taskId)
    if (!forceRefresh && cached && (Date.now() - cached.timestamp < CACHE_TTL)) {
      console.log('使用图表缓存数据')
      return cached.cells
    }

    let cells: CellData[]
    if (cellsCache.has(taskId)) {
      cells = cellsCache.get(taskId)!
    } else {
      cells = await loadCellsByTask(taskId)
    }

    chartDataCache.value.set(taskId, {
      cells,
      filteredCells: cells,
      config: null,
      timestamp: Date.now()
    })

    return cells
  }

  // 细胞筛选函数
  function filterCells(
    cells: CellData[],
    config: {
      cellSelection: 'top' | 'range' | 'all'
      sortBy?: string
      topN?: number
      cellRange?: [number, number]
    }
  ): CellData[] {
    let result = [...cells]

    if (config.cellSelection === 'top' && config.sortBy && config.topN) {
      result.sort((a, b) => {
        const aVal = getCellSortValue(a, config.sortBy!)
        const bVal = getCellSortValue(b, config.sortBy!)
        return bVal - aVal
      })
      result = result.slice(0, config.topN)
    }

    if (config.cellSelection === 'range' && config.cellRange) {
      const [start, end] = config.cellRange
      result = result.filter(c => {
        const id = parseInt(c.cell_id.replace(/\D/g, '') || '0', 10)
        return id >= start && id <= end
      })
    }

    return result
  }

  // 提取排序值
  function getCellSortValue(cell: CellData, sortBy: string): number {
    switch (sortBy) {
      case 'tracking_duration':
      case 'frame_count':
        return cell.frame_count
      case 'area':
        return cell.frames.reduce((s, f) => s + f.area, 0) / cell.frames.length
      case 'speed':
      case 'velocity':
        return cell.avg_velocity
      case 'circularity':
        return cell.rawMetrics?.reduce((s, m) => s + (m.shape?.circularity || 0), 0) / (cell.rawMetrics?.length || 1) || 0
      case 'aspect_ratio':
        return cell.rawMetrics?.reduce((s, m) => s + (m.shape?.aspect_ratio || 0), 0) / (cell.rawMetrics?.length || 1) || 0
      case 'perimeter':
        return cell.rawMetrics?.reduce((s, m) => s + (m.shape?.perimeter || 0), 0) / (cell.rawMetrics?.length || 1) || 0
      case 'distance':
        return cell.rawMetrics?.reduce((s, m) => s + (m.motion?.distance || 0), 0) / (cell.rawMetrics?.length || 1) || 0
      case 'migration_speed':
        return cell.avg_velocity
      case 'mean_square_displacement':
        return cell.rawMetrics?.reduce((s, m) => s + (m.motion?.mean_square_displacement || 0), 0) / (cell.rawMetrics?.length || 1) || 0
      default:
        return 0
    }
  }

function extractFeatureValue(cell: CellData, feature: string, frameIndex?: number): number {
  // 指定帧模式
  if (frameIndex !== undefined) {
    if (frameIndex < 0 || frameIndex >= cell.frames.length) {
      console.warn(`帧索引 ${frameIndex} 超出范围 [0, ${cell.frames.length - 1}]`)
      return 0
    }

    const frame = cell.frames[frameIndex]
    if (!frame) {
      console.warn(`帧 ${frameIndex} 数据不存在`)
      return 0
    }

    const metrics = cell.rawMetrics?.[frameIndex]

    switch (feature) {
      case 'area': 
        return frame.area ?? 0
      case 'speed': 
        return frame.velocity?.speed ?? 0
      case 'perimeter': 
        return metrics?.shape?.perimeter ?? 0
      case 'circularity': 
        return metrics?.shape?.circularity ?? 0
      case 'aspect_ratio': 
        return metrics?.shape?.aspect_ratio ?? 0
      case 'distance': 
        return metrics?.motion?.distance ?? 0
      case 'migration_speed': 
        // 优先使用 metrics 中的值，回退到 frame.velocity.speed
        return metrics?.motion?.migration_speed ?? frame.velocity?.speed ?? 0
      case 'mean_square_displacement': 
        return metrics?.motion?.mean_square_displacement ?? 0
      default: 
        return 0
    }
  }
  
  // 平均模式（原有代码）...
  switch (feature) {
    case 'area':
      return cell.frames.length > 0 
        ? cell.frames.reduce((s, f) => s + (f.area ?? 0), 0) / cell.frames.length 
        : 0
    case 'speed':
    case 'migration_speed':
      return cell.avg_velocity ?? 0
    case 'perimeter':
    case 'circularity':
    case 'aspect_ratio':
    case 'distance':
    case 'mean_square_displacement':
      return getCellSortValue(cell, feature)
    default:
      return 0
  }
}

  // ==========================================
  // 导出（新增图表函数）
  // ==========================================
  return {
    records,
    selectedId,
    selectedRecord,
    selectedCellId,
    selectedCellData,
    compareRecords,
    sortConditions,
    selectRecord,
    clearSelection,
    addRecord,
    selectCell,
    backToResultList,
    goToCompareResult,
    backToCompareList,
    addUploadedRecord,
    updateTaskStatus,
    updateTaskResult,
    loadHistoryTasks,
    deleteRecord,
    addProcessingRecord,
    updateTaskProgress,
    startGlobalPolling,
    stopGlobalPolling,
    setSortConditions,
    aggregateCells,
    loadCellsByTask,
    loadCellDetail,
    clearCellsCache,
    clearCellDetailCache,
    clearAllCaches,
    // 图表专用导出
    chartDataCache,
    getCellsForChart,
    filterCells,
    extractFeatureValue,
    clearChartDataCache,
    getCellSortValue,
  }
})