<script setup lang="ts">
import '@/assets/styles/colors.css';
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAnalysisStore } from '@/stores/analysisStore';
import type { CellData } from '@/stores/analysisStore';
import * as echarts from 'echarts';
import JSZip from 'jszip';

declare global {
    interface Window {
        __drawingCanvasDebugApi?: DrawingCanvasDebugApi;
    }
}

const route = useRoute();
const router = useRouter();
const analysisStore = useAnalysisStore();

const chartType = computed(() => route.query.type as string);
const taskId = computed(() => route.query.taskId as string);
const compareSlot = computed(() => (route.query.compareSlot as 'A' | 'B' | undefined));
const isCompareReturn = computed(() => route.query.returnTo === 'compareResult' && !!compareSlot.value);
const config = computed(() => {
    try {
        return JSON.parse(route.query.config as string);
    } catch {
        return null;
    }
});

const loading = ref(false);
const error = ref<string | null>(null);
const cells = ref<CellData[]>([]);
const filteredCells = ref<CellData[]>([]);
const chartInstance = ref<echarts.ECharts | null>(null);
const chartContainer = ref<HTMLDivElement | null>(null);
const trajectory3dImageUrl = ref<string | null>(null);
const trajectory3dLoading = ref(false);
const scatterBatchMode = ref(false);
const scatterBatchFrames = ref<number[]>([]);
const scatterBatchIndex = ref(0);
const scatterBatchExporting = ref(false);
const baseFontSize = ref(Number(sessionStorage.getItem('drawingBaseFontSize') || 14));
const legendFontSize = ref(Number(sessionStorage.getItem('drawingLegendFontSize') || 12));
const titleFontSize = ref(Number(sessionStorage.getItem('drawingTitleFontSize') || 16));

const academicPalette = ['#0173B2', '#DE8F05', '#029E73', '#D55E00', '#CC78BC', '#CA9161', '#56B4E9', '#949494'];

type DrawingChartType = 'timeSeries' | 'histogram' | 'scatter' | 'trajectory';

interface ValidationSnapshot {
    taskId: string;
    chartType: string;
    config: any;
    stats: {
        rawCells: number;
        filteredCells: number;
        ratio: number;
    };
    filteredData: CellData[];
}

interface DrawingCanvasDebugApi {
    getTwoStageFilteredData: () => ValidationSnapshot;
    exportChartImage: (options?: ExportChartImageOptions) => string | null;
    downloadChartImage: (options?: ExportChartImageOptions) => boolean;
}

interface ExportChartImageOptions {
    type?: 'png' | 'jpeg';
    pixelRatio?: number;
    backgroundColor?: string;
    filename?: string;
}

function isPython3dMode() {
    return chartType.value === 'trajectory' && config.value?.trajectoryType === '3d';
}

async function loadTrajectory3dImage() {
    if (!taskId.value) return;

    trajectory3dLoading.value = true;
    try {
        const trackIds = filteredCells.value
            .map((c) => Number(c.cell_id))
            .filter((v) => Number.isFinite(v));
        const query = trackIds.length ? `?track_ids=${trackIds.join(',')}` : '';
        const resp = await fetch(`/api/trajectory-3d/${taskId.value}/${query}`);
        if (!resp.ok) {
            throw new Error(`3D轨迹图生成失败: HTTP ${resp.status}`);
        }

        const blob = await resp.blob();
        const oldUrl = trajectory3dImageUrl.value;
        trajectory3dImageUrl.value = URL.createObjectURL(blob);
        if (oldUrl) URL.revokeObjectURL(oldUrl);
    } finally {
        trajectory3dLoading.value = false;
    }
}

const chartTitle = computed(() => {
    const map: Record<string, string> = {
        timeSeries: '折线图',
        histogram: '直方图',
        scatter: '散点图',
        trajectory: '轨迹图',
    };
    return map[chartType.value] || '图表绘制';
});

const isSquareChart = computed(
    () => chartType.value === 'scatter' || (chartType.value === 'trajectory' && config.value?.trajectoryType !== '3d')
);
const isTallChart = computed(() => chartType.value === 'timeSeries' || chartType.value === 'histogram');

function getChartFontScale() {
    return isTallChart.value ? 1.12 : 1;
}

function getTitleTextStyle() {
    return {
        fontSize: titleFontSize.value,
        fontWeight: 500,
        fontFamily: 'Georgia, "Times New Roman", serif',
        color: '#1f2937',
    };
}

function getCenteredTitle(text: string) {
    return {
        text,
        left: 'center' as const,
        top: '2%' as const,
        textStyle: getTitleTextStyle(),
    };
}

function getAxisLabelStyle() {
    const scaled = Math.round(baseFontSize.value * getChartFontScale());
    return {
        fontSize: scaled,
        fontFamily: 'Arial, Helvetica, sans-serif',
        color: '#374151',
    };
}

function getDenseAxisLabelStyle() {
    return {
        ...getAxisLabelStyle(),
        interval: 0,
    };
}

function getAxisNameStyle() {
    const scaled = Math.round((baseFontSize.value + 1) * getChartFontScale());
    return {
        fontSize: scaled,
        fontWeight: 600,
        fontFamily: 'Arial, Helvetica, sans-serif',
        color: '#111827',
    };
}

function getLegendTextStyle() {
    const scaled = Math.round((legendFontSize.value + 1) * getChartFontScale());
    return {
        fontSize: scaled,
        fontFamily: 'Arial, Helvetica, sans-serif',
        color: '#4b5563',
    };
}

function getTooltipTextStyle() {
    return {
        fontSize: baseFontSize.value,
        fontFamily: 'Arial, Helvetica, sans-serif',
    };
}

function getAcademicGrid(right = '8%') {
    return {
        left: '12%',
        right,
        top: '14%',
        bottom: '14%',
        containLabel: false,
    };
}

function getBottomCenterLegend() {
    return {
        type: 'scroll' as const,
        left: 'center' as const,
        bottom: '2%' as const,
        orient: 'horizontal' as const,
        textStyle: getLegendTextStyle(),
    };
}

function getAcademicAxisLine() {
    return { lineStyle: { color: '#475569', width: 1 } };
}

function getAcademicSplitLine() {
    return { show: true, lineStyle: { color: '#d1d5db', width: 1, opacity: 1 } };
}

function getFeatureLabel(feature: string): string {
    if (feature === 'area') return '面积 (μm²)';
    if (feature === 'speed' || feature === 'migration_speed') return '速度 (μm/帧)';
    return feature;
}

function isScatterSingleMode() {
    return chartType.value === 'scatter' && (config.value?.frameMode || 'single') !== 'quad';
}

