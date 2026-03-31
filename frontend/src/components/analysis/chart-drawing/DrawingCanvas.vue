<script setup lang="ts">
import '@/assets/styles/colors.css';
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAnalysisStore } from '@/stores/analysisStore';
import type { CellData } from '@/stores/analysisStore';
import * as echarts from 'echarts';
import { buildOption as libBuildOption, filterDataFields as libFilterDataFields } from '@/lib/chartBuilder';
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
        const raw = JSON.parse(route.query.config as string);
        if (!raw || typeof raw !== 'object') return raw;

        // Normalize common fields used by drawing functions
        // Ensure frameMode is either 'single' or 'quad' when present
        if (raw.frameMode) {
            raw.frameMode = raw.frameMode === 'quad' ? 'quad' : 'single';
        }

        // Normalize selectedFrames to number[] if provided (for quad mode)
        if (Array.isArray(raw.selectedFrames)) {
            raw.selectedFrames = raw.selectedFrames
                .map((v: any) => Number(v))
                .filter((n: number) => Number.isFinite(n));
        }

        // Ensure selectedFrame is a finite number
        if (raw.selectedFrame !== undefined) {
            const sf = Number(raw.selectedFrame);
            raw.selectedFrame = Number.isFinite(sf) ? sf : 1;
        }

        return raw;
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

function filterDataFields(cellsInput: CellData[], type: string, cfg: any): CellData[] {
    return libFilterDataFields(cellsInput, type, cfg);
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

function buildOption(): echarts.EChartsOption {
    const runtimeConfig = {
        ...(config.value || {}),
    };

    // In scatter single-frame batch mode, override selectedFrame with current batch frame.
    if (chartType.value === 'scatter' && (runtimeConfig.frameMode || 'single') !== 'quad' && scatterBatchMode.value) {
        runtimeConfig.selectedFrame = getCurrentScatterFrame();
    }

    return libBuildOption(chartType.value as any, filteredCells.value, runtimeConfig, {
        baseFontSize: baseFontSize.value,
        legendFontSize: legendFontSize.value,
        titleFontSize: titleFontSize.value,
    }) as unknown as echarts.EChartsOption;
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