<script setup lang="ts">
import '@/assets/styles/colors.css'
import { ref, watch } from 'vue'
import { useAnalysisStore } from '@/stores/analysisStore'
import type { AnalysisRecord } from '@/stores/analysisStore'
import { useAnalysisApi } from '@/composables/useAnalysisApi'
import { useToast } from '@/composables/useToast'
import CellDetailPanel from './CellDetailPanel.vue'
import ResultHeader from './ResultHeader.vue'
import VideoComparison from './VideoComparison.vue'
import CellDetails from './CellDetails.vue'
import ChartDrawing from './ChartDrawing.vue'
import FrameAnalysis from './FrameAnalysis.vue'

type TabType = 'video' | 'cell' | 'chart' | 'frame'

const props = defineProps<{
  record: AnalysisRecord
}>()

const store = useAnalysisStore()
const api = useAnalysisApi()
const { showToast } = useToast()

// 当前激活的选项卡，默认为视频对比
const activeTab = ref<TabType>('video')

// 监听 record 变化，切换记录时重置为默认选项卡
watch(() => props.record, () => {
  activeTab.value = 'video'
})

const isExporting = ref(false)
const exportError = ref<string | null>(null)

// 处理返回结果列表
function handleBackToList() {
  store.backToResultList()
}

// 处理数据导出
async function handleExport(format: 'csv' | 'json' = 'csv') {
  try {
    isExporting.value = true
    exportError.value = null
    await api.exportData(props.record.task_id, format)
    showToast(`数据已成功导出为 ${format.toUpperCase()} 格式`, 'success')
  } catch (error: any) {
    exportError.value = error.message || '导出失败'
    console.error('Export error:', error)
    showToast(error.message || '导出失败', 'error')
  } finally {
    isExporting.value = false
  }
}

// 处理视频下载
async function handleDownloadVideo() {
  try {
    isExporting.value = true
    exportError.value = null
    await api.downloadVideo(props.record.task_id, props.record.video_name)
    showToast('标注视频下载成功！', 'success')
  } catch (error: any) {
    exportError.value = error.message || '下载失败'
    console.error('Download error:', error)
    showToast(error.message || '下载失败', 'error')
  } finally {
    isExporting.value = false
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
    @back="handleBackToList"
  />

  <!-- 显示结果列表 -->
  <div v-else class="result-panel">
    <!-- 结果头部 -->
    <ResultHeader
      :record="record"
      :is-exporting="isExporting"
      :activeTab="activeTab"
      @export="handleExport"
      @download="handleDownloadVideo"
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
  padding: 2rem;
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
