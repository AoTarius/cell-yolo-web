<script setup lang="ts">
import '@/assets/styles/colors.css'
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useAnalysisStore, type CellData } from '@/stores/analysisStore'
import { useAnalysisApi } from '@/composables/useAnalysisApi'
import { useToast } from '@/composables/useToast'
import { useRouter, useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { buildOption, filterDataFields as cbFilterDataFields } from '@/lib/chartBuilder'

const store = useAnalysisStore()
const api = useAnalysisApi()
const { showToast } = useToast()
const router = useRouter()
const route = useRoute()
const COMPARE_FRAME_STATE_KEY = 'compareResultFrameState'

// 从store中获取对比记录
const recordA = computed(() => store.compareRecords[0])
const recordB = computed(() => store.compareRecords[1])

// 检查是否有有效的对比记录
const hasValidRecords = computed(() => recordA.value && recordB.value)
const isFrameSyncMode = computed(() => route.query.syncFrames === '1')
const isModelCompareMode = computed(() => route.query.compareMode === 'model')

// 组件挂载时，如果没有有效记录，返回对比页面
onMounted(() => {
  if (!hasValidRecords.value) {
    router.push({ name: isModelCompareMode.value ? 'resourceManage' : 'compare' })
  } else {
    restoreFrameState()
    alignFrameIndexesForSync()
    // 根据恢复后的帧号加载图像
    if (recordA.value?.task_id) {
      loadImageA()
    }
    if (recordB.value?.task_id) {
      loadImageB()
    }
  }
})

// 图片显示
const displayedImageUrlA = ref('')
const displayedImageUrlB = ref('')

// 图片加载状态
const isImageLoadingA = ref(false)
const isImageLoadingB = ref(false)

// 响应式的当前帧号（各自独立）
const currentFrameIndexA = ref(0)
const currentFrameIndexB = ref(0)

function clampFrameIndex(index: number, totalFrames: number) {
  if (!Number.isFinite(index) || totalFrames <= 0) return 0
  return Math.min(Math.max(0, Math.floor(index)), totalFrames - 1)
}

function saveFrameState() {
  if (!recordA.value?.task_id || !recordB.value?.task_id) return

  const payload = {
    taskIdA: String(recordA.value.task_id),
    taskIdB: String(recordB.value.task_id),
    frameIndexA: currentFrameIndexA.value,
    frameIndexB: currentFrameIndexB.value,
    updatedAt: Date.now(),
  }

  sessionStorage.setItem(COMPARE_FRAME_STATE_KEY, JSON.stringify(payload))
}

function restoreFrameState() {
  if (!recordA.value?.task_id || !recordB.value?.task_id) return

  const raw = sessionStorage.getItem(COMPARE_FRAME_STATE_KEY)
  if (!raw) return

  try {
    const parsed = JSON.parse(raw)
    const taskIdA = String(recordA.value.task_id)
    const taskIdB = String(recordB.value.task_id)
    if (parsed?.taskIdA !== taskIdA || parsed?.taskIdB !== taskIdB) return

    const totalA = Number(recordA.value?.result?.total_frames || 0)
    const totalB = Number(recordB.value?.result?.total_frames || 0)
    currentFrameIndexA.value = clampFrameIndex(Number(parsed?.frameIndexA ?? 0), totalA)
    currentFrameIndexB.value = clampFrameIndex(Number(parsed?.frameIndexB ?? 0), totalB)
  } catch {
    // ignore bad state cache
  }
}

function getSyncTotalFrames() {
  const totalA = Number(recordA.value?.result?.total_frames || 0)
  const totalB = Number(recordB.value?.result?.total_frames || 0)
  if (totalA <= 0 || totalB <= 0) return 0
  return Math.min(totalA, totalB)
}

function setSyncedFrameIndex(frameIndex: number) {
  const syncTotal = getSyncTotalFrames()
  if (syncTotal <= 0) return

  const target = clampFrameIndex(frameIndex, syncTotal)
  currentFrameIndexA.value = target
  currentFrameIndexB.value = target
  loadImageA()
  loadImageB()
}

function alignFrameIndexesForSync() {
  if (!isFrameSyncMode.value) return
  const syncTotal = getSyncTotalFrames()
  if (syncTotal <= 0) return

  const aligned = clampFrameIndex(Math.min(currentFrameIndexA.value, currentFrameIndexB.value), syncTotal)
  currentFrameIndexA.value = aligned
  currentFrameIndexB.value = aligned
}

const isExporting = ref(false)
const exportError = ref<string | null>(null)

type CompareChartType = 'timeSeries' | 'histogram' | 'scatter' | 'trajectory'

const chartTypeA = ref<CompareChartType>('scatter')
const chartTypeB = ref<CompareChartType>('scatter')
const chartImageA = ref('')
const chartImageB = ref('')
const chartLabelA = ref('')
const chartLabelB = ref('')
const chartRenderTypeA = ref<CompareChartType>('scatter')
const chartRenderTypeB = ref<CompareChartType>('scatter')
const chartImageVariantA = ref<'wide' | 'square' | ''>('')
const chartImageVariantB = ref<'wide' | 'square' | ''>('')

const featureOptions = [
  { label: '面积', value: 'area' },
  { label: '速度', value: 'speed' },
  { label: '迁移速度', value: 'migration_speed' },
]

const chartConfigModalVisible = ref(false)
const chartConfigSlot = ref<'A' | 'B' | null>(null)
const chartConfigType = ref<CompareChartType>('scatter')
const chartConfigDraft = ref<Record<string, any>>({})
const chartConfigFramesText = ref('2,25,50,75')

const slotConfigs = ref({
  A: {
    timeSeries: getDefaultConfigByType('timeSeries') as Record<string, any>,
    histogram: getDefaultConfigByType('histogram') as Record<string, any>,
    scatter: getDefaultConfigByType('scatter') as Record<string, any>,
    trajectory: getDefaultConfigByType('trajectory') as Record<string, any>,
  },
  B: {
    timeSeries: getDefaultConfigByType('timeSeries') as Record<string, any>,
    histogram: getDefaultConfigByType('histogram') as Record<string, any>,
    scatter: getDefaultConfigByType('scatter') as Record<string, any>,
    trajectory: getDefaultConfigByType('trajectory') as Record<string, any>,
  },
})

const chartTypeOptions: Array<{ label: string; value: CompareChartType }> = [
  { label: '折线图', value: 'timeSeries' },
  { label: '直方图', value: 'histogram' },
  { label: '散点图', value: 'scatter' },
  { label: '轨迹图', value: 'trajectory' },
]

function getDefaultConfigByType(type: CompareChartType) {
  if (type === 'timeSeries') {
    return {
      yAxisFeature: 'area',
      cellSelection: 'top',
      sortBy: 'tracking_duration',
      topN: 10,
      lineType: 'smooth',
      showDataPoints: false,
    }
  }

  if (type === 'histogram') {
    return {
      xAxisFeature: 'area',
      statMode: 'average',
      frameMode: 'single',
      selectedFrame: 2,
      binCount: 12,
      probabilityType: 'probability',
    }
  }

  if (type === 'trajectory') {
    return {
      trajectoryType: 'normalized',
      colorMap: 'time',
      cellSelection: 'top',
      sortBy: 'tracking_duration',
      topN: 10,
      lineWidth: 2,
      showStartPoint: false,
      showEndPoint: false,
      fadeEffect: false,
    }
  }

  return {
    frameMode: 'single',
    selectedFrame: 2,
    pointSize: 8,
    colorBy: 'cell_id',
    showTrajectory: false,
    trajectoryLength: 10,
  }
}

function loadCompareChartCache() {
  const aRaw = sessionStorage.getItem('compareChartSlot_A')
  const bRaw = sessionStorage.getItem('compareChartSlot_B')

  if (aRaw) {
    try {
      const parsed = JSON.parse(aRaw)
      if (parsed?.taskId === recordA.value?.task_id) {
        const parsedType = (parsed.chartType || 'scatter') as CompareChartType
        // ignore stale 3D backend exports or blob urls for compare (compare supports normalized only)
        const labelLower = String(parsed.chartLabel || '').toLowerCase()
        const imgUrl = parsed.imageDataUrl || ''
        if (parsedType === 'trajectory' && (labelLower.includes('3d') || String(imgUrl).startsWith('blob:'))) {
          // skip using this cached image
        } else {
          chartImageA.value = imgUrl
          chartLabelA.value = parsed.chartLabel || ''
          chartRenderTypeA.value = parsedType
          chartTypeA.value = parsedType
        }
        
        // set image variant for proper display
        const cfgA = slotConfigs.value.A?.[parsedType]
            if (parsedType === 'timeSeries' || parsedType === 'histogram') chartImageVariantA.value = 'wide'
            else if (parsedType === 'scatter') chartImageVariantA.value = 'square'
            else if (parsedType === 'trajectory') chartImageVariantA.value = 'square'
      }
    } catch {
      // ignore bad cache
    }
  }

  if (bRaw) {
    try {
      const parsed = JSON.parse(bRaw)
      if (parsed?.taskId === recordB.value?.task_id) {
        const parsedType = (parsed.chartType || 'scatter') as CompareChartType
        const labelLower = String(parsed.chartLabel || '').toLowerCase()
        const imgUrl = parsed.imageDataUrl || ''
        if (parsedType === 'trajectory' && (labelLower.includes('3d') || String(imgUrl).startsWith('blob:'))) {
          // skip stale 3D cached image
        } else {
          chartImageB.value = imgUrl
          chartLabelB.value = parsed.chartLabel || ''
          chartRenderTypeB.value = parsedType
          chartTypeB.value = parsedType
        }
        const cfgB = slotConfigs.value.B?.[parsedType]
        if (parsedType === 'timeSeries' || parsedType === 'histogram') chartImageVariantB.value = 'wide'
        else if (parsedType === 'scatter') chartImageVariantB.value = 'square'
        else if (parsedType === 'trajectory') chartImageVariantB.value = 'square'
      }
    } catch {
      // ignore bad cache
    }
  }
}

function goToChartDrawing(slot: 'A' | 'B') {
  const record = slot === 'A' ? recordA.value : recordB.value
  const chartType = slot === 'A' ? chartTypeA.value : chartTypeB.value
  if (!record?.task_id) return

  const config = slotConfigs.value[slot][chartType]
  router.push({
    name: 'drawingCanvas',
    query: {
      type: chartType,
      taskId: record.task_id,
      config: JSON.stringify(config),
      returnTo: 'compareResult',
      compareSlot: slot,
      compareTaskName: record.task_name || '',
    },
  })
}

function openChartConfigModal(slot: 'A' | 'B') {
  const type = slot === 'A' ? chartTypeA.value : chartTypeB.value
  chartConfigSlot.value = slot
  chartConfigType.value = type
  chartConfigDraft.value = JSON.parse(JSON.stringify(slotConfigs.value[slot][type]))
  chartConfigFramesText.value = Array.isArray(chartConfigDraft.value.selectedFrames)
    ? chartConfigDraft.value.selectedFrames.join(',')
    : '2,25,50,75'
  chartConfigModalVisible.value = true
}

function confirmChartConfigAndDraw() {
  if (!chartConfigSlot.value) return

  if (chartConfigType.value === 'histogram') {
    chartConfigDraft.value.frameMode = 'single'
  }

  if (chartConfigType.value === 'scatter') {
    // Compare should always use single-frame scatter; normalize selectedFrame
    chartConfigDraft.value.frameMode = 'single'
    const n = Number(chartConfigDraft.value.selectedFrame || 1)
    chartConfigDraft.value.selectedFrame = Number.isFinite(n) ? n : 1
  }

  if (chartConfigType.value === 'trajectory') {
    // Enforce normalized trajectories in compare flow
    chartConfigDraft.value.trajectoryType = 'normalized'
  }

  slotConfigs.value[chartConfigSlot.value][chartConfigType.value] = JSON.parse(JSON.stringify(chartConfigDraft.value))
  applyChartToSlot(chartConfigSlot.value, chartConfigType.value, true)
  chartConfigModalVisible.value = false
}

function closeChartConfigModal() {
  chartConfigModalVisible.value = false
}

watch(chartConfigType, (nextType) => {
  if (!chartConfigSlot.value || !chartConfigModalVisible.value) return
  chartConfigDraft.value = JSON.parse(JSON.stringify(slotConfigs.value[chartConfigSlot.value][nextType]))
  chartConfigFramesText.value = Array.isArray(chartConfigDraft.value.selectedFrames)
    ? chartConfigDraft.value.selectedFrames.join(',')
    : '2,25,50,75'
})

function handleRegenerateA() {
  openChartConfigModal('A')
}

function handleRegenerateB() {
  openChartConfigModal('B')
}

function getFeatureValueByType(frame: any, chartType: CompareChartType, config: Record<string, any>) {
  const feature = chartType === 'histogram'
    ? (config.xAxisFeature || 'area')
    : (config.yAxisFeature || 'area')

  if (feature === 'area') return Number(frame?.area || 0)
  if (feature === 'speed' || feature === 'migration_speed') return Number(frame?.velocity?.speed || 0)
  return Number(frame?.area || 0)
}

function renderBasicChartImage(cells: CellData[], title: string, chartType: CompareChartType, config: Record<string, any>) {
  const canvas = document.createElement('canvas')
  const width = 900
  const height = 520
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')
  if (!ctx) return ''

  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, width, height)

  const marginLeft = 72
  const marginRight = 30
  const marginTop = 60
  const marginBottom = 56
  const plotWidth = width - marginLeft - marginRight
  const plotHeight = height - marginTop - marginBottom

  ctx.fillStyle = '#111827'
  ctx.font = 'bold 24px Arial'
  ctx.fillText(title, marginLeft, 34)

  ctx.strokeStyle = '#d1d5db'
  ctx.lineWidth = 1
  for (let i = 0; i <= 5; i++) {
    const y = marginTop + (plotHeight / 5) * i
    ctx.beginPath()
    ctx.moveTo(marginLeft, y)
    ctx.lineTo(width - marginRight, y)
    ctx.stroke()
  }

  const palette = ['#2563eb', '#16a34a', '#dc2626', '#d97706', '#7c3aed', '#0891b2', '#db2777', '#4b5563']

  ctx.strokeStyle = '#9ca3af'
  ctx.lineWidth = 1.2
  ctx.beginPath()
  ctx.moveTo(marginLeft, marginTop)
  ctx.lineTo(marginLeft, marginTop + plotHeight)
  ctx.lineTo(marginLeft + plotWidth, marginTop + plotHeight)
  ctx.stroke()

  if (chartType === 'scatter') {
    const frameNo = Number(config.selectedFrame || 2)
    const points = cells
      .slice(0, 120)
      .map((cell) => {
        const f = cell.frames.find((x) => Number(x.frame_number) === frameNo)
        if (!f) return null
        return {
          x: Number(f.position?.x ?? 0),
          y: Number(f.position?.y ?? 0),
        }
      })
      .filter((p): p is { x: number; y: number } => !!p)

    if (!points.length) {
      ctx.fillStyle = '#6b7280'
      ctx.font = '18px Arial'
      ctx.fillText('暂无可绘制数据', marginLeft + 20, marginTop + 40)
      return canvas.toDataURL('image/png')
    }

    const xMin = Math.min(...points.map((p) => p.x))
    const xMax = Math.max(...points.map((p) => p.x))
    const yMin = Math.min(...points.map((p) => p.y))
    const yMax = Math.max(...points.map((p) => p.y))
    const xRange = Math.max(1, xMax - xMin)
    const yRange = Math.max(1, yMax - yMin)

    ctx.fillStyle = '#2563eb'
    points.forEach((p) => {
      const x = marginLeft + ((p.x - xMin) / xRange) * plotWidth
      const y = marginTop + plotHeight - ((p.y - yMin) / yRange) * plotHeight
      ctx.beginPath()
      ctx.arc(x, y, 3, 0, Math.PI * 2)
      ctx.fill()
    })

    return canvas.toDataURL('image/png')
  }

  if (chartType === 'histogram') {
    const feature = config.xAxisFeature || 'area'
    const values = cells
      .slice(0, 80)
      .map((cell) => {
        const vals = cell.frames.map((f) => getFeatureValueByType(f, 'histogram', { xAxisFeature: feature }))
        if (!vals.length) return null
        return vals.reduce((s, v) => s + v, 0) / vals.length
      })
      .filter((v): v is number => v !== null && Number.isFinite(v))

    if (!values.length) {
      ctx.fillStyle = '#6b7280'
      ctx.font = '18px Arial'
      ctx.fillText('暂无可绘制数据', marginLeft + 20, marginTop + 40)
      return canvas.toDataURL('image/png')
    }

    const min = Math.min(...values)
    const max = Math.max(...values)
    const binCount = Math.max(5, Number(config.binCount || 12))
    const step = Math.max(1e-6, (max - min) / binCount)
    const bins = Array.from({ length: binCount }, () => 0)
    values.forEach((v) => {
      const idx = Math.min(binCount - 1, Math.max(0, Math.floor((v - min) / step)))
      if (bins[idx] !== undefined) {
        bins[idx] += 1
      }
    })

    const maxBin = Math.max(...bins, 1)
    const barW = plotWidth / binCount
    bins.forEach((b, i) => {
      const h = (b / maxBin) * plotHeight
      const x = marginLeft + i * barW + 2
      const y = marginTop + plotHeight - h
      ctx.fillStyle = '#2563eb'
      ctx.fillRect(x, y, Math.max(2, barW - 4), h)
    })

    return canvas.toDataURL('image/png')
  }

  if (chartType === 'trajectory') {
    const trajectoryType = String(config.trajectoryType || 'normal')
    const sampled = cells.slice(0, Math.min(16, cells.length))
    const series = sampled
      .map((cell) => {
        const frames = cell.frames.slice().sort((a, b) => a.frame_number - b.frame_number)
        if (frames.length < 2) return null

        const baseX = trajectoryType === 'normalized' ? Number(frames[0]?.position?.x ?? 0) : 0
        const baseY = trajectoryType === 'normalized' ? Number(frames[0]?.position?.y ?? 0) : 0

        const points = frames
          .map((f) => ({
            x: Number(f.position?.x ?? 0) - baseX,
            y: Number(f.position?.y ?? 0) - baseY,
          }))
          .filter((p) => Number.isFinite(p.x) && Number.isFinite(p.y))

        return points.length > 1 ? { id: cell.cell_id, points } : null
      })
      .filter((s): s is { id: string; points: Array<{ x: number; y: number }> } => !!s)

    if (!series.length) {
      ctx.fillStyle = '#6b7280'
      ctx.font = '18px Arial'
      ctx.fillText('暂无可绘制轨迹数据', marginLeft + 20, marginTop + 40)
      return canvas.toDataURL('image/png')
    }

    const xVals = series.flatMap((s) => s.points.map((p) => p.x))
    const yVals = series.flatMap((s) => s.points.map((p) => p.y))
    const xMin = Math.min(...xVals)
    const xMax = Math.max(...xVals)
    const yMin = Math.min(...yVals)
    const yMax = Math.max(...yVals)
    const xRange = Math.max(1, xMax - xMin)
    const yRange = Math.max(1, yMax - yMin)

    series.forEach((s, idx) => {
      ctx.strokeStyle = palette[idx % palette.length] || '#2563eb'
      ctx.lineWidth = 2
      ctx.beginPath()
      s.points.forEach((p, pointIdx) => {
        const x = marginLeft + ((p.x - xMin) / xRange) * plotWidth
        const y = marginTop + plotHeight - ((p.y - yMin) / yRange) * plotHeight
        if (pointIdx === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      })
      ctx.stroke()
    })

    return canvas.toDataURL('image/png')
  }

  const sampled = cells.slice(0, Math.min(8, cells.length))
  const series = sampled
    .map((cell) => {
      const points = cell.frames
        .slice()
        .sort((a, b) => a.frame_number - b.frame_number)
        .map((f) => ({ x: Number(f.frame_number), y: getFeatureValueByType(f, chartType, config) }))
        .filter((p) => Number.isFinite(p.x) && Number.isFinite(p.y))
      return { id: cell.cell_id, points }
    })
    .filter((s) => s.points.length > 1)

  if (!series.length) {
    ctx.fillStyle = '#6b7280'
    ctx.font = '18px Arial'
    ctx.fillText('暂无可绘制数据', marginLeft + 20, marginTop + 40)
    return canvas.toDataURL('image/png')
  }

  const xVals = series.flatMap((s) => s.points.map((p) => p.x))
  const yVals = series.flatMap((s) => s.points.map((p) => p.y))
  const xMin = Math.min(...xVals)
  const xMax = Math.max(...xVals)
  const yMin = Math.min(...yVals)
  const yMax = Math.max(...yVals)
  const xRange = Math.max(1, xMax - xMin)
  const yRange = Math.max(1, yMax - yMin)

  series.forEach((s, idx) => {
    ctx.strokeStyle = palette[idx % palette.length] || '#2563eb'
    ctx.lineWidth = 2
    ctx.beginPath()
    s.points.forEach((p, pointIdx) => {
      const x = marginLeft + ((p.x - xMin) / xRange) * plotWidth
      const y = marginTop + plotHeight - ((p.y - yMin) / yRange) * plotHeight
      if (pointIdx === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    })
    ctx.stroke()
  })

  return canvas.toDataURL('image/png')
}

async function renderEchartsImage(cells: CellData[], chartType: CompareChartType, config: Record<string, any>, width = 900, height = 520, opts: Record<string, any> = {}) {
  const container = document.createElement('div')
  container.style.width = `${width}px`
  container.style.height = `${height}px`
  container.style.position = 'fixed'
  container.style.left = '-9999px'
  container.style.top = '-9999px'
  container.style.overflow = 'hidden'
  document.body.appendChild(container)
  const chart = echarts.init(container, undefined, { renderer: 'canvas' })
  try {
    // ensure correct pixel dimensions for rendering
    chart.resize({ width, height })
    // Apply same initial cell filtering as DrawingCanvas (store.filterCells)
    const preFiltered = typeof store.filterCells === 'function' ? store.filterCells(cells, config as any) : cells
    const filtered = cbFilterDataFields(preFiltered, chartType, config)
    const option = buildOption(chartType, filtered, config, opts)
    chart.setOption(option, true)
    // give ECharts a moment to render visuals
    await new Promise((r) => setTimeout(r, 80))
    const pixelRatio = Number(opts.pixelRatio || 2)
    const dataUrl = chart.getDataURL({ pixelRatio, backgroundColor: '#ffffff' })
    return dataUrl
  } finally {
    try { chart.dispose() } catch {}
    try { document.body.removeChild(container) } catch {}
  }
}

async function blobToDataUrl(blob: Blob): Promise<string | null> {
  return await new Promise((resolve) => {
    const reader = new FileReader()
    reader.onload = () => resolve(typeof reader.result === 'string' ? reader.result : null)
    reader.onerror = () => resolve(null)
    reader.readAsDataURL(blob)
  })
}

async function fetch3dBlobWithRetry(taskId: string | number, query: string, attempts = 5): Promise<Blob | null> {
  let delay = 400
  for (let i = 0; i < attempts; i++) {
    try {
      const resp = await fetch(`/api/trajectory-3d/${taskId}/${query}`)
      if (resp.ok) {
        const blob = await resp.blob()
        // basic sanity check: blob size
        if (blob && blob.size > 100) return blob
      } else {
        // if server returns 202 Accepted or 503, wait and retry
        // fallthrough to wait
      }
    } catch (e) {
      // ignore network error and retry
    }
    await new Promise((r) => setTimeout(r, delay))
    delay = Math.min(2000, delay * 1.8)
  }
  return null
}

async function applyChartToSlot(slot: 'A' | 'B', chartType: CompareChartType, forceRegen = false) {
  const cells = slot === 'A' ? allCellsCacheA.value : allCellsCacheB.value
  const taskName = slot === 'A' ? (recordA.value?.task_name || '任务A') : (recordB.value?.task_name || '任务B')
  const config = slotConfigs.value[slot][chartType]
  const titleMap: Record<CompareChartType, string> = {
    timeSeries: '折线图',
    histogram: '直方图',
    scatter: '散点图',
    trajectory: '轨迹图',
  }
  let image = ''
  const record = slot === 'A' ? recordA.value : recordB.value

  // Prefer any existing exported image in sessionStorage for this slot/task/chartType
  if (!forceRegen) {
    try {
      const raw = sessionStorage.getItem(`compareChartSlot_${slot}`)
      if (raw) {
        const parsed = JSON.parse(raw)
        if (parsed?.taskId === record?.task_id && parsed.chartType === chartType && parsed.imageDataUrl) {
          image = parsed.imageDataUrl
        }
      }
    } catch {
      image = ''
    }
  }

  // If no exported image found, attempt ECharts offscreen rendering first, otherwise fallback to canvas
  if (!image) {
    // Special-case: 3D trajectory may be rendered by backend Python service — try fetching it first
    // no backend 3D fetch in compare page; always render locally with ECharts (or fallback canvas)
    try {
      // determine rendering size and font scale to match DrawingCanvas
      const isSquare = chartType === 'scatter' || chartType === 'trajectory'
      const width = isSquare ? 520 : 900
      const height = isSquare ? 520 : 520
      const baseFontSize = Number(sessionStorage.getItem('drawingBaseFontSize') || 14)
      const legendFontSize = Number(sessionStorage.getItem('drawingLegendFontSize') || 12)
      const titleFontSize = Number(sessionStorage.getItem('drawingTitleFontSize') || 16)

      image = await renderEchartsImage(cells, chartType, config, width, height, {
        baseFontSize,
        legendFontSize,
        titleFontSize,
        pixelRatio: 2,
      })
    } catch (err) {
      console.warn('ECharts 离屏渲染失败，退回到 canvas 渲染', err)
      try {
        image = renderBasicChartImage(cells, `${taskName} - ${titleMap[chartType]}`, chartType, config)
      } catch (e) {
        image = ''
      }
    }
  }

  if (slot === 'A') {
    chartTypeA.value = chartType
    chartImageA.value = image
    chartRenderTypeA.value = chartType
    if (chartType === 'timeSeries' || chartType === 'histogram') chartImageVariantA.value = 'wide'
    else if (chartType === 'scatter') chartImageVariantA.value = 'square'
    else if (chartType === 'trajectory') chartImageVariantA.value = 'square'
    chartLabelA.value = `${taskName} · ${titleMap[chartType]}`
  } else {
    chartTypeB.value = chartType
    chartImageB.value = image
    chartRenderTypeB.value = chartType
    if (chartType === 'timeSeries' || chartType === 'histogram') chartImageVariantB.value = 'wide'
    else if (chartType === 'scatter') chartImageVariantB.value = 'square'
    else if (chartType === 'trajectory') chartImageVariantB.value = 'square'
    chartLabelB.value = `${taskName} · ${titleMap[chartType]}`
  }

  if (record?.task_id) {
    sessionStorage.setItem(
      `compareChartSlot_${slot}`,
      JSON.stringify({
        slot,
        taskId: record.task_id,
        chartType,
        chartLabel: slot === 'A' ? chartLabelA.value : chartLabelB.value,
        imageDataUrl: image,
        updatedAt: Date.now(),
      }),
    )
  }
}

watch(chartTypeA, (nextType) => {
  if (!recordA.value?.task_id) return
  applyChartToSlot('A', nextType)
})

watch(chartTypeB, (nextType) => {
  if (!recordB.value?.task_id) return
  applyChartToSlot('B', nextType)
})

function ensureDefaultCharts() {
  if (!chartImageA.value) {
    applyChartToSlot('A', chartTypeA.value)
  }
  if (!chartImageB.value) {
    applyChartToSlot('B', chartTypeB.value)
  }
}

// 加载图片A
function loadImageA() {
  if (!recordA.value?.task_id) {
    return
  }

  const timestamp = Date.now()
  const newUrl = `/api/frame/${recordA.value.task_id}/${currentFrameIndexA.value}/?t=${timestamp}`
  isImageLoadingA.value = true

  const img = new Image()
  img.onload = () => {
    displayedImageUrlA.value = newUrl
    isImageLoadingA.value = false
  }
  img.onerror = () => {
    console.error('帧图片加载失败:', newUrl)
    isImageLoadingA.value = false
  }
  img.src = newUrl
}

// 加载图片B
function loadImageB() {
  if (!recordB.value?.task_id) {
    return
  }

  const timestamp = Date.now()
  const newUrl = `/api/frame/${recordB.value.task_id}/${currentFrameIndexB.value}/?t=${timestamp}`
  isImageLoadingB.value = true

  const img = new Image()
  img.onload = () => {
    displayedImageUrlB.value = newUrl
    isImageLoadingB.value = false
  }
  img.onerror = () => {
    console.error('帧图片加载失败:', newUrl)
    isImageLoadingB.value = false
  }
  img.src = newUrl
}

// 添加响应式变量以存储细胞数据
const allCellsCacheA = ref<CellData[]>([])
const allCellsCacheB = ref<CellData[]>([])
const currentFrameCellsA = ref<CellData[]>([])
const currentFrameCellsB = ref<CellData[]>([])

// 加载任务A的所有细胞数据
async function loadAllCellsA() {
  if (!recordA.value?.task_id) return
  if (allCellsCacheA.value.length > 0) return

  try {
    allCellsCacheA.value = await store.loadCellsByTask(recordA.value.task_id)
  } catch (error) {
    console.error('加载任务A的细胞数据失败:', error)
    allCellsCacheA.value = []
  }
}

// 加载任务B的所有细胞数据
async function loadAllCellsB() {
  if (!recordB.value?.task_id) return
  if (allCellsCacheB.value.length > 0) return

  try {
    allCellsCacheB.value = await store.loadCellsByTask(recordB.value.task_id)
  } catch (error) {
    console.error('加载任务B的细胞数据失败:', error)
    allCellsCacheB.value = []
  }
}

// 加载任务A当前帧的细胞数据
function loadCurrentFrameCellsA() {
  if (!recordA.value?.task_id || allCellsCacheA.value.length === 0) {
    currentFrameCellsA.value = []
    return
  }

  const currentFrameNum = currentFrameIndexA.value + 1
  
  // 筛选并提取当前帧数据
  currentFrameCellsA.value = allCellsCacheA.value
    .map(cell => {
      const frameData = cell.frames.find(f => Number(f.frame_number) === currentFrameNum)
      if (!frameData) return null
      // 返回新对象，只保留当前帧数据在 frames[0]
      return {
        ...cell,
        frames: [frameData]
      }
    })
    .filter((cell): cell is CellData => cell !== null)
}

// 加载任务B当前帧的细胞数据
function loadCurrentFrameCellsB() {
  if (!recordB.value?.task_id || allCellsCacheB.value.length === 0) {
    currentFrameCellsB.value = []
    return
  }

  const currentFrameNum = currentFrameIndexB.value + 1
  
  currentFrameCellsB.value = allCellsCacheB.value
    .map(cell => {
      const frameData = cell.frames.find(f => Number(f.frame_number) === currentFrameNum)
      if (!frameData) return null
      return {
        ...cell,
        frames: [frameData]
      }
    })
    .filter((cell): cell is CellData => cell !== null)
}

// 当帧号变化时更新帧细胞数据
watch(() => currentFrameIndexA.value, () => {
  loadCurrentFrameCellsA()
  saveFrameState()
})
watch(() => currentFrameIndexB.value, () => {
  loadCurrentFrameCellsB()
  saveFrameState()
})

// 组件挂载时加载所有细胞数据
onMounted(async () => {
  if (recordA.value?.task_id) {
    await loadAllCellsA()
    loadCurrentFrameCellsA()
  }
  if (recordB.value?.task_id) {
    await loadAllCellsB()
    loadCurrentFrameCellsB()
  }

  loadCompareChartCache()
  ensureDefaultCharts()
})

// ==================== 视频A的控制函数 ====================
// 视频A下一帧
function handleNextFrameA() {
  if (isFrameSyncMode.value) {
    const syncTotal = getSyncTotalFrames()
    if (currentFrameIndexA.value < syncTotal - 1) {
      setSyncedFrameIndex(currentFrameIndexA.value + 1)
    }
    return
  }

  const totalFrames = recordA.value?.result?.total_frames || 0
  if (currentFrameIndexA.value < totalFrames - 1) {
    currentFrameIndexA.value++
    loadImageA()
  }
}

// 视频A上一帧
function handlePrevFrameA() {
  if (isFrameSyncMode.value) {
    if (currentFrameIndexA.value > 0) {
      setSyncedFrameIndex(currentFrameIndexA.value - 1)
    }
    return
  }

  if (currentFrameIndexA.value > 0) {
    currentFrameIndexA.value--
    loadImageA()
  }
}

// 视频A回到第一帧
function handleGoToFirstFrameA() {
  if (isFrameSyncMode.value) {
    setSyncedFrameIndex(0)
    return
  }

  currentFrameIndexA.value = 0
  loadImageA()
}

// 视频A跳转到指定帧
function handleJumpToFrameA(frameStr: string) {
  const frame = parseInt(frameStr, 10)
  if (isFrameSyncMode.value) {
    const syncTotal = getSyncTotalFrames()
    if (!isNaN(frame) && frame >= 1 && frame <= syncTotal) {
      setSyncedFrameIndex(frame - 1)
    }
    return
  }

  const total = recordA.value?.result?.total_frames || 0

  if (!isNaN(frame) && frame >= 1 && frame <= total) {
    currentFrameIndexA.value = frame - 1
    loadImageA()
  }
}

// ==================== 视频B的控制函数 ====================
// 视频B下一帧
function handleNextFrameB() {
  if (isFrameSyncMode.value) {
    const syncTotal = getSyncTotalFrames()
    if (currentFrameIndexB.value < syncTotal - 1) {
      setSyncedFrameIndex(currentFrameIndexB.value + 1)
    }
    return
  }

  const totalFrames = recordB.value?.result?.total_frames || 0
  if (currentFrameIndexB.value < totalFrames - 1) {
    currentFrameIndexB.value++
    loadImageB()
  }
}

// 视频B上一帧
function handlePrevFrameB() {
  if (isFrameSyncMode.value) {
    if (currentFrameIndexB.value > 0) {
      setSyncedFrameIndex(currentFrameIndexB.value - 1)
    }
    return
  }

  if (currentFrameIndexB.value > 0) {
    currentFrameIndexB.value--
    loadImageB()
  }
}

// 视频B回到第一帧
function handleGoToFirstFrameB() {
  if (isFrameSyncMode.value) {
    setSyncedFrameIndex(0)
    return
  }

  currentFrameIndexB.value = 0
  loadImageB()
}

// 视频B跳转到指定帧
function handleJumpToFrameB(frameStr: string) {
  const frame = parseInt(frameStr, 10)
  if (isFrameSyncMode.value) {
    const syncTotal = getSyncTotalFrames()
    if (!isNaN(frame) && frame >= 1 && frame <= syncTotal) {
      setSyncedFrameIndex(frame - 1)
    }
    return
  }

  const total = recordB.value?.result?.total_frames || 0

  if (!isNaN(frame) && frame >= 1 && frame <= total) {
    currentFrameIndexB.value = frame - 1
    loadImageB()
  }
}

// ==================== 计算属性 ====================
// 计算属性：当前帧号（从1开始显示）
const currentFrameNumberA = computed(() => currentFrameIndexA.value + 1)
const currentFrameNumberB = computed(() => currentFrameIndexB.value + 1)

// 计算属性：总帧数
const totalFramesA = computed(() => recordA.value?.result?.total_frames || 0)
const totalFramesB = computed(() => recordB.value?.result?.total_frames || 0)

// 处理返回对比页面
function handleBackToCompare() {
  store.compareRecords = []
  router.push({ name: isModelCompareMode.value ? 'resourceManage' : 'compare' })
}

watch([recordA, recordB], () => {
  restoreFrameState()
  alignFrameIndexesForSync()
  if (recordA.value?.task_id) {
    loadImageA()
  }
  if (recordB.value?.task_id) {
    loadImageB()
  }
  saveFrameState()
  loadCompareChartCache()
  ensureDefaultCharts()
})
</script>

<template>
  <div class="compare-result-panel">
    <!-- 结果头部 -->
    <div class="result-header">
      <div class="header-content">
        <button class="btn-back" @click="handleBackToCompare">
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
          返回对比
        </button>
        <div class="header-title">
          <h2>对比分析结果</h2>
          <p class="header-subtitle">
            {{ recordA?.task_name || '未知' }} vs {{ recordB?.task_name || '未知' }}
          </p>
          <p v-if="isFrameSyncMode" class="header-mode-tip">模型对比模式：帧同步已开启</p>
        </div>
      </div>
    </div>

    <div class="result-content">
      <!-- 视频对比区域 -->
      <div class="image-compare-section">
        <div class="image-compare-wrapper">
          <!-- 左侧：记录A的标注视频 -->
          <div class="image-panel image-panel-left">
            <h3>标注视频 A - {{ recordA?.task_name || '未知' }}</h3>
            <div class="image-container">
              <div class="image-wrapper">
                <img
                  v-if="displayedImageUrlA"
                  :src="displayedImageUrlA"
                  class="image-player"
                  alt="当前帧 A"
                  :class="{ 'loading': isImageLoadingA }"
                />
                <div v-else class="image-placeholder">
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
                      d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                    ></path>
                  </svg>
                  <p class="placeholder-text">暂无帧数据</p>
                </div>
              </div>
            </div>

            <!-- 视频A的帧控制栏 -->
            <div class="image-controls">
              <button class="btn-control" @click="handleGoToFirstFrameA">
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
              <button class="btn-control" @click="handlePrevFrameA">
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
                  :value="currentFrameNumberA"
                  :min="1"
                  :max="totalFramesA"
                  @input="handleJumpToFrameA(($event.target as HTMLInputElement).value)"
                  @blur="handleJumpToFrameA(($event.target as HTMLInputElement).value)"
                  @keyup.enter="handleJumpToFrameA(($event.target as HTMLInputElement).value)"
                  class="frame-input"
                />
                <span class="frame-separator">/</span>
                <span class="frame-total">{{ totalFramesA }}</span>
                <span class="frame-label">帧</span>
              </div>
              <button class="btn-control" @click="handleNextFrameA">
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

          <!-- 中间分隔线 -->
          <div class="image-divider"></div>

          <!-- 右侧：记录B的标注视频 -->
          <div class="image-panel image-panel-right">
            <h3>标注视频 B - {{ recordB?.task_name || '未知' }}</h3>
            <div class="image-container">
              <div class="image-wrapper">
                <img
                  v-if="displayedImageUrlB"
                  :src="displayedImageUrlB"
                  class="image-player"
                  alt="当前帧 B"
                  :class="{ 'loading': isImageLoadingB }"
                />
                <div v-else class="image-placeholder">
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
                      d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                    ></path>
                  </svg>
                  <p class="placeholder-text">暂无帧数据</p>
                </div>
              </div>
            </div>

            <!-- 视频B的帧控制栏 -->
            <div class="image-controls">
              <button class="btn-control" @click="handleGoToFirstFrameB">
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
              <button class="btn-control" @click="handlePrevFrameB">
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
                  :value="currentFrameNumberB"
                  :min="1"
                  :max="totalFramesB"
                  @input="handleJumpToFrameB(($event.target as HTMLInputElement).value)"
                  @blur="handleJumpToFrameB(($event.target as HTMLInputElement).value)"
                  @keyup.enter="handleJumpToFrameB(($event.target as HTMLInputElement).value)"
                  class="frame-input"
                />
                <span class="frame-separator">/</span>
                <span class="frame-total">{{ totalFramesB }}</span>
                <span class="frame-label">帧</span>
              </div>
              <button class="btn-control" @click="handleNextFrameB">
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
      </div>

      <!-- 细胞详细信息部分（左右两块） -->
      <div class="cell-detail-section">
        <h3>细胞详细信息</h3>
        <div class="cell-detail-wrapper">
          <!-- 左侧：记录A的细胞信息 -->
          <div class="cell-detail-panel cell-detail-panel-left">
            <!-- 无数据状态 -->
            <div v-if="currentFrameCellsA.length === 0" class="no-cells-state">
              <svg class="no-cells-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <p>当前帧无可用数据</p>
              <p class="placeholder-hint">若为初始帧则为正常情况</p>
            </div>
            
            <!-- 表格数据 -->
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
                  <tr v-for="cell in currentFrameCellsA" :key="cell.cell_id">
                    <td class="cell-id">{{ cell.cell_id }}</td>
                    <td>{{ (cell.frames[0]?.position?.x ?? 0).toFixed(1) }}, {{ (cell.frames[0]?.position?.y ?? 0).toFixed(1) }}</td>
                    <td>{{ (cell.frames[0]?.area ?? 0).toFixed(1) }}</td>
                    <td>{{ (cell.frames[0]?.velocity?.speed ?? 0).toFixed(2) }}</td>
                    <td>{{ (cell.frames[0]?.velocity?.vx ?? 0).toFixed(2) }}, {{ (cell.frames[0]?.velocity?.vy ?? 0).toFixed(2) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 中间分隔线 -->
          <div class="cell-detail-divider"></div>

          <!-- 右侧：记录B的细胞信息 -->
          <div class="cell-detail-panel cell-detail-panel-right">
            <!-- 无数据状态 -->
            <div v-if="currentFrameCellsB.length === 0" class="no-cells-state">
              <svg class="no-cells-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <p>当前帧无可用数据</p>
              <p class="placeholder-hint">若为初始帧则为正常情况</p>
            </div>
            
            <!-- 表格数据 -->
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
                  <tr v-for="cell in currentFrameCellsB" :key="cell.cell_id">
                    <td class="cell-id">{{ cell.cell_id }}</td>
                    <td>{{ (cell.frames[0]?.position?.x ?? 0).toFixed(1) }}, {{ (cell.frames[0]?.position?.y ?? 0).toFixed(1) }}</td>
                    <td>{{ (cell.frames[0]?.area ?? 0).toFixed(1) }}</td>
                    <td>{{ (cell.frames[0]?.velocity?.speed ?? 0).toFixed(2) }}</td>
                    <td>{{ (cell.frames[0]?.velocity?.vx ?? 0).toFixed(2) }}, {{ (cell.frames[0]?.velocity?.vy ?? 0).toFixed(2) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- 图表部分（左右两块） -->
      <div class="chart-section">
        <h3>对比图表</h3>
        <div class="chart-wrapper">
          <!-- 左侧：记录A的图表 -->
          <div class="chart-panel chart-panel-left">
            <div class="chart-config-row">
              <select v-model="chartTypeA" class="chart-type-select">
                <option v-for="opt in chartTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
              <button class="btn-control" @click="handleRegenerateA">重新绘图</button>
              <button class="btn-control" @click="goToChartDrawing('A')">调整图例</button>
            </div>
            <div :class="['chart-placeholder', 'chart-placeholder-clickable', { 'chart-placeholder-has-image': !!chartImageA }]" @click="handleRegenerateA">
              <img
                v-if="chartImageA"
                :src="chartImageA"
                :class="[
                  'compare-chart-image',
                  chartImageVariantA === 'wide' ? 'compare-chart-image-wide' : '',
                  chartImageVariantA === 'square' ? 'compare-chart-image-square' : ''
                ]"
                alt="任务A对比图"
              />
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
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  ></path>
                </svg>
                <p>任务 A 图表区域</p>
                <p class="placeholder-hint">点击进入绘图并回填到此位置</p>
              </template>
              <p v-if="chartImageA && chartLabelA" class="placeholder-hint">{{ chartLabelA }}</p>
            </div>
          </div>

          <!-- 中间分隔线 -->
          <div class="chart-divider"></div>

          <!-- 右侧：记录B的图表 -->
          <div class="chart-panel chart-panel-right">
            <div class="chart-config-row">
              <select v-model="chartTypeB" class="chart-type-select">
                <option v-for="opt in chartTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
              <button class="btn-control" @click="handleRegenerateB">重新绘图</button>
              <button class="btn-control" @click="goToChartDrawing('B')">调整图例</button>
            </div>
            <div :class="['chart-placeholder', 'chart-placeholder-clickable', { 'chart-placeholder-has-image': !!chartImageB }]" @click="handleRegenerateB">
              <img
                v-if="chartImageB"
                :src="chartImageB"
                :class="[
                  'compare-chart-image',
                  chartImageVariantB === 'wide' ? 'compare-chart-image-wide' : '',
                  chartImageVariantB === 'square' ? 'compare-chart-image-square' : ''
                ]"
                alt="任务B对比图"
              />
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
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  ></path>
                </svg>
                <p>任务 B 图表区域</p>
                <p class="placeholder-hint">点击进入绘图并回填到此位置</p>
              </template>
              <p v-if="chartImageB && chartLabelB" class="placeholder-hint">{{ chartLabelB }}</p>
            </div>
          </div>
        </div>
      </div>

      <div v-if="chartConfigModalVisible" class="modal" @click.self="closeChartConfigModal">
        <div class="modal-content config-modal-content">
          <div class="modal-header">
            <h3>图表参数设置（{{ chartConfigSlot }}）</h3>
            <span class="close" @click="closeChartConfigModal">&times;</span>
          </div>

          <div class="modal-body">
            <div class="form-item">
              <label>图表类型</label>
              <select v-model="chartConfigType">
                <option v-for="opt in chartTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>

            <div v-if="chartConfigType === 'timeSeries'" class="form-grid">
              <div class="form-item">
                <label>Y轴特征</label>
                <select v-model="chartConfigDraft.yAxisFeature">
                  <option v-for="f in featureOptions" :key="f.value" :value="f.value">{{ f.label }}</option>
                </select>
              </div>
              <div class="form-item">
                <label>TopN</label>
                <input v-model.number="chartConfigDraft.topN" type="number" min="1" max="100" />
              </div>
              <div class="form-item">
                <label>线型</label>
                <select v-model="chartConfigDraft.lineType">
                  <option value="smooth">平滑</option>
                  <option value="line">折线</option>
                </select>
              </div>
            </div>

            <div v-if="chartConfigType === 'histogram'" class="form-grid">
              <div class="form-item">
                <label>X轴特征</label>
                <select v-model="chartConfigDraft.xAxisFeature">
                  <option v-for="f in featureOptions" :key="f.value" :value="f.value">{{ f.label }}</option>
                </select>
              </div>
              <div class="form-item">
                <label>分箱</label>
                <input v-model.number="chartConfigDraft.binCount" type="number" min="5" max="40" />
              </div>
              <div class="form-item">
                <label>统计类型</label>
                <select v-model="chartConfigDraft.statMode">
                  <option value="average">整体平均</option>
                  <option value="frame">单帧</option>
                </select>
              </div>
              <div class="form-item" v-if="chartConfigDraft.statMode === 'frame'">
                <label>帧号</label>
                <input v-model.number="chartConfigDraft.selectedFrame" type="number" min="1" />
              </div>
            </div>

            <div v-if="chartConfigType === 'scatter'" class="form-grid">
              <div class="form-item">
                <label>模式</label>
                <select v-model="chartConfigDraft.frameMode">
                  <option value="single">单帧</option>
                </select>
              </div>
              <div class="form-item">
                <label>帧号</label>
                <input v-model.number="chartConfigDraft.selectedFrame" type="number" min="1" />
              </div>
              <div class="form-item">
                <label>点大小</label>
                <input v-model.number="chartConfigDraft.pointSize" type="number" min="3" max="24" />
              </div>
              <div class="form-item">
                <label>着色</label>
                <select v-model="chartConfigDraft.colorBy">
                  <option value="cell_id">细胞ID</option>
                  <option value="area">面积</option>
                  <option value="speed">速度</option>
                </select>
              </div>
            </div>

            <div v-if="chartConfigType === 'trajectory'" class="form-grid">
              <div class="form-item">
                <label>轨迹类型</label>
                <select v-model="chartConfigDraft.trajectoryType">
                  <option value="normalized">归一化</option>
                </select>
              </div>
              <div class="form-item">
                <label>着色</label>
                <select v-model="chartConfigDraft.colorMap">
                  <option value="time">时间</option>
                  <option value="speed">速度</option>
                  <option value="cell_id">细胞ID</option>
                </select>
              </div>
              <div class="form-item">
                <label>线宽</label>
                <input v-model.number="chartConfigDraft.lineWidth" type="number" min="1" max="8" />
              </div>
              <div class="form-item">
                <label>TopN</label>
                <input v-model.number="chartConfigDraft.topN" type="number" min="1" max="100" />
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="closeChartConfigModal">取消</button>
            <button class="btn-primary" @click="confirmChartConfigAndDraw">生成图表</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.compare-result-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-main);
  overflow: hidden;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .compare-result-panel {
  background: var(--bg-main-light);
}

.result-header {
  padding: 1.5rem 2rem;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .result-header {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  max-width: 1600px;
  margin: 0 auto;
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
  white-space: nowrap;
}

:global(:root:not(.dark)) .btn-back {
  background: var(--bg-card-light);
  color: var(--text-primary-light);
  border-color: var(--border-color-light);
}

.btn-back:hover {
  background: var(--bg-hover);
  border-color: var(--text-muted);
}

:global(:root:not(.dark)) .btn-back:hover {
  background: var(--bg-main-light);
  border-color: var(--text-disabled-light);
}

.btn-back svg {
  width: 16px;
  height: 16px;
}

.header-title {
  flex: 1;
}

.header-title h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.25rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .header-title h2 {
  color: var(--text-primary-light);
}

.header-subtitle {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0;
  transition: color 0.3s;
}

.header-mode-tip {
  margin: 0.35rem 0 0;
  font-size: 0.8rem;
  color: var(--accent-blue);
}

:global(:root:not(.dark)) .header-subtitle {
  color: var(--text-muted-light);
}

.result-content {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.image-compare-section {
  margin-bottom: 2rem;
}

.image-compare-wrapper {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.image-panel h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .image-panel h3 {
  color: var(--text-primary-light);
}

.image-container {
  flex: 1;
  background: var(--bg-main);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.3s;
  min-height: 400px;
}

:global(:root:not(.dark)) .image-container {
  background: var(--bg-main-light);
  border-color: var(--border-color-light);
}

.image-wrapper {
  width: 100%;
  height: 100%;
}

.image-player {
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: opacity 0.15s ease-in-out;
}

.image-player.loading {
  opacity: 0.7;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--alpha-toast);
  transition: background 0.3s;
}

:global(:root:not(.dark)) .image-placeholder {
  background: var(--alpha-toast-light);
}

.image-placeholder .placeholder-icon {
  width: 64px;
  height: 64px;
  color: var(--text-muted);
  margin-bottom: 1rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .image-placeholder .placeholder-icon {
  color: var(--text-disabled-light);
}

.image-placeholder .placeholder-text {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .image-placeholder .placeholder-text {
  color: var(--text-primary-light);
}

.image-divider {
  width: 1px;
  background: var(--border-color);
  align-self: stretch;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .image-divider {
  background: var(--border-color-light);
}

.image-controls {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .image-controls {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

.btn-control {
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

:global(:root:not(.dark)) .btn-control {
  background: var(--bg-card-light);
  color: var(--text-primary-light);
  border-color: var(--border-color-light);
}

.btn-control:hover {
  background: var(--bg-hover);
  border-color: var(--text-muted);
}

:global(:root:not(.dark)) .btn-control:hover {
  background: var(--bg-main-light);
  border-color: var(--text-disabled-light);
}

.btn-control svg {
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

.chart-section {
  margin-bottom: 2rem;
}

.chart-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .chart-section h3 {
  color: var(--text-primary-light);
}

.chart-wrapper {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 1rem;
  align-items: start;
}

.chart-panel {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-self: start;
}

.chart-config-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.chart-type-select {
  flex: 1;
  height: 34px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-input);
  color: var(--text-secondary);
  padding: 0 0.75rem;
}

:global(:root:not(.dark)) .chart-type-select {
  border-color: var(--border-color-light);
  background: var(--bg-card-light);
  color: var(--text-primary-light);
}

.chart-panel h4 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.75rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .chart-panel h4 {
  color: var(--text-primary-light);
}

.chart-divider {
  width: 1px;
  background: var(--border-color);
  align-self: stretch;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .chart-divider {
  background: var(--border-color-light);
}

.chart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 340px;
  background: var(--bg-card);
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  color: var(--text-muted);
  transition: background 0.3s, border-color 0.3s;
}

.chart-placeholder-clickable {
  cursor: pointer;
}

.chart-placeholder-has-image {
  width: fit-content;
  max-width: 100%;
  min-height: 0;
  padding: 0.45rem;
  margin: 0 auto;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.compare-chart-image {
  width: 100%;
  height: auto;
  display: block;
  max-width: 100%;
  object-fit: contain;
}

.compare-chart-image-wide {
  image-rendering: auto;
  max-width: 92%;
  height: auto;
  margin: auto;
  object-fit: contain;
}

.compare-chart-image-square {
  width: auto;
  max-width: 100%;
  aspect-ratio: 1 / 1;
  height: auto;
  object-fit: contain;
}

.config-modal-content {
  width: min(760px, 92vw);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  margin-top: 0.75rem;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.form-item label {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.form-item input,
.form-item select {
  height: 34px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 0 0.6rem;
  background: var(--bg-input);
  color: var(--text-primary);
}

.modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.9rem 1rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-body {
  padding: 1rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.6rem;
  padding: 0.9rem 1rem;
  border-top: 1px solid var(--border-color);
}

.close {
  cursor: pointer;
  color: var(--text-muted);
  font-size: 1.2rem;
}

.btn-secondary,
.btn-primary {
  height: 34px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  padding: 0 0.9rem;
  cursor: pointer;
}

.btn-secondary {
  background: var(--bg-input);
  color: var(--text-secondary);
}

.btn-primary {
  background: var(--accent-blue);
  color: #fff;
  border-color: var(--accent-blue);
}

:global(:root:not(.dark)) .chart-placeholder {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
  color: var(--text-muted-light);
}

.cell-detail-section {
  margin-bottom: 2rem;
}

.cell-detail-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .cell-detail-section h3 {
  color: var(--text-primary-light);
}

.cell-detail-wrapper {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 1rem;
  min-height: 400px;
}

.cell-detail-panel {
  display: flex;
  flex-direction: column;
}

.cell-detail-panel h4 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.75rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .cell-detail-panel h4 {
  color: var(--text-primary-light);
}

.cell-detail-divider {
  width: 1px;
  background: var(--border-color);
  align-self: stretch;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .cell-detail-divider {
  background: var(--border-color-light);
}

.cell-detail-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg-card);
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  color: var(--text-muted);
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .cell-detail-placeholder {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
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

.chart-placeholder > p,
.cell-detail-placeholder > p {
  margin: 0.5rem 0;
  font-size: 1rem;
  color: var(--text-secondary);
  transition: color 0.3s;
}

:global(:root:not(.dark)) .chart-placeholder > p,
:global(:root:not(.dark)) .cell-detail-placeholder > p {
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

/* 滚动条样式 */
.result-content::-webkit-scrollbar {
  width: 10px;
}

.result-content::-webkit-scrollbar-track {
  background: var(--bg-main);
  transition: background 0.3s;
}

:global(:root:not(.dark)) .result-content::-webkit-scrollbar-track {
  background: var(--bg-main-light);
}

.result-content::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 5px;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .result-content::-webkit-scrollbar-thumb {
  background: var(--border-color-light);
}

.result-content::-webkit-scrollbar-thumb:hover {
  background: var(--border-hover);
  transition: background 0.3s;
}

:global(:root:not(.dark)) .result-content::-webkit-scrollbar-thumb:hover {
  background: var(--border-hover-light);
}

/* 无数据状态 */
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
  height: 400px; /* 固定高度 */
}

:global(:root:not(.dark)) .no-cells-state {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

.no-cells-icon {
  width: 64px;
  height: 64px;
  color: var(--text-muted);
}

:global(:root:not(.dark)) .no-cells-icon {
  color: var(--text-disabled-light);
}

.no-cells-state > p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 1rem;
}

:global(:root:not(.dark)) .no-cells-state > p {
  color: var(--text-primary-light);
}

.no-cells-state .placeholder-hint {
  font-size: 0.875rem;
  color: var(--text-disabled) !important;
}

:global(:root:not(.dark)) .no-cells-state .placeholder-hint {
  color: var(--text-disabled-light) !important;
}

/* 细胞表格容器 - 固定高度，内部滚动 */
.cells-table-container {
  height: 400px; /* 固定高度 */
  overflow: auto;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

:global(:root:not(.dark)) .cells-table-container {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

/* 细胞表格 */
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

/* 表格滚动条样式 */
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