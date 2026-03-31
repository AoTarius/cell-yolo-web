import type { CellData } from '@/stores/analysisStore'
import type { CSSProperties } from 'vue'

const academicPalette = ['#0173B2', '#DE8F05', '#029E73', '#D55E00', '#CC78BC', '#CA9161', '#56B4E9', '#949494']

export interface ChartBuilderOptions {
  baseFontSize?: number
  legendFontSize?: number
  titleFontSize?: number
}

function getFeatureLabel(feature: string): string {
  if (feature === 'area') return '面积 (μm²)'
  if (feature === 'speed' || feature === 'migration_speed') return '速度 (μm/帧)'
  return feature
}

export function filterDataFields(cellsInput: CellData[], type: string, cfg: any): CellData[] {
  if (!cellsInput.length) return []

  const chartTypeSafe = type as any

  return cellsInput.map((cell) => {
    const filteredCell: any = {
      cell_id: cell.cell_id,
      first_frame: cell.first_frame,
      last_frame: cell.last_frame,
      frame_count: cell.frame_count,
      avg_width: cell.avg_width,
      avg_height: cell.avg_height,
      avg_conf: cell.avg_conf,
      avg_velocity: cell.avg_velocity,
      avgVisibility: cell.avgVisibility,
      cellClass: cell.cellClass,
      rawMetrics: cell.rawMetrics,
      frames: [],
    }

    filteredCell.frames = cell.frames
      .map((frame, index) => {
        const filteredFrame: any = { frame_number: frame.frame_number }

        switch (chartTypeSafe) {
          case 'timeSeries': {
            const feature = cfg?.yAxisFeature
            if (feature === 'area') {
              filteredFrame.area = frame.area
            } else if (feature === 'speed' || feature === 'migration_speed') {
              filteredFrame.velocity = { ...frame.velocity }
            } else if (feature) {
              const metric = cell.rawMetrics?.[index]
              const metricValue = metric?.shape?.[feature] ?? metric?.motion?.[feature]
              if (metricValue !== undefined) filteredFrame[feature] = metricValue
            }
            break
          }
          case 'histogram': {
            const feature = cfg?.xAxisFeature
            if (feature === 'area') {
              filteredFrame.area = frame.area
            } else if (feature === 'speed' || feature === 'migration_speed') {
              filteredFrame.velocity = { ...frame.velocity }
            } else if (feature) {
              const metric = cell.rawMetrics?.[index]
              const metricValue = metric?.shape?.[feature] ?? metric?.motion?.[feature]
              if (metricValue !== undefined) filteredFrame[feature] = metricValue
            }
            break
          }
          case 'scatter': {
            filteredFrame.position = {
              x: frame.position?.x ?? 0,
              y: frame.position?.y ?? 0,
            }
            if (cfg?.colorBy === 'area') filteredFrame.area = frame.area
            if (cfg?.colorBy === 'speed') filteredFrame.velocity = { ...frame.velocity }
            break
          }
          case 'trajectory': {
            filteredFrame.position = {
              x: frame.position?.x ?? 0,
              y: frame.position?.y ?? 0,
            }
            if (cfg?.colorMap === 'speed') filteredFrame.velocity = { ...frame.velocity }
            break
          }
          default:
            return frame
        }

        return filteredFrame
      })
      .filter((f: any) => f && Object.keys(f).length > 1)

    filteredCell.frame_count = filteredCell.frames.length
    return filteredCell as CellData
  })
}