function getScatterFrameNumbers(): number[] {
    const frames = new Set<number>();
    filteredCells.value.forEach((cell) => {
        cell.frames.forEach((f: any) => {
            const n = Number(f.frame_number);
            if (Number.isFinite(n)) frames.add(n);
        });
    });
    return Array.from(frames).sort((a, b) => a - b);
}

function getCurrentScatterFrame(): number {
    if (scatterBatchMode.value && scatterBatchFrames.value.length > 0) {
        return scatterBatchFrames.value[scatterBatchIndex.value] ?? scatterBatchFrames.value[0] ?? 1;
    }
    return Number(config.value?.selectedFrame || 1);
}

function enableScatterBatchMode() {
    if (!isScatterSingleMode()) return;
    const frames = getScatterFrameNumbers();
    if (!frames.length) return;
    scatterBatchFrames.value = frames;

    const current = getCurrentScatterFrame();
    const idx = frames.findIndex((f) => f === current);
    scatterBatchIndex.value = idx >= 0 ? idx : 0;
    scatterBatchMode.value = true;
    renderChart();
}

function prevScatterFrame() {
    if (!scatterBatchMode.value || scatterBatchFrames.value.length === 0) return;
    if (scatterBatchIndex.value <= 0) return;
    scatterBatchIndex.value -= 1;
    renderChart();
}

function nextScatterFrame() {
    if (!scatterBatchMode.value || scatterBatchFrames.value.length === 0) return;
    if (scatterBatchIndex.value >= scatterBatchFrames.value.length - 1) return;
    scatterBatchIndex.value += 1;
    renderChart();
}

async function exportAllScatterFramesZip() {
    if (!isScatterSingleMode() || !chartInstance.value || scatterBatchExporting.value) return;
    const frames = getScatterFrameNumbers();
    if (!frames.length) return;

    scatterBatchExporting.value = true;
    const prevMode = scatterBatchMode.value;
    const prevFrames = [...scatterBatchFrames.value];
    const prevIndex = scatterBatchIndex.value;

    try {
        scatterBatchMode.value = true;
        scatterBatchFrames.value = frames;
        const zip = new JSZip();
        const folder = zip.folder(`scatter-${taskId.value || 'task'}`);

        for (let i = 0; i < frames.length; i += 1) {
            scatterBatchIndex.value = i;
            chartInstance.value.setOption(buildOption(), true);
            await nextTick();
            const dataUrl = chartInstance.value.getDataURL({
                type: 'png',
                pixelRatio: 2,
                backgroundColor: '#ffffff',
            });
            const base64 = dataUrl.split(',')[1];
            if (folder && base64) {
                const frameNo = frames[i] ?? 0;
                folder.file(`frame_${String(frameNo).padStart(4, '0')}.png`, base64, { base64: true });
            }
        }

        const blob = await zip.generateAsync({ type: 'blob' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `scatter-batch-${taskId.value || 'task'}.zip`;
        link.click();
        URL.revokeObjectURL(url);
    } finally {
        scatterBatchMode.value = prevMode;
        scatterBatchFrames.value = prevFrames;
        scatterBatchIndex.value = prevIndex;
        scatterBatchExporting.value = false;
        renderChart();
    }
}

function getSymmetricBounds(points: Array<[number, number]>, defaultHalf = 200): { min: number; max: number } {
    if (!points.length) return { min: -defaultHalf, max: defaultHalf };

    const maxAbs = Math.max(...points.map(([x, y]) => Math.max(Math.abs(Number(x ?? 0)), Math.abs(Number(y ?? 0)))));
    const bound = Math.max(defaultHalf, Math.ceil((maxAbs * 1.08) / 20) * 20);
    return { min: -bound, max: bound };
}

function getDataBounds(points: Array<[number, number]>, defaultSpan = 200): {
    xMin: number;
    xMax: number;
    yMin: number;
    yMax: number;
} {
    if (!points.length) {
        return { xMin: 0, xMax: defaultSpan, yMin: 0, yMax: defaultSpan };
    }

    const xs = points.map(([x]) => Number(x ?? 0)).filter((v) => Number.isFinite(v));
    const ys = points.map(([, y]) => Number(y ?? 0)).filter((v) => Number.isFinite(v));
    if (!xs.length || !ys.length) {
        return { xMin: 0, xMax: defaultSpan, yMin: 0, yMax: defaultSpan };
    }

    const rawXMin = Math.min(...xs);
    const rawXMax = Math.max(...xs);
    const rawYMin = Math.min(...ys);
    const rawYMax = Math.max(...ys);

    const xSpan = Math.max(1, rawXMax - rawXMin);
    const ySpan = Math.max(1, rawYMax - rawYMin);
    const xPad = Math.max(8, xSpan * 0.08);
    const yPad = Math.max(8, ySpan * 0.08);

    return {
        xMin: rawXMin - xPad,
        xMax: rawXMax + xPad,
        yMin: rawYMin - yPad,
        yMax: rawYMax + yPad,
    };
}

function filterDataFields(cellsInput: CellData[], type: string, cfg: any): CellData[] {
    if (!cellsInput.length) return [];

    const chartTypeSafe = type as DrawingChartType;

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
        };

        filteredCell.frames = cell.frames
            .map((frame, index) => {
                const filteredFrame: any = { frame_number: frame.frame_number };

                switch (chartTypeSafe) {
                    case 'timeSeries': {
                        const feature = cfg?.yAxisFeature;
                        if (feature === 'area') {
                            filteredFrame.area = frame.area;
                        } else if (feature === 'speed' || feature === 'migration_speed') {
                            filteredFrame.velocity = { ...frame.velocity };
                        } else if (feature) {
                            const metric = cell.rawMetrics?.[index];
                            const metricValue = metric?.shape?.[feature] ?? metric?.motion?.[feature];
                            if (metricValue !== undefined) filteredFrame[feature] = metricValue;
                        }
                        break;
                    }
                    case 'histogram': {
                        const feature = cfg?.xAxisFeature;
                        if (feature === 'area') {
                            filteredFrame.area = frame.area;
                        } else if (feature === 'speed' || feature === 'migration_speed') {
                            filteredFrame.velocity = { ...frame.velocity };
                        } else if (feature) {
                            const metric = cell.rawMetrics?.[index];
                            const metricValue = metric?.shape?.[feature] ?? metric?.motion?.[feature];
                            if (metricValue !== undefined) filteredFrame[feature] = metricValue;
                        }
                        break;
                    }
                    case 'scatter': {
                        filteredFrame.position = {
                            x: frame.position?.x ?? 0,
                            y: frame.position?.y ?? 0,
                        };
                        if (cfg?.colorBy === 'area') filteredFrame.area = frame.area;
                        if (cfg?.colorBy === 'speed') filteredFrame.velocity = { ...frame.velocity };
                        break;
                    }
                    case 'trajectory': {
                        filteredFrame.position = {
                            x: frame.position?.x ?? 0,
                            y: frame.position?.y ?? 0,
                        };
                        if (cfg?.colorMap === 'speed') filteredFrame.velocity = { ...frame.velocity };
                        break;
                    }
                    default:
                        return frame;
                }

                return filteredFrame;
            })
            .filter((f: any) => f && Object.keys(f).length > 1);

        filteredCell.frame_count = filteredCell.frames.length;
        return filteredCell as CellData;
    });
}

