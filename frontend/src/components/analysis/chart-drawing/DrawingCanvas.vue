<script setup lang="ts">
import '@/assets/styles/colors.css';
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAnalysisStore } from '@/stores/analysisStore';
import type { CellData } from '@/stores/analysisStore';
import * as echarts from 'echarts';
import 'echarts-gl';

const route = useRoute();
const router = useRouter();
const analysisStore = useAnalysisStore();

const chartType = computed(() => route.query.type as string);
const taskId = computed(() => route.query.taskId as string);
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
const baseFontSize = ref(Number(sessionStorage.getItem('drawingBaseFontSize') || 14));
const legendFontSize = ref(Number(sessionStorage.getItem('drawingLegendFontSize') || 12));

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

declare global {
    interface Window {
        __drawingCanvasDebugApi?: DrawingCanvasDebugApi;
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

function getTitleTextStyle() {
    return { fontSize: baseFontSize.value + 4 };
}

function getAxisLabelStyle() {
    return { fontSize: baseFontSize.value };
}

function getAxisNameStyle() {
    return { fontSize: baseFontSize.value };
}

function getLegendTextStyle() {
    return { fontSize: legendFontSize.value };
}

function getTooltipTextStyle() {
    return { fontSize: baseFontSize.value };
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
    const series = filteredCells.value.slice(0, 30).map((cell) => {
        const data = [...cell.frames]
            .sort((a, b) => a.frame_number - b.frame_number)
            .map((f: any) => [f.frame_number, getFrameFeatureValue(f, feature)]);

        return {
            name: cell.cell_id,
            type: 'line' as const,
            showSymbol: !!config.value?.showDataPoints,
            smooth: config.value?.lineType === 'smooth',
            data,
        };
    });

    return {
        title: { text: `${chartTitle.value} - ${feature}`, textStyle: getTitleTextStyle() },
        tooltip: { trigger: 'axis', textStyle: getTooltipTextStyle() },
        legend: { type: 'scroll', textStyle: getLegendTextStyle() },
        xAxis: { type: 'value', name: '帧号', axisLabel: getAxisLabelStyle(), nameTextStyle: getAxisNameStyle() },
        yAxis: { type: 'value', name: feature, axisLabel: getAxisLabelStyle(), nameTextStyle: getAxisNameStyle() },
        series,
    };
}

function buildHistogramOption(): echarts.EChartsOption {
    const feature = config.value?.xAxisFeature || 'area';
    const statMode = config.value?.statMode || 'average';
    const frameMode = config.value?.frameMode || 'single';
    const selectedFrame = Number(config.value?.selectedFrame || 1);
    const selectedFrames = Array.isArray(config.value?.selectedFrames)
        ? config.value.selectedFrames.map((v: any) => Number(v)).filter((v: number) => Number.isFinite(v))
        : [1, 25, 50, 75];
    const frameRange = Array.isArray(config.value?.frameRange) ? config.value.frameRange as [number, number] : undefined;
    const probabilityType = (config.value?.probabilityType || 'probability') as 'probability' | 'count';
    const binCount = Math.max(1, Number(config.value?.binCount || 10));

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
            name: idx >= 2 ? feature : '',
            axisLabel: getAxisLabelStyle(),
            nameTextStyle: getAxisNameStyle(),
        }));

        const yAxis = quadSeries.map((_, idx) => ({
            type: 'value' as const,
            gridIndex: idx,
            name: idx % 2 === 0 ? (probabilityType === 'probability' ? '概率' : '数量') : '',
            axisLabel: getAxisLabelStyle(),
            nameTextStyle: getAxisNameStyle(),
        }));

        return {
            title: {
                text: `${chartTitle.value} - ${feature} (四宫格)`,
                textStyle: getTitleTextStyle(),
            },
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
        title: {
            text: `${chartTitle.value} - ${feature} (${statMode === 'average' ? '平均模式' : '按帧模式'})`,
            textStyle: getTitleTextStyle(),
        },
        legend: histogramSeries.length > 1 ? { type: 'scroll', textStyle: getLegendTextStyle() } : undefined,
        tooltip: { trigger: 'axis', textStyle: getTooltipTextStyle() },
        xAxis: { type: 'category', data: labels, name: feature, axisLabel: getAxisLabelStyle(), nameTextStyle: getAxisNameStyle() },
        yAxis: { type: 'value', name: probabilityType === 'probability' ? '概率' : '数量', axisLabel: getAxisLabelStyle(), nameTextStyle: getAxisNameStyle() },
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

    const frameMode = config.value?.frameMode || 'single';
    const selectedFrame = Number(config.value?.selectedFrame || 1);
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
        series = selectedFrames.slice(0, 4).map((frameNo: number) => {
            const framePoints = allPoints.filter((p) => p.frame === frameNo);
            return {
                name: `Frame ${frameNo}`,
                type: 'scatter' as const,
                symbolSize: Number(config.value?.pointSize || 8),
                data: framePoints.map((p) => ({
                    cellId: p.cellId,
                    frame: p.frame,
                    value: [p.x, p.y, p.value],
                })),
            };
        });
    } else if (frameMode === 'sequence') {
        title = `${chartTitle.value} - 序列帧`;
        series = selectedFrames.map((frameNo: number) => {
            const framePoints = allPoints.filter((p) => p.frame === frameNo);
            return {
                name: `Frame ${frameNo}`,
                type: 'scatter' as const,
                symbolSize: Number(config.value?.pointSize || 8),
                data: framePoints.map((p) => ({
                    cellId: p.cellId,
                    frame: p.frame,
                    value: [p.x, p.y, p.value],
                })),
            };
        });
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
        title: { text: title, textStyle: getTitleTextStyle() },
        legend: undefined,
        tooltip: {
            textStyle: getTooltipTextStyle(),
            formatter: (params: any) => {
                const d = params.data;
                const colorInfo = useColorMap
                    ? `<br/>${config.value?.colorBy}: ${Number(d.value?.[2] ?? 0).toFixed(3)}`
                    : '';
                return `Cell: ${d.cellId}<br/>Frame: ${d.frame}<br/>X: ${d.value[0]}<br/>Y: ${d.value[1]}${colorInfo}`;
            },
        },
        grid: { left: '8%', right: '8%', top: '8%', bottom: '8%', containLabel: true },
        xAxis: {
            type: 'value',
            name: 'X',
            axisLabel: getAxisLabelStyle(),
            nameTextStyle: getAxisNameStyle(),
            min: scatterBounds.xMin,
            max: scatterBounds.xMax,
            splitLine: { show: true, lineStyle: { opacity: 0.18 } },
            scale: true,
        },
        yAxis: {
            type: 'value',
            name: 'Y',
            axisLabel: getAxisLabelStyle(),
            nameTextStyle: getAxisNameStyle(),
            min: scatterBounds.yMin,
            max: scatterBounds.yMax,
            splitLine: { show: true, lineStyle: { opacity: 0.18 } },
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
            }
            : undefined,
        series,
    };
}