export function buildOption(chartType: string, filteredCells: CellData[], cfg: any, opts?: ChartBuilderOptions) {
  const baseFontSize = opts?.baseFontSize || 14
  const legendFontSize = opts?.legendFontSize || 12
  const titleFontSize = opts?.titleFontSize || 16

  function getTitleTextStyle() {
    return {
      fontSize: titleFontSize,
      fontWeight: 500,
      fontFamily: 'Georgia, "Times New Roman", serif',
      color: '#1f2937',
    }
  }

  function getCenteredTitle(text: string) {
    return { text, left: 'center' as const, top: '2%' as const, textStyle: getTitleTextStyle() }
  }

  function getAxisLabelStyle() {
    const scaled = Math.round(baseFontSize * 1)
    return { fontSize: scaled, fontFamily: 'Arial, Helvetica, sans-serif', color: '#374151' }
  }

  function getAxisNameStyle() {
    const scaled = Math.round((baseFontSize + 1) * 1)
    return { fontSize: scaled, fontWeight: 600, fontFamily: 'Arial, Helvetica, sans-serif', color: '#111827' }
  }

  function getLegendTextStyle() {
    const scaled = Math.round((legendFontSize + 1) * 1)
    return { fontSize: scaled, fontFamily: 'Arial, Helvetica, sans-serif', color: '#4b5563' }
  }

  function getTooltipTextStyle() {
    return { fontSize: baseFontSize, fontFamily: 'Arial, Helvetica, sans-serif' }
  }

  function getAcademicGrid(right = '8%') {
    return { left: '12%', right, top: '14%', bottom: '14%', containLabel: false }
  }

  function getAcademicAxisLine() {
    return { lineStyle: { color: '#475569', width: 1 } }
  }

  function getAcademicSplitLine() {
    return { show: true, lineStyle: { color: '#d1d5db', width: 1, opacity: 1 } }
  }

  const chartTitle = chartType === 'timeSeries' ? '折线图' : chartType === 'histogram' ? '直方图' : chartType === 'scatter' ? '散点图' : '轨迹图'

  // Implement simplified options similar to DrawingCanvas
  function getDataBounds(points: Array<[number, number]>, defaultSpan = 200) {
    if (!points.length) return { xMin: 0, xMax: defaultSpan, yMin: 0, yMax: defaultSpan }

    // filter out non-finite and extremely large outliers
    const MAX_COORD = 1e6
    const xs = points.map(([x]) => Number(x ?? 0)).filter((v) => Number.isFinite(v) && Math.abs(v) < MAX_COORD)
    const ys = points.map(([, y]) => Number(y ?? 0)).filter((v) => Number.isFinite(v) && Math.abs(v) < MAX_COORD)
    if (!xs.length || !ys.length) return { xMin: 0, xMax: defaultSpan, yMin: 0, yMax: defaultSpan }

    const rawXMin = Math.min(...xs)
    const rawXMax = Math.max(...xs)
    const rawYMin = Math.min(...ys)
    const rawYMax = Math.max(...ys)
    const xSpan = Math.max(1, rawXMax - rawXMin)
    const ySpan = Math.max(1, rawYMax - rawYMin)
    const xPad = Math.max(8, xSpan * 0.08)
    const yPad = Math.max(8, ySpan * 0.08)
    return { xMin: rawXMin - xPad, xMax: rawXMax + xPad, yMin: rawYMin - yPad, yMax: rawYMax + yPad }
  }

  function getNonNegativeBounds(points: Array<[number, number]>, defaultSpan = 240) {
    const raw = getDataBounds(points, defaultSpan)
    const xMin = Math.max(0, raw.xMin)
    const yMin = Math.max(0, raw.yMin)
    const xMax = Math.max(xMin + 1, raw.xMax)
    const yMax = Math.max(yMin + 1, raw.yMax)
    return { xMin, xMax, yMin, yMax }
  }

  function normalizeQuadFrames(requestedFrames: number[], availableFrames: number[], anchorFrame: number) {
    const uniqueRequested = Array.from(new Set(requestedFrames.filter((v) => Number.isFinite(v))))
    const uniqueAvailable = Array.from(new Set(availableFrames.filter((v) => Number.isFinite(v)))).sort((a, b) => a - b)
    const fallback = Number.isFinite(anchorFrame) ? anchorFrame : 1
    const normalized: number[] = []

    uniqueRequested.forEach((frame) => {
      if (normalized.length >= 4) return
      normalized.push(frame)
    })

    if (!normalized.length) {
      if (uniqueAvailable.length > 0) {
        const nearestAvailable = [...uniqueAvailable].sort((a, b) => Math.abs(a - fallback) - Math.abs(b - fallback))[0]
        normalized.push(nearestAvailable ?? fallback)
      } else {
        normalized.push(fallback)
      }
    }

    if (normalized.length < 4) {
      const orderedCandidates = [...uniqueAvailable].sort((a, b) => {
        const da = Math.abs(a - fallback)
        const db = Math.abs(b - fallback)
        if (da !== db) return da - db
        return a - b
      })

      orderedCandidates.forEach((frame) => {
        if (normalized.length >= 4) return
        if (!normalized.includes(frame)) normalized.push(frame)
      })
    }

    while (normalized.length < 4) {
      normalized.push(normalized[normalized.length - 1] ?? fallback)
    }

    return normalized.slice(0, 4)
  }
  switch (chartType) {
    case 'timeSeries': {
      const feature = cfg?.yAxisFeature || 'area'
      const featureLabel = getFeatureLabel(feature)
      function getFrameFeatureValue(f: any, featureName: string) {
        if (featureName === 'area') return Number(f.area ?? 0)
        if (featureName === 'speed' || featureName === 'migration_speed') return Number(f.velocity?.speed ?? 0)
        return Number(f[featureName] ?? f.value ?? 0)
      }

      const series = filteredCells.slice(0, 30).map((cell, idx) => {
        const data = [...cell.frames]
          .sort((a, b) => a.frame_number - b.frame_number)
          .map((f: any) => [f.frame_number, getFrameFeatureValue(f, feature)])
        return {
          name: cell.cell_id,
          type: 'line' as const,
          showSymbol: !!cfg?.showDataPoints,
          smooth: cfg?.lineType === 'smooth',
          lineStyle: { width: 1.2, color: academicPalette[idx % academicPalette.length] },
          data,
        }
      })

      return {
        color: academicPalette,
        animation: false,
        backgroundColor: '#ffffff',
        title: getCenteredTitle(`${chartTitle} - ${featureLabel}`),
        tooltip: { trigger: 'axis', textStyle: getTooltipTextStyle(), backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#d1d5db', borderWidth: 1 },
        legend: { type: 'scroll' as const, left: 'center' as const, bottom: '2%' as const, orient: 'horizontal' as const, textStyle: getLegendTextStyle() },
        grid: { ...getAcademicGrid(), bottom: '20%' },
        xAxis: { type: 'value', name: '帧号', axisLabel: getAxisLabelStyle(), nameTextStyle: getAxisNameStyle(), axisLine: getAcademicAxisLine(), splitLine: getAcademicSplitLine() },
        yAxis: { type: 'value', name: featureLabel, axisLabel: getAxisLabelStyle(), nameTextStyle: getAxisNameStyle(), axisLine: getAcademicAxisLine(), splitLine: getAcademicSplitLine() },
        series,
      }
    }

    case 'histogram': {
      const feature = cfg?.xAxisFeature || 'area'
      const featureLabel = getFeatureLabel(feature)
      const statMode = cfg?.statMode || 'average'
      const frameMode = cfg?.frameMode || 'single'
      const selectedFrame = Number(cfg?.selectedFrame || 1)
      const selectedFrames = Array.isArray(cfg?.selectedFrames)
        ? cfg.selectedFrames.map((v: any) => Number(v)).filter((v: number) => Number.isFinite(v))
        : [1, 25, 50, 75]
      const frameRange = Array.isArray(cfg?.frameRange) ? (cfg.frameRange as [number, number]) : undefined
      const probabilityType = (cfg?.probabilityType || 'probability') as 'probability' | 'count'
      const binCount = Math.max(4, Math.min(80, Number(cfg?.binCount || 14)))

      function getFrameFeatureValue(f: any, featureName: string) {
        if (featureName === 'area') return Number(f.area ?? 0)
        if (featureName === 'speed' || featureName === 'migration_speed') return Number(f.velocity?.speed ?? 0)
        return Number(f[featureName] ?? 0)
      }

      function getCellFrameValuesInRange(cell: CellData, featureName: string, range?: [number, number]) {
        return cell.frames
          .filter((f: any) => {
            if (!range) return true
            return f.frame_number >= range[0] && f.frame_number <= range[1]
          })
          .map((f: any) => getFrameFeatureValue(f, featureName))
          .filter((v: number) => Number.isFinite(v))
      }

      function getCellFeatureByFrame(cell: CellData, featureName: string, frameNumber: number) {
        const frame = cell.frames.find((f: any) => f.frame_number === frameNumber)
        if (!frame) return null
        const value = getFrameFeatureValue(frame, featureName)
        return Number.isFinite(value) ? value : null
      }

      function quantile(sortedValues: number[], q: number) {
        if (!sortedValues.length) return 0
        const pos = (sortedValues.length - 1) * q
        const lower = Math.floor(pos)
        const upper = Math.ceil(pos)
        if (lower === upper) return sortedValues[lower] ?? 0
        const lowerV = sortedValues[lower] ?? 0
        const upperV = sortedValues[upper] ?? 0
        return lowerV + (upperV - lowerV) * (pos - lower)
      }

      let valuesBySeries: Array<{ name: string; values: number[] }> = []

      if (statMode === 'average') {
        const avgValues = filteredCells
          .map((cell) => {
            const vals = getCellFrameValuesInRange(cell, feature, frameRange)
            if (!vals.length) return null
            return vals.reduce((sum, v) => sum + v, 0) / vals.length
          })
          .filter((v): v is number => v !== null && Number.isFinite(v))

        valuesBySeries = [{ name: '平均值分布', values: avgValues }]
      } else {
        const availableFrames = Array.from(
          new Set(filteredCells.flatMap((cell) => cell.frames.map((f: any) => Number(f.frame_number))).filter((v) => Number.isFinite(v)))
        )
        const framesForSeries = frameMode === 'single'
          ? [selectedFrame]
          : frameMode === 'quad'
            ? normalizeQuadFrames(selectedFrames, availableFrames, selectedFrame)
            : selectedFrames

        valuesBySeries = framesForSeries.map((frameNo: number) => ({
          name: `Frame ${frameNo}`,
          values: filteredCells
            .map((cell) => getCellFeatureByFrame(cell, feature, frameNo))
            .filter((v): v is number => v !== null && Number.isFinite(v)),
        }))
      }

      const allValues = valuesBySeries.flatMap((s) => s.values).filter((v) => Number.isFinite(v))
      if (!allValues.length) return { title: { text: '无可用数据' }, series: [] }

      const sorted = [...allValues].sort((a, b) => a - b)
      const rawMin = sorted[0] ?? 0
      const rawMax = sorted[sorted.length - 1] ?? 1
      const q01 = quantile(sorted, 0.01)
      const q99 = quantile(sorted, 0.99)

      const robustRangeSpan = q99 - q01
      const rawRangeSpan = rawMax - rawMin
      const shouldUseRobustRange = sorted.length >= 20 && robustRangeSpan > 0 && rawRangeSpan / robustRangeSpan > 3

      let min = shouldUseRobustRange ? q01 : rawMin
      let max = shouldUseRobustRange ? q99 : rawMax

      if (feature === 'circularity') {
        min = Math.max(0, min)
        max = Math.min(1, max)
      }
      if (feature === 'aspect_ratio') {
        min = Math.max(0, min)
      }

      if (!(max > min)) {
        const center = Number.isFinite(min) ? min : 0
        const delta = Math.max(Math.abs(center) * 0.05, 1e-3)
        min = center - delta
        max = center + delta
      }

      const step = (max - min) / binCount
      const decimals = step >= 1 ? 2 : step >= 0.1 ? 3 : 4

      const labels = Array.from({ length: binCount }, (_, i) => {
        const start = min + i * step
        const end = start + step
        return `${start.toFixed(decimals)}-${end.toFixed(decimals)}`
      })

      function buildHistogramBins(values: number[]) {
        const bins = Array.from({ length: binCount }, () => 0)
        values.forEach((v) => {
          const clipped = Math.max(min, Math.min(max, v))
          const idx = Math.min(binCount - 1, Math.max(0, Math.floor((clipped - min) / step)))
          if (bins[idx] !== undefined) bins[idx] += 1
        })

        if (probabilityType === 'probability') {
          const total = values.length || 1
          return bins.map((n) => Number((n / total).toFixed(4)))
        }

        return bins
      }

      const histogramSeries = valuesBySeries.map((entry) => ({
        name: entry.name,
        type: 'bar' as const,
        barMaxWidth: frameMode === 'single' ? 32 : 20,
        itemStyle: { opacity: 0.85 },
        data: buildHistogramBins(entry.values),
      }))

      if (frameMode === 'quad' && !!cfg?.showQuadGrid && histogramSeries.length > 1) {
        const quadSeries = histogramSeries.slice(0, 4)
        const grid = [
          { left: '8%', top: '14%', width: '36%', height: '30%' },
          { left: '56%', top: '14%', width: '36%', height: '30%' },
          { left: '8%', top: '58%', width: '36%', height: '30%' },
          { left: '56%', top: '58%', width: '36%', height: '30%' },
        ]

        const xAxis = quadSeries.map((_, idx) => ({
          type: 'category' as const,
          gridIndex: idx,
          data: labels,
          name: idx >= 2 ? featureLabel : '',
          axisLabel: getAxisLabelStyle(),
          nameTextStyle: getAxisNameStyle(),
          axisLine: getAcademicAxisLine(),
          splitLine: getAcademicSplitLine(),
        }))

        const yAxis = quadSeries.map((_, idx) => ({
          type: 'value' as const,
          gridIndex: idx,
          name: idx % 2 === 0 ? (probabilityType === 'probability' ? '概率' : '数量') : '',
          axisLabel: getAxisLabelStyle(),
          nameTextStyle: getAxisNameStyle(),
          axisLine: getAcademicAxisLine(),
          splitLine: getAcademicSplitLine(),
        }))

        return {
          color: academicPalette,
          animation: false,
          backgroundColor: '#ffffff',
          title: getCenteredTitle(`${chartTitle} - ${featureLabel} (四宫格)`),
          tooltip: {
            trigger: 'axis',
            textStyle: getTooltipTextStyle(),
            backgroundColor: 'rgba(255,255,255,0.95)',
            borderColor: '#d1d5db',
            borderWidth: 1,
          },
          grid,
          xAxis,
          yAxis,
          series: quadSeries.map((item, idx) => ({
            ...item,
            xAxisIndex: idx,
            yAxisIndex: idx,
            barMaxWidth: 14,
            label: { show: false },
          })),
        }
      }

      return {
        color: academicPalette,
        animation: false,
        backgroundColor: '#ffffff',
        title: getCenteredTitle(`${chartTitle} - ${featureLabel}`),
        legend: histogramSeries.length > 1
          ? { type: 'scroll' as const, left: 'center' as const, bottom: '2%' as const, orient: 'horizontal' as const, textStyle: getLegendTextStyle() }
          : undefined,
        tooltip: { trigger: 'axis', textStyle: getTooltipTextStyle(), backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#d1d5db', borderWidth: 1 },
        grid: histogramSeries.length > 1 ? { ...getAcademicGrid(), bottom: '22%' } : getAcademicGrid(),
        xAxis: {
          type: 'category',
          data: labels,
          name: featureLabel,
          axisLabel: { ...getAxisLabelStyle(), rotate: 35 },
          nameTextStyle: getAxisNameStyle(),
          axisLine: getAcademicAxisLine(),
          splitLine: getAcademicSplitLine(),
          axisTick: { alignWithLabel: true },
        },
        yAxis: {
          type: 'value',
          name: probabilityType === 'probability' ? '概率' : '数量',
          axisLabel: getAxisLabelStyle(),
          nameTextStyle: getAxisNameStyle(),
          axisLine: getAcademicAxisLine(),
          splitLine: getAcademicSplitLine(),
        },
        series: histogramSeries,
      }
    }

    case 'scatter': {
      const allPoints = filteredCells.flatMap((cell) =>
        cell.frames.map((f: any) => ({
          cellId: cell.cell_id,
          frame: f.frame_number,
          x: Number(f.position?.x ?? 0),
          y: Number(f.position?.y ?? 0),
          value:
            cfg?.colorBy === 'area'
              ? Number(f.area ?? 0)
              : cfg?.colorBy === 'speed'
                ? Number(f.velocity?.speed ?? 0)
                : 0,
        }))
      )

      const frameMode = (cfg?.frameMode || 'single') === 'quad' ? 'quad' : 'single'
      const selectedFrame = Number(cfg?.selectedFrame || 1)
      const selectedFrames = Array.isArray(cfg?.selectedFrames)
        ? cfg.selectedFrames.map((v: any) => Number(v)).filter((v: number) => Number.isFinite(v))
        : [1, 25, 50, 75]
      const availableFrames = Array.from(new Set(allPoints.map((p) => Number(p.frame)).filter((v) => Number.isFinite(v))))
      const allScatterXY: Array<[number, number]> = allPoints.map((p) => [p.x, p.y])
      const fixedScatterBounds = getNonNegativeBounds(allScatterXY, 240)
      const useColorMap = cfg?.colorBy === 'area' || cfg?.colorBy === 'speed'

      const getVisualMapRange = () => {
        const values = allPoints.map((p) => Number(p.value)).filter((v) => Number.isFinite(v))
        if (!values.length) return { min: 0, max: 1 }
        const min = Math.min(...values)
        const max = Math.max(...values)
        return { min, max: max > min ? max : min + 1 }
      }

      if (frameMode === 'quad') {
        const quadFrames = normalizeQuadFrames(selectedFrames, availableFrames, selectedFrame)
        const grid = [
          { left: '8%', top: '14%', width: '36%', height: '32%', containLabel: false },
          { left: '56%', top: '14%', width: '36%', height: '32%', containLabel: false },
          { left: '8%', top: '56%', width: '36%', height: '32%', containLabel: false },
          { left: '56%', top: '56%', width: '36%', height: '32%', containLabel: false },
        ]

        const xAxis = quadFrames.map((_: number, idx: number) => ({
          type: 'value' as const,
          gridIndex: idx,
          min: fixedScatterBounds.xMin,
          max: fixedScatterBounds.xMax,
          name: '',
          axisLabel: getAxisLabelStyle(),
          nameTextStyle: getAxisNameStyle(),
          axisLine: getAcademicAxisLine(),
          splitLine: { show: true, lineStyle: { color: '#9aa5b1', width: 1.2, opacity: 1 } },
          minorTick: { show: true },
          minorSplitLine: { show: true, lineStyle: { color: '#d1d5db', width: 1, opacity: 0.95 } },
          scale: true,
        }))

        const yAxis = quadFrames.map((_: number, idx: number) => ({
          type: 'value' as const,
          gridIndex: idx,
          min: fixedScatterBounds.yMin,
          max: fixedScatterBounds.yMax,
          name: '',
          axisLabel: getAxisLabelStyle(),
          nameTextStyle: getAxisNameStyle(),
          axisLine: getAcademicAxisLine(),
          splitLine: { show: true, lineStyle: { color: '#9aa5b1', width: 1.2, opacity: 1 } },
          minorTick: { show: true },
          minorSplitLine: { show: true, lineStyle: { color: '#d1d5db', width: 1, opacity: 0.95 } },
          scale: true,
        }))

        const quadSeries = quadFrames.map((frameNo: number, idx: number) => {
          const framePoints = allPoints.filter((p) => p.frame === frameNo)
          return {
            name: `Frame ${frameNo}`,
            type: 'scatter' as const,
            symbolSize: Number(cfg?.pointSize || 8),
            itemStyle: { color: academicPalette[idx % academicPalette.length], opacity: 0.8 },
            xAxisIndex: idx,
            yAxisIndex: idx,
            data: framePoints.map((p) => ({
              cellId: p.cellId,
              frame: p.frame,
              value: [p.x, p.y, p.value],
            })),
          }
        })

        return {
          color: academicPalette,
          animation: false,
          backgroundColor: '#ffffff',
          title: getCenteredTitle(`${chartTitle} - 四帧对比`),
          tooltip: {
            textStyle: getTooltipTextStyle(),
            backgroundColor: 'rgba(255,255,255,0.95)',
            borderColor: '#d1d5db',
            borderWidth: 1,
            formatter: (params: any) => {
              const d = params.data
              return `Cell: ${d.cellId}<br/>Frame: ${d.frame}<br/>X: ${Number(d.value[0] ?? 0).toFixed(2)} μm<br/>Y: ${Number(d.value[1] ?? 0).toFixed(2)} μm`
            },
          },
          graphic: quadFrames.map((f: number, idx: number) => ({
            type: 'text',
            left: idx % 2 === 0 ? '8%' : '56%',
            top: idx < 2 ? '10%' : '52%',
            style: {
              text: `Frame ${f}`,
              fill: '#334155',
              fontSize: legendFontSize,
              fontWeight: 600,
            },
          })),
          grid,
          xAxis,
          yAxis,
          visualMap: useColorMap
            ? {
                type: 'continuous',
                dimension: 2,
                seriesIndex: quadSeries.map((_: any, idx: number) => idx),
                min: getVisualMapRange().min,
                max: getVisualMapRange().max,
                calculable: true,
                text: ['高', '低'],
                orient: 'vertical',
                right: 8,
                top: 'middle',
                textStyle: getAxisLabelStyle(),
                inRange: { color: ['#f7fbff', '#2171b5'] },
              }
            : undefined,
          series: quadSeries,
        }
      }

      const points = allPoints.filter((p) => p.frame === selectedFrame)
      const showTrajectory = !!cfg?.showTrajectory
      const trajectoryLength = Math.max(2, Number(cfg?.trajectoryLength || 10))

      const trajectorySeries = showTrajectory
        ? filteredCells
            .slice(0, 80)
            .map((cell) => {
              const trail = [...cell.frames]
                .sort((a, b) => a.frame_number - b.frame_number)
                .filter((f: any) => f.frame_number <= selectedFrame)
                .slice(-trajectoryLength)
                .map((f: any) => [Number(f.position?.x ?? 0), Number(f.position?.y ?? 0)])

              if (trail.length < 2) return null
              return {
                name: `Trail-${cell.cell_id}`,
                type: 'line' as const,
                showSymbol: false,
                silent: true,
                lineStyle: {
                  width: 1,
                  opacity: 0.45,
                  color: '#64748b',
                },
                data: trail,
              }
            })
            .filter((s): s is NonNullable<typeof s> => s !== null)
        : []

      const series = [
        ...trajectorySeries,
        {
          type: 'scatter' as const,
          name: `Frame ${selectedFrame}`,
          symbolSize: Number(cfg?.pointSize || 8),
          itemStyle: {
            color: useColorMap ? undefined : academicPalette[0],
            opacity: 0.8,
          },
          data: points.map((p) => ({
            cellId: p.cellId,
            frame: p.frame,
            value: [p.x, p.y, p.value],
          })),
        },
      ]

      const scatterSeriesIndex = series
        .map((s, idx) => ({ s, idx }))
        .filter(({ s }) => s?.type === 'scatter')
        .map(({ idx }) => idx)

      return {
        color: academicPalette,
        animation: false,
        backgroundColor: '#ffffff',
        title: getCenteredTitle(`${chartTitle} - 第 ${selectedFrame} 帧`),
        tooltip: {
          textStyle: getTooltipTextStyle(),
          backgroundColor: 'rgba(255,255,255,0.95)',
          borderColor: '#d1d5db',
          borderWidth: 1,
          formatter: (params: any) => {
            const d = params.data
            const colorInfo = useColorMap ? `<br/>${cfg?.colorBy}: ${Number(d.value?.[2] ?? 0).toFixed(3)}` : ''
            return `Cell: ${d.cellId}<br/>Frame: ${d.frame}<br/>X: ${Number(d.value?.[0] ?? 0).toFixed(2)} μm<br/>Y: ${Number(d.value?.[1] ?? 0).toFixed(2)} μm${colorInfo}`
          },
        },
        grid: getAcademicGrid(useColorMap ? '18%' : '8%'),
        xAxis: {
          type: 'value',
          name: 'X 位置 (μm)',
          min: fixedScatterBounds.xMin,
          max: fixedScatterBounds.xMax,
          axisLabel: getAxisLabelStyle(),
          nameTextStyle: getAxisNameStyle(),
          axisLine: getAcademicAxisLine(),
          splitLine: { show: true, lineStyle: { color: '#9aa5b1', width: 1.2, opacity: 1 } },
          minorTick: { show: true },
          minorSplitLine: { show: true, lineStyle: { color: '#d1d5db', width: 1, opacity: 0.95 } },
          scale: true,
        },
        yAxis: {
          type: 'value',
          name: 'Y 位置 (μm)',
          min: fixedScatterBounds.yMin,
          max: fixedScatterBounds.yMax,
          axisLabel: getAxisLabelStyle(),
          nameTextStyle: getAxisNameStyle(),
          axisLine: getAcademicAxisLine(),
          splitLine: { show: true, lineStyle: { color: '#9aa5b1', width: 1.2, opacity: 1 } },
          minorTick: { show: true },
          minorSplitLine: { show: true, lineStyle: { color: '#d1d5db', width: 1, opacity: 0.95 } },
          scale: true,
        },
        visualMap: useColorMap
          ? {
              type: 'continuous',
              dimension: 2,
              seriesIndex: scatterSeriesIndex,
              min: getVisualMapRange().min,
              max: getVisualMapRange().max,
              calculable: true,
              text: ['高', '低'],
              orient: 'vertical',
              right: 16,
              top: 'middle',
              textStyle: getAxisLabelStyle(),
              inRange: { color: ['#f7fbff', '#2171b5'] },
            }
          : undefined,
        series,
      }
    }

    case 'trajectory': {
      const trajectoryType = cfg?.trajectoryType || 'normal'
      if (trajectoryType === '3d') {
        return { title: getCenteredTitle('3D 轨迹图由后端 Python 渲染'), series: [] }
      }

      const colorMap = cfg?.colorMap || 'time'
      const lineWidth = Number(cfg?.lineWidth || 2)
      const showStartPoint = !!cfg?.showStartPoint
      const showEndPoint = !!cfg?.showEndPoint
      const fadeEffect = !!cfg?.fadeEffect

      const series = filteredCells.slice(0, 50).map((cell, idx) => {
        const sortedFrames = [...cell.frames].sort((a, b) => a.frame_number - b.frame_number)
        const first = sortedFrames[0]
        const baseX = trajectoryType === 'normalized' ? Number(first?.position?.x ?? 0) : 0
        const baseY = trajectoryType === 'normalized' ? Number(first?.position?.y ?? 0) : 0

        const data = sortedFrames.map((f: any) => {
          const frameNo = Number(f.frame_number ?? 0)
          const xRaw = Number(f.position?.x ?? 0) - baseX
          const yRaw = trajectoryType === 'normalized'
            ? baseY - Number(f.position?.y ?? 0)
            : Number(f.position?.y ?? 0)
          const speed = Number(f.velocity?.speed ?? 0)
          const colorValue = colorMap === 'speed' ? speed : frameNo
          return [xRaw, yRaw, colorValue, frameNo, speed]
        })

        const markData: Array<{ name: string; coord: number[] }> = []
        if (showStartPoint && data.length > 0) {
          const start = data[0]
          if (start) markData.push({ name: 'Start', coord: [start[0] ?? 0, start[1] ?? 0] })
        }
        if (showEndPoint && data.length > 1) {
          const last = data[data.length - 1]!
          markData.push({ name: 'End', coord: [last[0]!, last[1]!] })
        }

        return {
          name: cell.cell_id,
          type: 'line' as const,
          showSymbol: false,
          lineStyle: { width: lineWidth, opacity: fadeEffect ? 0.7 : 1, color: academicPalette[idx % academicPalette.length] },
          encode: { x: 0, y: 1 },
          data,
          markPoint: markData.length ? { symbolSize: 26, data: markData } : undefined,
        }
      })

      const isNormalized = trajectoryType === 'normalized'
      const allXY = series.flatMap((s: any) => (s.data as number[][]).map((d) => [Number(d[0] ?? 0), Number(d[1] ?? 0)]))
      const maxAbs = allXY.length ? Math.max(...allXY.map(([x, y]) => Math.max(Math.abs(Number(x ?? 0)), Math.abs(Number(y ?? 0))))) : 100
      const concentricRadii = [200, 400]
      const boundRaw = Math.max(maxAbs + 30, ...concentricRadii.map((r) => r + 20))
      const bound = Math.ceil(boundRaw / 50) * 50
      const trajectoryBounds = isNormalized
        ? { min: -bound, max: bound }
        : getNonNegativeBounds(allXY as Array<[number, number]>, 280)

      const circleSeries = isNormalized ? concentricRadii.filter((r) => r < bound).map((r) => {
        const circleData = Array.from({ length: 181 }, (_, i) => {
          const t = (Math.PI * 2 * i) / 180
          return [Number((r * Math.cos(t)).toFixed(4)), Number((r * Math.sin(t)).toFixed(4))]
        })
        return { name: `__circle_${r}`, type: 'line' as const, silent: true, showSymbol: false, z: 1, lineStyle: { type: 'dashed' as const, width: 1.3, color: '#5f6773', opacity: 0.95 }, data: circleData, tooltip: { show: false } }
      }) : []

      const crossSeries = isNormalized ? [ { name: '__axis_x', type: 'line' as const, silent: true, showSymbol: false, z: 1, lineStyle: { type: 'dashed' as const, width: 1, color: '#b0b3b9', opacity: 0.7 }, data: [[-bound, 0], [bound, 0]], tooltip: { show: false } }, { name: '__axis_y', type: 'line' as const, silent: true, showSymbol: false, z: 1, lineStyle: { type: 'dashed' as const, width: 1, color: '#b0b3b9', opacity: 0.7 }, data: [[0, -bound], [0, bound]], tooltip: { show: false } } ] : []

      const radiusLabelSeries = isNormalized ? [ { name: '__radius_labels', type: 'scatter' as const, silent: true, symbolSize: 2, itemStyle: { color: 'transparent' }, label: { show: true, formatter: (p: any) => `${p.value?.[2] ?? ''} μm`, color: '#2c2f36', fontSize: baseFontSize, position: 'right' as const }, data: concentricRadii.filter((r) => r < bound).map((r) => [r, 0, r]), tooltip: { show: false }, z: 2 } ] : []

      const styledTrajectorySeries = series.map((s: any) => ({ ...s, z: 3, lineStyle: { ...s.lineStyle, opacity: isNormalized ? 0.82 : s.lineStyle?.opacity } }))

      return {
        animation: false,
        backgroundColor: '#ffffff',
        color: academicPalette,
        title: getCenteredTitle(isNormalized ? 'Normalized Cell Trajectories' : chartTitle),
        tooltip: { trigger: 'item', textStyle: getTooltipTextStyle(), backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#d1d5db', borderWidth: 1, formatter: (params: any) => { if (String(params?.seriesName || '').startsWith('__')) return ''; const d = params.data || []; return `${params.seriesName}<br/>X: ${Number(d[0] ?? 0).toFixed(2)}<br/>Y: ${Number(d[1] ?? 0).toFixed(2)}<br/>Frame: ${Number(d[3] ?? 0)}<br/>Speed: ${Number(d[4] ?? 0).toFixed(3)}` } },
        legend: undefined,
        grid: isNormalized
          ? { left: '16%', right: '16%', top: '16%', bottom: '16%', containLabel: false }
          : { ...getAcademicGrid(), left: '16%' },
        xAxis: { type: 'value', name: isNormalized ? 'Normalized X (μm)' : 'X 位置 (μm)', nameLocation: 'middle', nameGap: 40, nameTextStyle: getAxisNameStyle(), min: isNormalized ? (trajectoryBounds as { min: number; max: number }).min : (trajectoryBounds as any).xMin, max: isNormalized ? (trajectoryBounds as { min: number; max: number }).max : (trajectoryBounds as any).xMax, axisLine: getAcademicAxisLine(), splitLine: isNormalized ? { show: true, lineStyle: { color: '#9ca3af', width: 1.1, opacity: 0.95 } } : getAcademicSplitLine(), minorTick: isNormalized ? { show: true } : undefined, minorSplitLine: isNormalized ? { show: true, lineStyle: { color: '#d1d5db', width: 1, opacity: 0.8 } } : undefined, axisLabel: isNormalized ? { ...getAxisLabelStyle(), margin: 10 } : getAxisLabelStyle(), scale: true },
        yAxis: { type: 'value', name: isNormalized ? 'Normalized Y (μm)' : 'Y 位置 (μm)', nameLocation: 'middle', nameGap: isNormalized ? 56 : 68, nameTextStyle: getAxisNameStyle(), min: isNormalized ? (trajectoryBounds as { min: number; max: number }).min : (trajectoryBounds as any).yMin, max: isNormalized ? (trajectoryBounds as { min: number; max: number }).max : (trajectoryBounds as any).yMax, axisLine: getAcademicAxisLine(), splitLine: isNormalized ? { show: true, lineStyle: { color: '#9ca3af', width: 1.1, opacity: 0.95 } } : getAcademicSplitLine(), minorTick: isNormalized ? { show: true } : undefined, minorSplitLine: isNormalized ? { show: true, lineStyle: { color: '#d1d5db', width: 1, opacity: 0.8 } } : undefined, axisLabel: isNormalized ? { ...getAxisLabelStyle(), margin: 10 } : getAxisLabelStyle(), scale: true },
        visualMap: undefined,
        series: [...(circleSeries as any), ...(crossSeries as any), ...(radiusLabelSeries as any), ...styledTrajectorySeries],
      }
    }

    default:
      return { title: { text: '不支持的图表类型' }, series: [] }
  }
}