function buildValidationSnapshot(): ValidationSnapshot {
    const rawCount = cells.value.length;
    const filteredCount = filteredCells.value.length;
    return {
        taskId: taskId.value || '',
        chartType: chartType.value || '',
        config: config.value,
        stats: {
            rawCells: rawCount,
            filteredCells: filteredCount,
            ratio: rawCount > 0 ? Number(((filteredCount / rawCount) * 100).toFixed(2)) : 0,
        },
        filteredData: filteredCells.value,
    };
}

function getFrameFeatureValue(frame: any, feature: string): number {
    if (feature === 'area') return Number(frame.area ?? 0);
    if (feature === 'speed' || feature === 'migration_speed') return Number(frame.velocity?.speed ?? 0);
    return Number(frame[feature] ?? 0);
}

function getCellFrameValuesInRange(cell: CellData, feature: string, frameRange?: [number, number]): number[] {
    return cell.frames
        .filter((f: any) => {
            if (!frameRange) return true;
            return f.frame_number >= frameRange[0] && f.frame_number <= frameRange[1];
        })
        .map((f: any) => getFrameFeatureValue(f, feature))
        .filter((v) => Number.isFinite(v));
}

function getCellFeatureByFrame(cell: CellData, feature: string, frameNumber: number): number | null {
    const frame = cell.frames.find((f: any) => f.frame_number === frameNumber);
    if (!frame) return null;
    const value = getFrameFeatureValue(frame, feature);
    return Number.isFinite(value) ? value : null;
}

function buildHistogramBins(
    values: number[],
    min: number,
    max: number,
    binCount: number,
    probabilityType: 'probability' | 'count'
): number[] {
    const span = max - min || 1;
    const step = span / binCount;
    const bins = Array.from({ length: binCount }, () => 0);

    values.forEach((v) => {
        const index = Math.min(binCount - 1, Math.max(0, Math.floor((v - min) / step)));
        if (bins[index] !== undefined) {
            bins[index] += 1;
        }
    });

    if (probabilityType === 'probability') {
        const total = values.length || 1;
        return bins.map((n) => Number((n / total).toFixed(4)));
    }

    return bins;
}

function buildTimeSeriesOption(): echarts.EChartsOption {
    const feature = config.value?.yAxisFeature || 'area';
    const featureLabel = getFeatureLabel(feature);
    const series = filteredCells.value.slice(0, 30).map((cell, idx) => {
        const data = [...cell.frames]
            .sort((a, b) => a.frame_number - b.frame_number)
            .map((f: any) => [f.frame_number, getFrameFeatureValue(f, feature)]);

        return {
            name: cell.cell_id,
            type: 'line' as const,
            showSymbol: !!config.value?.showDataPoints,
            smooth: config.value?.lineType === 'smooth',
            lineStyle: {
                width: 1.2,
                color: academicPalette[idx % academicPalette.length],
            },
            data,
        };
    });

    return {
        color: academicPalette,
        animation: false,
        backgroundColor: '#ffffff',
        title: getCenteredTitle(`${chartTitle.value} - ${featureLabel}`),
        tooltip: {
            trigger: 'axis',
            textStyle: getTooltipTextStyle(),
            backgroundColor: 'rgba(255,255,255,0.95)',
            borderColor: '#d1d5db',
            borderWidth: 1,
        },
        legend: getBottomCenterLegend(),
        grid: {
            ...getAcademicGrid(),
            bottom: '20%',
        },
        xAxis: {
            type: 'value',
            name: '帧号',
            nameLocation: 'middle',
            nameGap: 40,
            axisLabel: getAxisLabelStyle(),
            nameTextStyle: getAxisNameStyle(),
            axisLine: getAcademicAxisLine(),
            splitLine: getAcademicSplitLine(),
            splitNumber: 14,
            minorTick: { show: true },
            minorSplitLine: { show: true, lineStyle: { color: '#e5e7eb', width: 1, opacity: 1 } },
        },
        yAxis: {
            type: 'value',
            name: featureLabel,
            nameLocation: 'middle',
            nameGap: 58,
            axisLabel: getAxisLabelStyle(),
            nameTextStyle: getAxisNameStyle(),
            axisLine: getAcademicAxisLine(),
            splitLine: getAcademicSplitLine(),
        },
        series,
    };
}