function buildTrajectoryOption(): echarts.EChartsOption {
    const trajectoryType = config.value?.trajectoryType || 'normal';

    if (trajectoryType === '3d') {
        const elev = Number(config.value?.viewElev ?? 20);
        const azim = Number(config.value?.viewAzim ?? 120);
        const distance = Number(config.value?.viewDistance ?? 180);
        const colorMap = config.value?.colorMap || 'track';

        const palette = [
            '#e15759', '#4e79a7', '#59a14f', '#f28e2b', '#af7aa1', '#76b7b2', '#edc948', '#ff9da7',
            '#9c755f', '#bab0ab', '#2ca02c', '#17becf', '#bcbd22', '#1f77b4', '#d62728', '#9467bd',
        ];

        const series3D = filteredCells.value.slice(0, 80).map((cell, idx) => {
            const sortedFrames = [...cell.frames].sort((a, b) => a.frame_number - b.frame_number);
            const data = sortedFrames.map((f: any) => {
                const x = Number(f.position?.x ?? 0);
                const y = Number(f.position?.y ?? 0);
                const frameNo = Number(f.frame_number ?? 0);
                const speed = Number(f.velocity?.speed ?? 0);
                // [x, y, z, colorValue, frame, speed]
                return [x, y, frameNo, colorMap === 'speed' ? speed : frameNo, frameNo, speed];
            });

            return {
                name: cell.cell_id,
                type: 'line3D',
                coordinateSystem: 'cartesian3D',
                data,
                lineStyle: {
                    width: Math.max(1, Number(config.value?.lineWidth || 2)),
                    opacity: 0.88,
                    color: colorMap === 'cell_id' ? palette[idx % palette.length] : undefined,
                },
            };
        });

        const option3D: any = {
            title: {
                text: `${chartTitle.value} (3D)`,
                textStyle: getTitleTextStyle(),
            },
            legend: undefined,
            tooltip: {
                textStyle: getTooltipTextStyle(),
                formatter: (params: any) => {
                    const d = params?.data || [];
                    return `${params.seriesName}<br/>X: ${Number(d[0] ?? 0).toFixed(2)}<br/>Y: ${Number(d[1] ?? 0).toFixed(2)}<br/>Frame: ${Number(d[4] ?? 0)}<br/>Speed: ${Number(d[5] ?? 0).toFixed(3)}`;
                },
            },
            grid3D: {
                boxWidth: 160,
                boxDepth: 120,
                boxHeight: 90,
                axisLine: { lineStyle: { color: '#6f7682' } },
                axisLabel: { color: '#2c2f36', fontSize: Math.max(10, baseFontSize.value - 1) },
                axisPointer: {
                    show: true,
                },
                viewControl: {
                    projection: 'perspective',
                    alpha: elev,
                    beta: azim,
                    distance,
                    rotateSensitivity: 1,
                    zoomSensitivity: 0.8,
                    panSensitivity: 0.8,
                },
                light: {
                    main: { intensity: 1.1, shadow: true },
                    ambient: { intensity: 0.45 },
                },
            },
            xAxis3D: {
                type: 'value',
                name: 'X Position (μm)',
                axisLabel: getAxisLabelStyle(),
                nameTextStyle: getAxisNameStyle(),
            },
            yAxis3D: {
                type: 'value',
                name: 'Y Position (μm)',
                axisLabel: getAxisLabelStyle(),
                nameTextStyle: getAxisNameStyle(),
            },
            zAxis3D: {
                type: 'value',
                name: 'Time (frame)',
                axisLabel: getAxisLabelStyle(),
                nameTextStyle: getAxisNameStyle(),
            },
            visualMap: undefined,
            series: series3D,
        };

        return option3D as echarts.EChartsOption;
    }

    const colorMap = config.value?.colorMap || 'time';
    const lineWidth = Number(config.value?.lineWidth || 2);
    const showStartPoint = !!config.value?.showStartPoint;
    const showEndPoint = !!config.value?.showEndPoint;
    const fadeEffect = !!config.value?.fadeEffect;

    const series = filteredCells.value.slice(0, 50).map((cell) => {
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
                        width: 1,
                        color: '#a9acb2',
                        opacity: 0.75,
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
        title: {
            text: isNormalized ? 'Normalized Cell Trajectories' : chartTitle.value,
            textStyle: getTitleTextStyle(),
        },
        tooltip: {
            trigger: 'item',
            textStyle: getTooltipTextStyle(),
            formatter: (params: any) => {
                if (String(params?.seriesName || '').startsWith('__')) return '';
                const d = params.data || [];
                return `${params.seriesName}<br/>X: ${Number(d[0] ?? 0).toFixed(2)}<br/>Y: ${Number(d[1] ?? 0).toFixed(2)}<br/>Frame: ${Number(d[3] ?? 0)}<br/>Speed: ${Number(d[4] ?? 0).toFixed(3)}`;
            },
        },
        legend: undefined,
        grid: { left: '8%', right: '8%', top: '8%', bottom: '8%', containLabel: true },
        xAxis: {
            type: 'value',
            name: isNormalized ? 'Normalized X (μm)' : 'X',
            axisLabel: getAxisLabelStyle(),
            nameTextStyle: getAxisNameStyle(),
            min: isNormalized ? (trajectoryBounds as { min: number; max: number }).min : (trajectoryBounds as { xMin: number }).xMin,
            max: isNormalized ? (trajectoryBounds as { min: number; max: number }).max : (trajectoryBounds as { xMax: number }).xMax,
            splitLine: { show: false },
            scale: true,
        },
        yAxis: {
            type: 'value',
            name: isNormalized ? 'Normalized Y (μm)' : 'Y',
            axisLabel: getAxisLabelStyle(),
            nameTextStyle: getAxisNameStyle(),
            min: isNormalized ? (trajectoryBounds as { min: number; max: number }).min : (trajectoryBounds as { yMin: number }).yMin,
            max: isNormalized ? (trajectoryBounds as { min: number; max: number }).max : (trajectoryBounds as { yMax: number }).yMax,
            splitLine: { show: false },
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
    if (!chartContainer.value || !filteredCells.value.length) return;

    if (!chartInstance.value) {
        chartInstance.value = echarts.init(chartContainer.value);
    }

    chartInstance.value.setOption(buildOption(), true);
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
    if (!chartInstance.value) return null;

    return chartInstance.value.getDataURL({
        type: options?.type || 'png',
        pixelRatio: options?.pixelRatio || 2,
        backgroundColor: options?.backgroundColor || '#ffffff',
    });
}

function downloadChartImage(options?: ExportChartImageOptions): boolean {
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
    } else {
        router.back();
    }
}

watch(
    [filteredCells, chartType, config],
    async () => {
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

watch([baseFontSize, legendFontSize], async ([base, legend]) => {
    sessionStorage.setItem('drawingBaseFontSize', String(base));
    sessionStorage.setItem('drawingLegendFontSize', String(legend));
    await nextTick();
    renderChart();
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
});
</script>

<template>
    <div class="drawing-canvas">
        <div class="header">
            <button class="btn-back" @click="goBack">← 返回</button>
            <h2>{{ chartTitle }}</h2>
            <div class="header-actions">
                <div class="font-control">
                    <label>字体</label>
                    <input v-model.number="baseFontSize" type="range" min="10" max="22" step="1" />
                    <span>{{ baseFontSize }}</span>
                </div>
                <div class="font-control">
                    <label>图例</label>
                    <input v-model.number="legendFontSize" type="range" min="10" max="20" step="1" />
                    <span>{{ legendFontSize }}</span>
                </div>
                <button class="btn-export" @click="handleExportImage" :disabled="loading || !!error || filteredCells.length === 0">
                    导出图片
                </button>
            </div>
        </div>

        <div class="main-content">
            <div v-if="loading" class="state">加载细胞数据中...</div>
            <div v-else-if="error" class="state error">
                <p>{{ error }}</p>
                <button class="btn-back" @click="loadData">重试</button>
            </div>
            <div v-else-if="filteredCells.length === 0" class="state">无可绘制数据</div>
            <div
                v-else
                ref="chartContainer"
                :class="['chart-container', { 'chart-container-square': isSquareChart }]"
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
    width: 100%;
    height: calc(100vh - 140px);
    min-height: 520px;
    max-height: 860px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
}

.chart-container-square {
    width: min(100%, calc(100vh - 180px));
    height: auto;
    aspect-ratio: 1 / 1;
    min-height: 0;
    margin: 0 auto;
}
</style>