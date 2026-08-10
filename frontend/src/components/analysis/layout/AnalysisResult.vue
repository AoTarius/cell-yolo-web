<script setup lang="ts">
import '@/assets/styles/colors.css'
import { ref, watch } from 'vue'
import { useAnalysisStore } from '@/stores/analysisStore'
import type { AnalysisRecord } from '@/stores/analysisStore'
import { useAnalysisApi } from '@/composables/useAnalysisApi'
import { useToast } from '@/composables/useToast'
import CellDetailPanel from '../cell-details/CellDetailPanel.vue'
import ResultHeader from './ResultHeader.vue'
import VideoComparison from '../video-comparison/VideoComparison.vue'
import CellDetails from '../cell-details/CellDetails.vue'
import ChartDrawing from '../chart-drawing/ChartDrawing.vue'
import FrameAnalysis from '../frame-analysis/FrameAnalysis.vue'
import { onMounted } from 'vue'
type TabType = 'video' | 'cell' | 'chart' | 'frame'

const props = defineProps<{
  record: AnalysisRecord
}>()

const store = useAnalysisStore()
const api = useAnalysisApi()
const { showToast } = useToast()
const previousTaskId = ref<string | null>(null)

// 当前激活的选项卡，默认为视频对比
const activeTab = ref<TabType>('video')

onMounted(() => {
  // 初始化 previousTaskId
  previousTaskId.value = props.record?.task_id || null

  // 恢复选项卡状态
  const savedTab = sessionStorage.getItem('activeTab')
  if (savedTab) {
    activeTab.value = savedTab as TabType
  } else if (sessionStorage.getItem('returnToChart') === 'true') {
    activeTab.value = 'chart'
    sessionStorage.removeItem('returnToChart')
  }
})

// 切换标签时保存状态
watch(activeTab, (newTab) => {
  sessionStorage.setItem('activeTab', newTab)
  sessionStorage.removeItem('returnToChart')
})

// 监听 record 变化，切换任务时重置为默认选项卡
watch(() => props.record?.task_id, (newTaskId, oldTaskId) => {
  if (newTaskId !== oldTaskId) {
    activeTab.value = 'video'
    previousTaskId.value = newTaskId || null
  }
})

const isExportingCsv = ref(false)
const isExportingJson = ref(false)
const isDownloadingVideo = ref(false)
const isDownloadingDataPackage = ref(false)
const exportError = ref<string | null>(null)

// 处理返回结果列表
function handleBackToList() {
  store.backToResultList()
}

// 处理数据导出
async function handleExport(format: 'csv' | 'json' = 'csv') {
  const stateVar = format === 'csv' ? isExportingCsv : isExportingJson
  try {
    stateVar.value = true
    exportError.value = null
    await api.exportData(props.record.task_id, format)
    showToast(`数据已成功导出为 ${format.toUpperCase()} 格式`, 'success')
  } catch (error: any) {
    exportError.value = error.message || '导出失败'
    console.error('Export error:', error)
    showToast(error.message || '导出失败', 'error')
  } finally {
    stateVar.value = false
  }
}

// 处理视频下载
async function handleDownloadVideo() {
  try {
    isDownloadingVideo.value = true
    exportError.value = null
    await api.downloadVideo(props.record.task_id, props.record.video_name)
    showToast('标注视频下载成功！', 'success')
  } catch (error: any) {
    exportError.value = error.message || '下载失败'
    console.error('Download error:', error)
    showToast(error.message || '下载失败', 'error')
  } finally {
    isDownloadingVideo.value = false
  }
}

// 处理数据包下载
async function handleDownloadDataPackage() {
  try {
    isDownloadingDataPackage.value = true
    exportError.value = null
    await api.downloadDataPackage(props.record.task_id, props.record.task_name || props.record.video_name)
    showToast('数据包导出成功！', 'success')
  } catch (error: any) {
    exportError.value = error.message || '导出失败'
    console.error('Data package download error:', error)
    showToast(error.message || '导出失败', 'error')
  } finally {
    isDownloadingDataPackage.value = false
  }
}

// 处理视频错误
function handleVideoError() {
  exportError.value = '视频加载失败'
}

// 处理选项卡切换
function handleTabChange(tab: TabType) {
  activeTab.value = tab
}
</script>

<template>
  <!-- 显示细胞详情 -->
  <CellDetailPanel
    v-if="store.selectedCellData"
    :cell-data="store.selectedCellData"
    :cell-id="store.selectedCellId ?? undefined"
    @back="handleBackToList"
  />

  <!-- 显示结果列表 -->
  <div v-else class="result-panel">
    <!-- 结果头部 -->
    <ResultHeader
      :record="record"
      :is-exporting-csv="isExportingCsv"
      :is-exporting-json="isExportingJson"
      :is-downloading-video="isDownloadingVideo"
      :is-downloading-data-package="isDownloadingDataPackage"
      :activeTab="activeTab"
      @export="handleExport"
      @download="handleDownloadVideo"
      @downloadDataPackage="handleDownloadDataPackage"
      @tabChange="handleTabChange"
    />

    <div class="result-content">
      <!-- 视频对比 -->
      <VideoComparison
        v-if="activeTab === 'video'"
        :record="record"
        @video-error="handleVideoError"
      />

      <!-- 细胞详情 -->
      <CellDetails v-else-if="activeTab === 'cell'" />

      <!-- 图表绘制 -->
      <ChartDrawing v-else-if="activeTab === 'chart'" />

      <!-- 逐帧分析 -->
      <FrameAnalysis
        v-else-if="activeTab === 'frame'"
        :record="record"
      />
    </div>
  </div>
</template>

<style scoped>
.result-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-main);
  overflow: hidden;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .result-panel {
  background: var(--bg-main-light);
}

.result-content {
  flex: 1;
  overflow-y: auto;
  padding: 2rem 2rem 0.5rem 2rem;
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
</style>