function buildHistogramOption(): echarts.EChartsOption {
    const feature = config.value?.xAxisFeature || 'area';
    const featureLabel = getFeatureLabel(feature);
    const statMode = config.value?.statMode || 'average';
    const frameMode = config.value?.frameMode || 'single';
    const selectedFrame = Number(config.value?.selectedFrame || 1);
    const selectedFrames = Array.isArray(config.value?.selectedFrames)
        ? config.value.selectedFrames.map((v: any) => Number(v)).filter((v: number) => Number.isFinite(v))
        : [1, 25, 50, 75];
    const frameRange = Array.isArray(config.value?.frameRange) ? config.value.frameRange as [number, number] : undefined;
    const probabilityType = (config.value?.probabilityType || 'probability') as 'probability' | 'count';
    const binCount = Math.max(1, Number(config.value?.binCount || 14));

    let valuesBySeries: Array<{ name: string; values: number[] }> = [];
    if (statMode === 'average') {
        const avgValues = filteredCells.value
            .map((cell) => {
                const vals = getCellFrameValuesInRange(cell, feature, frameRange);
                if (!vals.length) return null;
                return vals.reduce((s, v) => s + v, 0) / vals.length;
            })
            .filter((v): v is number => v !== null && Number.isFinite(v));

        valuesBySeries = [{ name: '平均值分布', values: avgValues }];
    } else {
        const framesForSeries: number[] = frameMode === 'single'
            ? [selectedFrame]
            : frameMode === 'quad'
                ? selectedFrames.slice(0, 4)
                : selectedFrames;

        valuesBySeries = framesForSeries.map((frameNo) => ({
            name: `Frame ${frameNo}`,
            values: filteredCells.value
                .map((cell) => getCellFeatureByFrame(cell, feature, frameNo))
                .filter((v): v is number => v !== null && Number.isFinite(v)),
        }));
    }

    const allValues = valuesBySeries.flatMap((item) => item.values);
    if (!allValues.length) {
        return { title: { text: '无可用数据' }, series: [] };
    }

    const min = Math.min(...allValues);
    const max = Math.max(...allValues);
    const step = (max - min || 1) / binCount;

    const labels = Array.from({ length: binCount }, (_, i) => {
        const start = min + i * step;
        const end = start + step;
        return `${start.toFixed(2)}-${end.toFixed(2)}`;
    });

    const histogramSeries = valuesBySeries.map((entry) => ({
        name: entry.name,
        type: 'bar' as const,
        barMaxWidth: frameMode === 'single' ? 32 : 20,
        itemStyle: { opacity: 0.85 },
        data: buildHistogramBins(entry.values, min, max, binCount, probabilityType),
    }));

    if (frameMode === 'quad' && !!config.value?.showQuadGrid && histogramSeries.length > 1) {
        const quadSeries = histogramSeries.slice(0, 4);
        const quadMeta = valuesBySeries.slice(0, 4);
        const grid = [
            { left: '8%', top: '14%', width: '36%', height: '30%' },
            { left: '56%', top: '14%', width: '36%', height: '30%' },
            { left: '8%', top: '58%', width: '36%', height: '30%' },
            { left: '56%', top: '58%', width: '36%', height: '30%' },
        ];

        const xAxis = quadSeries.map((item, idx) => ({
            type: 'category' as const,
            gridIndex: idx,
            data: labels,
            name: idx >= 2 ? featureLabel : '',
            axisLabel: getAxisLabelStyle(),
            nameTextStyle: getAxisNameStyle(),
            axisLine: getAcademicAxisLine(),
            splitLine: getAcademicSplitLine(),
        }));

        const yAxis = quadSeries.map((_, idx) => ({
            type: 'value' as const,
            gridIndex: idx,
            name: idx % 2 === 0 ? (probabilityType === 'probability' ? '概率' : '数量') : '',
            axisLabel: getAxisLabelStyle(),
            nameTextStyle: getAxisNameStyle(),
            axisLine: getAcademicAxisLine(),
            splitLine: getAcademicSplitLine(),
        }));

        return {
            title: getCenteredTitle(`${chartTitle.value} - ${featureLabel} (四宫格)`),
            tooltip: {
                trigger: 'axis',
                textStyle: getTooltipTextStyle(),
                formatter: (params: any) => {
                    const rows = Array.isArray(params) ? params : [params];
                    if (!rows.length) return '';
                    const axisLabel = rows[0]?.axisValueLabel ?? '';
                    const lines = rows
                        .map((item: any) => `${item.marker}${item.seriesName}: ${Number(item.value ?? 0).toFixed(4)}`)
                        .join('<br/>');
                    return `${axisLabel}<br/>${lines}`;
                },
            },
            graphic: quadMeta.map((meta, idx) => ({
                type: 'text',
                left: idx % 2 === 0 ? '8%' : '56%',
                top: idx < 2 ? '10%' : '54%',
                style: {
                    text: `${meta.name} | n=${meta.values.length}`,
                    fill: '#5f6b7a',
                    fontSize: legendFontSize.value,
                    fontWeight: 600,
                },
            })),
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
        };
    }

    return {
        color: academicPalette,
        animation: false,
        backgroundColor: '#ffffff',
        title: getCenteredTitle(`${chartTitle.value} - ${feature} (${statMode === 'average' ? '平均模式' : '按帧模式'})`),
        legend: histogramSeries.length > 1 ? getBottomCenterLegend() : undefined,
        tooltip: {
            trigger: 'axis',
            textStyle: getTooltipTextStyle(),
            backgroundColor: 'rgba(255,255,255,0.95)',
            borderColor: '#d1d5db',
            borderWidth: 1,
        },
        grid: histogramSeries.length > 1
            ? {
                ...getAcademicGrid(),
                bottom: '22%',
            }
            : getAcademicGrid(),
        xAxis: {
            type: 'category',
            data: labels,
            name: featureLabel,
            nameLocation: 'middle',
            nameGap: 48,
            nameTextStyle: getAxisNameStyle(),
            axisLine: getAcademicAxisLine(),
            splitLine: getAcademicSplitLine(),
            axisTick: { alignWithLabel: true },
            axisLabel: {
                ...getDenseAxisLabelStyle(),
                rotate: 35,
            },
        },
        yAxis: {
            type: 'value',
            name: probabilityType === 'probability' ? '概率' : '数量',
            nameLocation: 'middle',
            nameGap: 56,
            axisLabel: getAxisLabelStyle(),
            nameTextStyle: getAxisNameStyle(),
            axisLine: getAcademicAxisLine(),
            splitLine: getAcademicSplitLine(),
        },
        series: histogramSeries,
    };
}

