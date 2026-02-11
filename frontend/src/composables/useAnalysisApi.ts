import { ref } from 'vue'
import { analysisApi, AnalysisWebSocket, type WSMessage } from '@/api/analysis'
import { useAnalysisStore } from '@/stores/analysisStore'
import type { AnalysisRecord } from '@/stores/analysisStore'

/**
 * 分析 API 组合式函数
 * 提供便捷的 API 调用方法和状态管理
 */
export function useAnalysisApi() {
  const store = useAnalysisStore()
  const uploadProgress = ref(0)
  const isUploading = ref(false)
  const uploadError = ref<string | null>(null)

  // WebSocket 实例
  let ws: AnalysisWebSocket | null = null

  /**
   * 上传视频并启动分析
   */
  async function uploadAndAnalyze(file: File): Promise<AnalysisRecord | null> {
    try {
      isUploading.value = true
      uploadProgress.value = 0
      uploadError.value = null

      // 上传视频
      const record = await analysisApi.upload(file, (progressEvent) => {
        if (progressEvent.total) {
          uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        }
      })

      // 添加到 store
      store.addUploadedRecord(record)

      // 启动处理
      await analysisApi.startProcess(record.task_id)

      // 开始监听进度
      startProgressMonitoring(record.task_id)

      return record
    } catch (error: any) {
      uploadError.value = error.message || '上传失败'
      console.error('Upload error:', error)
      return null
    } finally {
      isUploading.value = false
    }
  }

  /**
   * 开始监听任务进度（轮询方式）
   */
  function startProgressMonitoring(taskId: string) {
    const pollInterval = setInterval(async () => {
      try {
        const statusData = await analysisApi.getStatus(taskId)

        // 更新 store 中的任务状态
        store.updateTaskStatus(taskId, {
          status: statusData.status as any,
          progress: statusData.progress,
        })

        // 如果任务完成，停止轮询并获取结果
        if (statusData.status === 'completed') {
          clearInterval(pollInterval)
          await fetchTaskResult(taskId)
        } else if (statusData.status === 'failed') {
          clearInterval(pollInterval)
        }
      } catch (error) {
        console.error('Failed to poll status:', error)
        clearInterval(pollInterval)
      }
    }, 2000) // 每2秒轮询一次

    // 保存 interval ID 以便后续清理
    return pollInterval
  }

  /**
   * 获取任务结果
   */
  async function fetchTaskResult(taskId: string) {
    try {
      const result = await analysisApi.getResult(taskId)
      store.updateTaskResult(taskId, result)
    } catch (error) {
      console.error('Failed to fetch result:', error)
    }
  }

  /**
   * 连接 WebSocket 接收实时更新
   */
  function connectWebSocket() {
    ws = new AnalysisWebSocket()

    ws.connect(
      (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data)

          switch (message.type) {
            case 'progress':
              // 更新进度
              store.updateTaskStatus(message.task_id, {
                progress: message.data.progress || 0,
              })
              break

            case 'status':
              // 更新状态
              store.updateTaskStatus(message.task_id, {
                status: message.data.status as any,
                progress: message.data.progress || 0,
              })
              break

            case 'complete':
              // 任务完成，获取结果
              fetchTaskResult(message.task_id)
              break

            case 'error':
              // 处理错误
              store.updateTaskStatus(message.task_id, {
                status: 'failed',
              })
              console.error('Task error:', message.data.error)
              break
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      },
      (error) => {
        console.error('WebSocket error:', error)
      },
      (event) => {
        console.log('WebSocket closed:', event)
      }
    )
  }

  /**
   * 订阅任务进度更新
   */
  function subscribeTask(taskId: string) {
    if (ws && ws.isConnected()) {
      ws.subscribeTask(taskId)
    }
  }

  /**
   * 取消订阅任务
   */
  function unsubscribeTask(taskId: string) {
    if (ws && ws.isConnected()) {
      ws.unsubscribeTask(taskId)
    }
  }

  /**
   * 导出数据
   */
  async function exportData(taskId: string, format: 'csv' | 'json' = 'csv') {
    try {
      const blob = await analysisApi.exportData(taskId, format)

      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `analysis_${taskId}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to export data:', error)
      throw error
    }
  }

  /**
   * 下载标注视频
   */
  async function downloadVideo(taskId: string, videoName: string) {
    try {
      const blob = await analysisApi.downloadVideo(taskId)

      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${videoName}_annotated.mp4`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Failed to download video:', error)
      throw error
    }
  }

  /**
   * 获取单个细胞数据
   */
  async function fetchCellData(taskId: string, cellId: string) {
    try {
      return await analysisApi.getCell(taskId, cellId)
    } catch (error) {
      console.error('Failed to fetch cell data:', error)
      throw error
    }
  }

  /**
   * 清理资源
   */
  function cleanup() {
    if (ws) {
      ws.close()
      ws = null
    }
  }

  return {
    // 状态
    uploadProgress,
    isUploading,
    uploadError,

    // 方法
    uploadAndAnalyze,
    startProgressMonitoring,
    fetchTaskResult,
    connectWebSocket,
    subscribeTask,
    unsubscribeTask,
    exportData,
    downloadVideo,
    fetchCellData,
    cleanup,
  }
}