function buildScatterOption(): echarts.EChartsOption {
    const allPoints = filteredCells.value.flatMap((cell) =>
        cell.frames.map((f: any) => ({
            cellId: cell.cell_id,
            frame: f.frame_number,
            x: Number(f.position?.x ?? 0),
            y: Number(f.position?.y ?? 0),
            value: config.value?.colorBy === 'area'
                ? Number(f.area ?? 0)
                : config.value?.colorBy === 'speed'
                    ? Number(f.velocity?.speed ?? 0)
                    : 0,
        }))
    );

    const frameMode = (config.value?.frameMode || 'single') === 'quad' ? 'quad' : 'single';
    const selectedFrame = getCurrentScatterFrame();
    const selectedFrames = Array.isArray(config.value?.selectedFrames)
        ? config.value.selectedFrames
            .map((v: any) => Number(v))
            .filter((v: number) => Number.isFinite(v))
        : [1, 25, 50, 75];

    let series: any[] = [];
    let title = `${chartTitle.value} - 第 ${selectedFrame} 帧`;
    const useColorMap = config.value?.colorBy === 'area' || config.value?.colorBy === 'speed';

    const getVisualMapRange = () => {
        const values = allPoints
            .map((p) => Number(p.value))
            .filter((v) => Number.isFinite(v));
        if (!values.length) return { min: 0, max: 1 };
        const min = Math.min(...values);
        const max = Math.max(...values);
        return { min, max: max > min ? max : min + 1 };
    };

    if (frameMode === 'quad') {
        title = `${chartTitle.value} - 四帧对比`;
        const quadFrames = selectedFrames.slice(0, 4);
        const quadPoints = allPoints.filter((p) => quadFrames.includes(p.frame));
        const quadBounds = getDataBounds(quadPoints.map((p) => [p.x, p.y] as [number, number]), 240);
        const grid = [
            { left: '8%', top: '14%', width: '36%', height: '32%', containLabel: false },
            { left: '56%', top: '14%', width: '36%', height: '32%', containLabel: false },
            { left: '8%', top: '56%', width: '36%', height: '32%', containLabel: false },
            { left: '56%', top: '56%', width: '36%', height: '32%', containLabel: false },
        ];

        const xAxis = quadFrames.map((_: number, idx: number) => ({
            type: 'value' as const,
            gridIndex: idx,
            min: quadBounds.xMin,
            max: quadBounds.xMax,
            name: '',
            axisLabel: getAxisLabelStyle(),
            nameTextStyle: getAxisNameStyle(),
            axisLine: getAcademicAxisLine(),
            splitLine: getAcademicSplitLine(),
            scale: true,
        }));

        const yAxis = quadFrames.map((_: number, idx: number) => ({
            type: 'value' as const,
            gridIndex: idx,
            min: quadBounds.yMin,
            max: quadBounds.yMax,
            name: '',
            axisLabel: getAxisLabelStyle(),
            nameTextStyle: getAxisNameStyle(),
            axisLine: getAcademicAxisLine(),
            splitLine: getAcademicSplitLine(),
            scale: true,
        }));

        const quadSeries = quadFrames.map((frameNo: number, idx: number) => {
            const framePoints = allPoints.filter((p) => p.frame === frameNo);
            return {
                name: `Frame ${frameNo}`,
                type: 'scatter' as const,
                symbolSize: Number(config.value?.pointSize || 8),
                itemStyle: { color: academicPalette[idx % academicPalette.length], opacity: 0.8 },
                xAxisIndex: idx,
                yAxisIndex: idx,
                data: framePoints.map((p) => ({
                    cellId: p.cellId,
                    frame: p.frame,
                    value: [p.x, p.y, p.value],
                })),
            };
        });

        return {
            color: academicPalette,
            animation: false,
            backgroundColor: '#ffffff',
            title: { text: title, textStyle: getTitleTextStyle() },
            tooltip: {
                textStyle: getTooltipTextStyle(),
                backgroundColor: 'rgba(255,255,255,0.95)',
                borderColor: '#d1d5db',
                borderWidth: 1,
                formatter: (params: any) => {
                    const d = params.data;
                    return `Cell: ${d.cellId}<br/>Frame: ${d.frame}<br/>X: ${Number(d.value[0] ?? 0).toFixed(2)} μm<br/>Y: ${Number(d.value[1] ?? 0).toFixed(2)} μm`;
                },
            },
            graphic: quadFrames.map((f: number, idx: number) => ({
                type: 'text',
                left: idx % 2 === 0 ? '8%' : '56%',
                top: idx < 2 ? '10%' : '52%',
                style: {
                    text: `Frame ${f}`,
                    fill: '#334155',
                    fontSize: legendFontSize.value,
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
        };
    } else {
        const points = allPoints.filter((p) => p.frame === selectedFrame);
        const showTrajectory = !!config.value?.showTrajectory;
        const trajectoryLength = Math.max(2, Number(config.value?.trajectoryLength || 10));

        const trajectorySeries = showTrajectory
            ? filteredCells.value
                .slice(0, 80)
                .map((cell) => {
                    const trail = [...cell.frames]
                        .sort((a, b) => a.frame_number - b.frame_number)
                        .filter((f: any) => f.frame_number <= selectedFrame)
                        .slice(-trajectoryLength)
                        .map((f: any) => [Number(f.position?.x ?? 0), Number(f.position?.y ?? 0)]);

                    if (trail.length < 2) return null;
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
                    };
                })
                .filter((s): s is NonNullable<typeof s> => s !== null)
            : [];

        series = [
            ...trajectorySeries,
            {
                type: 'scatter' as const,
                name: `Frame ${selectedFrame}`,
                symbolSize: Number(config.value?.pointSize || 8),
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
        ];
    }

    const scatterXY: Array<[number, number]> = series.flatMap((s: any) =>
        (s.data || []).map((item: any) => {
            if (Array.isArray(item)) return [Number(item[0] ?? 0), Number(item[1] ?? 0)] as [number, number];
            const v = item?.value;
            return [Number(v?.[0] ?? 0), Number(v?.[1] ?? 0)] as [number, number];
        })
    );
    const scatterBounds = getDataBounds(scatterXY, 240);

    const scatterSeriesIndex = series
        .map((s, idx) => ({ s, idx }))
        .filter(({ s }) => s?.type === 'scatter')
        .map(({ idx }) => idx);

    return {
        color: academicPalette,
        animation: false,
        backgroundColor: '#ffffff',
        title: getCenteredTitle(title),
        legend: undefined,
        tooltip: {
            textStyle: getTooltipTextStyle(),
            backgroundColor: 'rgba(255,255,255,0.95)',
            borderColor: '#d1d5db',
            borderWidth: 1,
            formatter: (params: any) => {
                const d = params.data;
                const colorInfo = useColorMap
                    ? `<br/>${config.value?.colorBy}: ${Number(d.value?.[2] ?? 0).toFixed(3)}`
                    : '';
                return `Cell: ${d.cellId}<br/>Frame: ${d.frame}<br/>X: ${Number(d.value[0] ?? 0).toFixed(2)} μm<br/>Y: ${Number(d.value[1] ?? 0).toFixed(2)} μm${colorInfo}`;
            },
        },
        grid: getAcademicGrid(useColorMap ? '18%' : '8%'),
        xAxis: {
            type: 'value',
            name: 'X 位置 (μm)',
            nameLocation: 'middle',
            nameGap: 40,
            axisLabel: getAxisLabelStyle(),
            nameTextStyle: getAxisNameStyle(),
            min: scatterBounds.xMin,
            max: scatterBounds.xMax,
            axisLine: getAcademicAxisLine(),
            splitLine: getAcademicSplitLine(),
            scale: true,
        },
        yAxis: {
            type: 'value',
            name: 'Y 位置 (μm)',
            nameLocation: 'middle',
            nameGap: 56,
            axisLabel: getAxisLabelStyle(),
            nameTextStyle: getAxisNameStyle(),
            min: scatterBounds.yMin,
            max: scatterBounds.yMax,
            axisLine: getAcademicAxisLine(),
            splitLine: getAcademicSplitLine(),
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
    };
}

function buildTrajectoryOption(): echarts.EChartsOption {
    const trajectoryType = config.value?.trajectoryType || 'normal';

    if (trajectoryType === '3d') {
        return {
            title: getCenteredTitle('3D 轨迹图由后端 Python 渲染'),
            series: [],
        };
    }

    const colorMap = config.value?.colorMap || 'time';
    const lineWidth = Number(config.value?.lineWidth || 2);
    const showStartPoint = !!config.value?.showStartPoint;
    const showEndPoint = !!config.value?.showEndPoint;
    const fadeEffect = !!config.value?.fadeEffect;

    const series = filteredCells.value.slice(0, 50).map((cell, idx) => {
        const sortedFrames = [...cell.frames].sort((a, b) => a.frame_number - b.frame_number);
        const first = sortedFrames[0];
        const baseX = trajectoryType === 'normalized'
            ? Number(first?.position?.x ?? 0)
            : 0;
        const baseY = trajectoryType === 'normalized'
            ? Number(first?.position?.y ?? 0)
            : 0;

        const data = sortedFrames.map((f: any) => {
            const frameNo = Number(f.frame_number ?? 0);
            const xRaw = Number(f.position?.x ?? 0) - baseX;
            const yRaw = Number(f.position?.y ?? 0) - baseY;
            const speed = Number(f.velocity?.speed ?? 0);
            const colorValue = colorMap === 'speed' ? speed : frameNo;
            return [xRaw, yRaw, colorValue, frameNo, speed];
        });

        const markData: Array<{ name: string; coord: number[] }> = [];
        if (showStartPoint && data.length > 0) {
            const start = data[0];
            if (start) {
                markData.push({ name: 'Start', coord: [start[0] ?? 0, start[1] ?? 0] });
            }
        }
        if (showEndPoint && data.length > 1) {
            const last = data[data.length - 1]!;
            markData.push({ name: 'End', coord: [last[0]!, last[1]!] });
        }

        return {
            name: cell.cell_id,
            type: 'line' as const,
            showSymbol: false,
            lineStyle: {
                width: lineWidth,
                opacity: fadeEffect ? 0.7 : 1,
                color: academicPalette[idx % academicPalette.length],
            },
            encode: { x: 0, y: 1 },
            data,
            markPoint: markData.length
                ? {
                    symbolSize: 26,
                    data: markData,
                }
                : undefined,
        };
    });

    const isNormalized = trajectoryType === 'normalized';
    const rawTrajectorySeries: any[] = series;

    const allXY = rawTrajectorySeries.flatMap((s: any) =>
        (s.data as number[][]).map((d) => [Number(d[0] ?? 0), Number(d[1] ?? 0)])
    );
    const maxAbs = allXY.length
        ? Math.max(
            ...allXY.map(([x, y]) => Math.max(Math.abs(Number(x ?? 0)), Math.abs(Number(y ?? 0))))
        )
        : 100;

    const concentricRadii = [200, 400];
    const boundRaw = Math.max(maxAbs + 30, ...concentricRadii.map((r) => r + 20));
    const bound = Math.ceil(boundRaw / 50) * 50;
    const trajectoryBounds = isNormalized
        ? { min: -bound, max: bound }
        : getDataBounds(allXY as Array<[number, number]>, 280);

    const circleSeries = isNormalized
        ? concentricRadii
            .filter((r) => r < bound)
            .map((r) => {
                const circleData = Array.from({ length: 181 }, (_, i) => {
                    const t = (Math.PI * 2 * i) / 180;
                    return [Number((r * Math.cos(t)).toFixed(4)), Number((r * Math.sin(t)).toFixed(4))];
                });

                return {
                    name: `__circle_${r}`,
                    type: 'line' as const,
                    silent: true,
                    showSymbol: false,
                    z: 1,
                    lineStyle: {
                        type: 'dashed' as const,
                        width: 1.3,
                        color: '#5f6773',
                        opacity: 0.95,
                    },
                    data: circleData,
                    tooltip: { show: false },
                };
            })
        : [];

    const crossSeries = isNormalized
        ? [
            {
                name: '__axis_x',
                type: 'line' as const,
                silent: true,
                showSymbol: false,
                z: 1,
                lineStyle: {
                    type: 'dashed' as const,
                    width: 1,
                    color: '#b0b3b9',
                    opacity: 0.7,
                },
                data: [[-bound, 0], [bound, 0]],
                tooltip: { show: false },
            },
            {
                name: '__axis_y',
                type: 'line' as const,
                silent: true,
                showSymbol: false,
                z: 1,
                lineStyle: {
                    type: 'dashed' as const,
                    width: 1,
                    color: '#b0b3b9',
                    opacity: 0.7,
                },
                data: [[0, -bound], [0, bound]],
                tooltip: { show: false },
            },
        ]
        : [];

    const radiusLabelSeries = isNormalized
        ? [
            {
                name: '__radius_labels',
                type: 'scatter' as const,
                silent: true,
                symbolSize: 2,
                itemStyle: { color: 'transparent' },
                label: {
                    show: true,
                    formatter: (p: any) => `${p.value?.[2] ?? ''} μm`,
                    color: '#2c2f36',
                    fontSize: baseFontSize.value,
                    position: 'right' as const,
                },
                data: concentricRadii
                    .filter((r) => r < bound)
                    .map((r) => [r, 0, r]),
                tooltip: { show: false },
                z: 2,
            },
        ]
        : [];

    const styledTrajectorySeries = rawTrajectorySeries.map((s: any) => ({
        ...s,
        z: 3,
        lineStyle: {
            ...s.lineStyle,
            opacity: isNormalized ? 0.82 : s.lineStyle?.opacity,
        },
    }));

    return {
        animation: false,
        backgroundColor: '#ffffff',
        color: academicPalette,
        title: getCenteredTitle(isNormalized ? 'Normalized Cell Trajectories' : chartTitle.value),
        tooltip: {
            trigger: 'item',
            textStyle: getTooltipTextStyle(),
            backgroundColor: 'rgba(255,255,255,0.95)',
            borderColor: '#d1d5db',
            borderWidth: 1,
            formatter: (params: any) => {
                if (String(params?.seriesName || '').startsWith('__')) return '';
                const d = params.data || [];
                return `${params.seriesName}<br/>X: ${Number(d[0] ?? 0).toFixed(2)}<br/>Y: ${Number(d[1] ?? 0).toFixed(2)}<br/>Frame: ${Number(d[3] ?? 0)}<br/>Speed: ${Number(d[4] ?? 0).toFixed(3)}`;
            },
        },
        legend: undefined,
        grid: isNormalized
            ? {
                left: '16%',
                right: '16%',
                top: '16%',
                bottom: '16%',
                containLabel: false,
            }
            : getAcademicGrid(),
        xAxis: {
            type: 'value',
            name: isNormalized ? 'Normalized X (μm)' : 'X 位置 (μm)',
            nameLocation: 'middle',
            nameGap: 40,
            nameTextStyle: getAxisNameStyle(),
            min: isNormalized ? (trajectoryBounds as { min: number; max: number }).min : (trajectoryBounds as { xMin: number }).xMin,
            max: isNormalized ? (trajectoryBounds as { min: number; max: number }).max : (trajectoryBounds as { xMax: number }).xMax,
            axisLine: getAcademicAxisLine(),
            splitLine: isNormalized
                ? { show: true, lineStyle: { color: '#9ca3af', width: 1.1, opacity: 0.95 } }
                : getAcademicSplitLine(),
            minorTick: isNormalized ? { show: true } : undefined,
            minorSplitLine: isNormalized ? { show: true, lineStyle: { color: '#d1d5db', width: 1, opacity: 0.8 } } : undefined,
            axisLabel: isNormalized ? { ...getAxisLabelStyle(), margin: 10 } : getAxisLabelStyle(),
            scale: true,
        },
        yAxis: {
            type: 'value',
            name: isNormalized ? 'Normalized Y (μm)' : 'Y 位置 (μm)',
            nameLocation: 'middle',
            nameGap: 56,
            nameTextStyle: getAxisNameStyle(),
            min: isNormalized ? (trajectoryBounds as { min: number; max: number }).min : (trajectoryBounds as { yMin: number }).yMin,
            max: isNormalized ? (trajectoryBounds as { min: number; max: number }).max : (trajectoryBounds as { yMax: number }).yMax,
            axisLine: getAcademicAxisLine(),
            splitLine: isNormalized
                ? { show: true, lineStyle: { color: '#9ca3af', width: 1.1, opacity: 0.95 } }
                : getAcademicSplitLine(),
            minorTick: isNormalized ? { show: true } : undefined,
            minorSplitLine: isNormalized ? { show: true, lineStyle: { color: '#d1d5db', width: 1, opacity: 0.8 } } : undefined,
            axisLabel: isNormalized ? { ...getAxisLabelStyle(), margin: 10 } : getAxisLabelStyle(),
            scale: true,
        },
        visualMap: undefined,
        series: [...circleSeries, ...crossSeries, ...radiusLabelSeries, ...styledTrajectorySeries],
    };
}

function buildOption(): echarts.EChartsOption {
    switch (chartType.value as DrawingChartType) {
        case 'timeSeries':
            return buildTimeSeriesOption();
        case 'histogram':
            return buildHistogramOption();
        case 'scatter':
            return buildScatterOption();
        case 'trajectory':
            return buildTrajectoryOption();
        default:
            return { title: { text: '不支持的图表类型' }, series: [] };
    }
}

function renderChart() {
    if (isPython3dMode()) return;
    if (!chartContainer.value || !filteredCells.value.length) return;

    if (!chartInstance.value) {
        chartInstance.value = echarts.init(chartContainer.value);
    }

    try {
        chartInstance.value.setOption(buildOption(), true);
    } catch (err: any) {
        throw err;
    }
}

async function loadData() {
    if (!taskId.value) {
        error.value = '未指定任务ID';
        return;
    }

    loading.value = true;
    error.value = null;

    try {
        const allCells = await analysisStore.getCellsForChart(taskId.value);
        cells.value = allCells;

        let tempFiltered = allCells;
        if (config.value) {
            tempFiltered = analysisStore.filterCells(allCells, config.value);
        }
        if (chartType.value) {
            tempFiltered = filterDataFields(tempFiltered, chartType.value, config.value);
        }

        filteredCells.value = tempFiltered;

        if (isPython3dMode()) {
            await loadTrajectory3dImage();
        }
    } catch (err: any) {
        error.value = `数据加载失败: ${err.message || err}`;
    } finally {
        loading.value = false;
        if (!error.value && filteredCells.value.length > 0) {
            await nextTick();
            renderChart();
        }
    }
}

function exportChartImage(options?: ExportChartImageOptions): string | null {
    if (isPython3dMode()) {
        return trajectory3dImageUrl.value;
    }
    if (!chartInstance.value) return null;

    return chartInstance.value.getDataURL({
        type: options?.type || 'png',
        pixelRatio: options?.pixelRatio || 2,
        backgroundColor: options?.backgroundColor || '#ffffff',
    });
}

function downloadChartImage(options?: ExportChartImageOptions): boolean {
    if (isPython3dMode()) {
        if (!trajectory3dImageUrl.value) return false;
        const ext = 'png';
        const filename = options?.filename || `trajectory-3d-${taskId.value || 'unknown'}.${ext}`;
        const link = document.createElement('a');
        link.href = trajectory3dImageUrl.value;
        link.download = filename;
        link.click();
        return true;
    }

    const dataUrl = exportChartImage(options);
    if (!dataUrl) return false;

    const ext = options?.type || 'png';
    const filename = options?.filename || `${chartType.value || 'chart'}-${taskId.value || 'unknown'}.${ext}`;
    const link = document.createElement('a');
    link.href = dataUrl;
    link.download = filename;
    link.click();
    return true;
}

function handleExportImage() {
    const ok = downloadChartImage({
        type: 'png',
        pixelRatio: 2,
        backgroundColor: '#ffffff',
        filename: `${chartType.value || 'chart'}-${taskId.value || 'unknown'}.png`,
    });
    if (!ok) return;
}

async function convertBlobUrlToDataUrl(blobUrl: string): Promise<string | null> {
    try {
        const res = await fetch(blobUrl);
        const blob = await res.blob();
        return await new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = () => resolve(typeof reader.result === 'string' ? reader.result : null);
            reader.onerror = () => resolve(null);
            reader.readAsDataURL(blob);
        });
    } catch {
        return null;
    }
}

async function applyToCompareSlot() {
    if (!isCompareReturn.value || !compareSlot.value) return;
    const exported = exportChartImage({
        type: 'png',
        pixelRatio: 4,
        backgroundColor: '#ffffff',
    });
    if (!exported) return;

    const imageDataUrl = isPython3dMode() && exported.startsWith('blob:')
        ? await convertBlobUrlToDataUrl(exported)
        : exported;
    if (!imageDataUrl) return;

    const payload = {
        slot: compareSlot.value,
        taskId: taskId.value || '',
        chartType: chartType.value || '',
        chartLabel: `${route.query.compareTaskName || ''} · ${chartTitle.value}`,
        imageDataUrl,
        updatedAt: Date.now(),
    };
    sessionStorage.setItem(`compareChartSlot_${compareSlot.value}`, JSON.stringify(payload));

    router.push({ name: 'compareResult' });
}

async function handleBatchExport() {
    await exportAllScatterFramesZip();
}

function handleResize() {
    chartInstance.value?.resize();
}

function goBack() {
    const returnTo = route.query.returnTo as string;
    if (returnTo === 'cellTracking') {
        router.push({
            name: 'cellTracking',
            state: { activeTab: 'chart' },
        });
    } else if (returnTo === 'compareResult') {
        router.push({ name: 'compareResult' });
    } else {
        router.back();
    }
}

watch(
    [filteredCells, chartType, config],
    async () => {
        if (chartType.value !== 'scatter' || (config.value?.frameMode || 'single') === 'quad') {
            scatterBatchMode.value = false;
        }
        if (isPython3dMode()) {
            await loadTrajectory3dImage();
            return;
        }
        await nextTick();
        renderChart();
    },
    { deep: true }
);

watch(loading, async (isLoading) => {
    if (!isLoading && !error.value && filteredCells.value.length > 0) {
        await nextTick();
        renderChart();
    }
});

let fontChangeTimer: ReturnType<typeof setTimeout> | null = null;
watch([baseFontSize, legendFontSize, titleFontSize], async ([base, legend, title]) => {
    sessionStorage.setItem('drawingBaseFontSize', String(base));
    sessionStorage.setItem('drawingLegendFontSize', String(legend));
    sessionStorage.setItem('drawingTitleFontSize', String(title));

    if (fontChangeTimer) {
        clearTimeout(fontChangeTimer);
    }
    fontChangeTimer = setTimeout(async () => {
        await nextTick();
        renderChart();
    }, 120);
});

onMounted(async () => {
    window.__drawingCanvasDebugApi = {
        getTwoStageFilteredData: buildValidationSnapshot,
        exportChartImage,
        downloadChartImage,
    };
    window.addEventListener('resize', handleResize);
    await loadData();
});

onUnmounted(() => {
    window.removeEventListener('resize', handleResize);
    if (chartInstance.value) {
        chartInstance.value.dispose();
        chartInstance.value = null;
    }
    if (window.__drawingCanvasDebugApi) {
        delete window.__drawingCanvasDebugApi;
    }
    if (trajectory3dImageUrl.value) {
        URL.revokeObjectURL(trajectory3dImageUrl.value);
    }
});
</script>

<template>
    <div class="drawing-canvas">
        <div class="header">
            <button class="btn-back" @click="goBack">← 返回</button>
            <h2>{{ chartTitle }}</h2>
            <div class="header-actions">
                <div class="font-control">
                    <label>字号x</label>
                    <input v-model.number="baseFontSize" type="range" min="10" max="22" step="1" />
                    <span>{{ baseFontSize }}</span>
                </div>
                <div class="font-control">
                    <label>图例</label>
                    <input v-model.number="legendFontSize" type="range" min="10" max="20" step="1" />
                    <span>{{ legendFontSize }}</span>
                </div>
                <div class="font-control">
                    <label>标题</label>
                    <input v-model.number="titleFontSize" type="range" min="12" max="24" step="1" />
                    <span>{{ titleFontSize }}</span>
                </div>
                <button class="btn-export" @click="handleExportImage" :disabled="loading || !!error || filteredCells.length === 0">
                    导出图片
                </button>
                <button v-if="isCompareReturn" class="btn-export" @click="applyToCompareSlot" :disabled="loading || !!error || filteredCells.length === 0">
                    应用到对比{{ compareSlot }}
                </button>
                <template v-if="isScatterSingleMode() && !isPython3dMode()">
                    <button class="btn-export" @click="enableScatterBatchMode" :disabled="loading || !!error || filteredCells.length === 0">
                        批量生成
                    </button>
                    <button class="btn-export" @click="prevScatterFrame" :disabled="!scatterBatchMode || scatterBatchIndex <= 0">
                        ←
                    </button>
                    <span v-if="scatterBatchMode" class="batch-indicator">{{ (scatterBatchIndex + 1) }}/{{ scatterBatchFrames.length }}</span>
                    <button class="btn-export" @click="nextScatterFrame" :disabled="!scatterBatchMode || scatterBatchIndex >= scatterBatchFrames.length - 1">
                        →
                    </button>
                    <button class="btn-export" @click="handleBatchExport" :disabled="!scatterBatchMode || scatterBatchExporting">
                        {{ scatterBatchExporting ? '导出中...' : '批量导出' }}
                    </button>
                </template>
            </div>
        </div>

        <div class="main-content">
            <div v-if="loading" class="state">加载细胞数据中...</div>
            <div v-else-if="error" class="state error">
                <p>{{ error }}</p>
                <button class="btn-back" @click="loadData">重试</button>
            </div>
            <div v-else-if="filteredCells.length === 0" class="state">无可绘制数据</div>
            <div v-else-if="isPython3dMode()" class="python-3d-wrap">
                <div v-if="trajectory3dLoading" class="state">正在生成 3D 轨迹图...</div>
                <img v-else-if="trajectory3dImageUrl" class="python-3d-image" :src="trajectory3dImageUrl" alt="3D轨迹图" />
                <div v-else class="state error">3D 轨迹图生成失败</div>
            </div>
            <div
                v-else
                ref="chartContainer"
                :class="[
                    'chart-container',
                    {
                        'chart-container-square': isSquareChart,
                        'chart-container-tall': isTallChart,
                    },
                ]"
            ></div>
        </div>
    </div>
</template>

<style scoped>
.drawing-canvas {
    min-height: 100vh;
    background-color: var(--bg-main);
    display: flex;
    flex-direction: column;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    background-color: var(--bg-card);
    border-bottom: 1px solid var(--border-color);
}

.header h2 {
    margin: 0;
    font-size: 18px;
    color: var(--text-primary);
}

.btn-back,
.btn-export {
    padding: 8px 14px;
    border-radius: 6px;
    border: 1px solid var(--border-color);
    background-color: var(--bg-input);
    color: var(--text-primary);
    cursor: pointer;
}

.btn-export {
    background-color: var(--accent-blue);
    border-color: var(--accent-blue);
    color: #fff;
}

.btn-export:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.header-actions {
    display: flex;
    align-items: center;
    gap: 10px;
}

.font-control {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--text-secondary);
    font-size: 12px;
}

.font-control input[type='range'] {
    width: 88px;
}

.batch-indicator {
    min-width: 56px;
    text-align: center;
    color: var(--text-secondary);
    font-size: 12px;
}

.main-content {
    flex: 1;
    padding: 20px;
    display: flex;
    justify-content: center;
    align-items: center;
}

.state {
    margin: auto;
    color: var(--text-secondary);
    text-align: center;
}

.state.error p {
    margin-bottom: 12px;
}

.chart-container {
    width: min(100%, 1400px);
    height: calc(100vh - 140px);
    min-height: 520px;
    max-height: 860px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    margin: 0 auto;
}

.chart-container-tall {
    width: min(100%, 1100px);
    height: auto;
    aspect-ratio: 5 / 4;
    min-height: min(620px, calc(100vh - 180px));
    max-height: min(900px, calc(100vh - 140px));
}

.chart-container-square {
    width: min(100%, calc(100vh - 180px));
    height: auto;
    aspect-ratio: 1 / 1;
    min-height: 0;
    margin: 0 auto;
}

.python-3d-wrap {
    width: 100%;
    height: calc(100vh - 140px);
    min-height: 520px;
    max-height: 860px;
    background: #fff;
    border: 1px solid var(--border-color);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.python-3d-image {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
}
</style>