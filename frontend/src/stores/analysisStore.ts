import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

export type AnalysisStatus = 'uploading' | 'processing' | 'completed' | 'failed'

// 位置信息
export interface Position {
  x: number
  y: number
}

// 速度信息
export interface Velocity {
  vx: number // X方向速度分量
  vy: number // Y方向速度分量
  speed: number // 速度大小
}

// 边界框信息
export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
}

// 单帧细胞数据
export interface CellFrameData {
  frame_number: number // 帧号
  position: Position // 中心位置
  area: number // 细胞面积
  velocity: Velocity // 速度向量
  bounding_box: BoundingBox // 边界框
}

// 细胞完整数据（符合需求文档 6.3.1）
export interface CellData {
  cell_id: string // 细胞ID
  first_frame: number // 首次出现帧号
  last_frame: number // 最后出现帧号
  frame_count: number // 存活帧数
  avg_width: number // 平均宽度
  avg_height: number // 平均高度
  avg_conf: number // 平均置信度
  avg_velocity: number // 平均速度
  frames: CellFrameData[] // 每一帧的数据
}

// 处理结果数据
export interface ProcessResult {
  output_video_path: string // 标注视频路径
  cell_count: number // 细胞总数
  total_frames: number // 总帧数
  video_duration: number // 视频时长（秒）
  model_name: string // 使用的模型名称
  cells: CellData[] // 细胞列表数据
}

// 分析记录（符合需求文档 6.3.2）
export interface AnalysisRecord {
  task_id: string // 任务ID
  task_name?: string // 任务名称（用户自定义）
  video_name: string // 视频文件名
  video_path: string // 原始视频路径
  status: AnalysisStatus // 任务状态
  progress: number // 处理进度 (0-100)
  start_time: Date // 开始时间
  end_time?: Date // 结束时间
  result?: ProcessResult // 处理结果
  model_name?: string // 模型名称（来自数据库，不是result.json）
  // 进度详情字段
  stage?: string // 当前阶段
  message?: string // 详细消息
  currentFrame?: number // 当前帧数
  totalFrames?: number // 总帧数
}

export const useAnalysisStore = defineStore('analysis', () => {
  // 所有分析记录
  const records = ref<AnalysisRecord[]>([])

  // 当前选中的分析记录ID
  const selectedId = ref<string | null>(null)

  // 排序条件
  const sortConditions = ref<Array<{ id: string; field: string; direction: string }>>([
    {
      id: '1',
      field: 'createdAt',
      direction: 'desc'
    }
  ])

  // 当前选中的记录
  const selectedRecord = computed(() => {
    if (!selectedId.value) return null
    return records.value.find((r) => r.task_id === selectedId.value) || null
  })

  // 是否显示上传面板（创建新分析）
  const showUploadPanel = ref(false)

  // 当前选中的细胞ID（用于显示细胞详情）
  const selectedCellId = ref<string | null>(null)

  // 当前选中的细胞数据
  const selectedCellData = computed(() => {
    if (!selectedCellId.value || !selectedRecord.value?.result?.cells) {
      return null
    }
    return (
      selectedRecord.value.result.cells.find((cell) => cell.cell_id === selectedCellId.value) ||
      null
    )
  })

  
  // 对比模式相关状态
  const compareRecords = ref<AnalysisRecord[]>([])

  // 选择记录
  function selectRecord(id: string) {
    selectedId.value = id
    showUploadPanel.value = false
    selectedCellId.value = null // 重置细胞选择
  }

  // 设置排序条件
  function setSortConditions(conditions: Array<{ id: string; field: string; direction: string }>) {
    sortConditions.value = conditions
  }

  // 清除选中状态
  function clearSelection() {
    selectedId.value = null
    selectedCellId.value = null
  }

  // 创建新分析
  function createNewAnalysis() {
    selectedId.value = null
    showUploadPanel.value = true
    selectedCellId.value = null
  }

  // 选择细胞（显示细胞详情）
  function selectCell(cellId: string) {
    selectedCellId.value = cellId
  }

  // 返回结果列表（关闭细胞详情）
  function backToResultList() {
    selectedCellId.value = null
  }

  // 跳转到对比结果页面
  function goToCompareResult(recordA: AnalysisRecord | undefined, recordB: AnalysisRecord | undefined, router: any) {
    if (!recordA || !recordB) {
      console.error('缺少对比记录')
      return
    }
    compareRecords.value = [recordA, recordB]
    router.push({ name: 'compareResult' })
  }

  // 返回对比列表
  function backToCompareList(router: any) {
    compareRecords.value = []
    router.push({ name: 'compare' })
  }

  // 加载历史任务
  async function loadHistoryTasks() {
    try {
      // 从 userStore 获取当前登录用户
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

      // 转换后端数据为前端格式
      const convertedRecords: AnalysisRecord[] = historyTasks.map((task: any) => {
        // 从数据库获取的模型名（最新）
        const modelNameFromDB = task.model_display_name || ''
        // 获取任务名称（用户自定义的名称）
        const taskNameFromDB = task.task_name || null

        // 根据任务状态决定转换方式
        if (task.status === 'processing') {
          // 处理中的任务
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
          // 已完成的任务
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

      // 只显示历史任务
      records.value = convertedRecords
    } catch (error) {
      console.error('加载历史任务失败:', error)
      // 加载失败时显示空列表
      records.value = []
    }
  }

  // 添加新记录（模拟上传）
  function addRecord(videoName: string, _videoFile: File) {
    // videoFile 参数保留用于后续实现真实上传功能
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
    showUploadPanel.value = false

    // 模拟处理进度更新
    const progressInterval = setInterval(() => {
      const record = records.value.find((r) => r.task_id === taskId)
      if (record && record.progress < 100) {
        record.progress += 10
      }
    }, 300)

    // 模拟处理过程（3秒后完成）
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
          video_duration: totalFrames / 30, // 假设 30fps
          model_name: 'best_split.pt', // 模拟数据使用默认模型
          cells: [], // 空数组，实际数据由后端提供
        }
      }
    }, 3000)
  }

  // 添加上传后的记录（用于 API 集成）
  function addUploadedRecord(record: AnalysisRecord) {
    records.value.unshift(record)
    selectedId.value = record.task_id
    showUploadPanel.value = false
  }

  // 更新任务状态（用于 API 集成）
  function updateTaskStatus(
    taskId: string,
    updates: {
      status?: AnalysisStatus
      progress?: number
    }
  ) {
    const record = records.value.find((r) => r.task_id === taskId)
    if (record) {
      if (updates.status !== undefined) {
        record.status = updates.status
      }
      if (updates.progress !== undefined) {
        record.progress = updates.progress
      }
      if (updates.status === 'completed') {
        record.end_time = new Date()
      }
    }
  }

  // 更新任务结果（用于 API 集成）
  function updateTaskResult(taskId: string, result: ProcessResult) {
    const record = records.value.find((r) => r.task_id === taskId)
    if (record) {
      record.result = result
      record.status = 'completed'
      record.progress = 100
      record.end_time = new Date()
    }
  }

  // 删除记录
  async function deleteRecord(taskId: string) {
    try {
      // 调用后端 API 删除任务
      await axios.delete(`/api/delete/${taskId}/`)

      // 从前端列表中移除记录
      const index = records.value.findIndex((r) => r.task_id === taskId)
      if (index !== -1) {
        records.value.splice(index, 1)
      }

      // 如果删除的是当前选中的记录，清空选中状态
      if (selectedId.value === taskId) {
        selectedId.value = null
      }

      return true
    } catch (error: any) {
      console.error('删除记录失败:', error)
      throw new Error(error.response?.data?.error || '删除失败')
    }
  }

  // 添加处理中的任务记录
  function addProcessingRecord(record: AnalysisRecord) {
    records.value.unshift(record)
  }

  // 更新任务进度详情
  function updateTaskProgress(
    taskId: string,
    updates: {
      progress?: number
      stage?: string
      message?: string
      currentFrame?: number
      totalFrames?: number
    }
  ) {
    const record = records.value.find((r) => r.task_id === taskId)
    if (record) {
      if (updates.progress !== undefined) {
        record.progress = updates.progress
      }
      if (updates.stage !== undefined) {
        record.stage = updates.stage
      }
      if (updates.message !== undefined) {
        record.message = updates.message
      }
      if (updates.currentFrame !== undefined) {
        record.currentFrame = updates.currentFrame
      }
      if (updates.totalFrames !== undefined) {
        record.totalFrames = updates.totalFrames
      }
    }
  }

  // 全局轮询控制
  let pollIntervalId: number | null = null

  // 启动全局轮询
  function startGlobalPolling() {
    if (pollIntervalId !== null) {
      return // 已经在轮询中
    }

    pollIntervalId = window.setInterval(async () => {
      // 查找所有处理中的任务
      const processingTasks = records.value.filter((r) => r.status === 'processing')

      if (processingTasks.length === 0) {
        return // 没有处理中的任务，跳过
      }

      // 并发轮询所有处理中的任务
      const pollPromises = processingTasks.map(async (task) => {
        try {
          const response = await axios.get(`/api/status/${task.task_id}/`)
          const data = response.data

          // 更新任务进度
          updateTaskProgress(task.task_id, {
            progress: data.progress || 0,
            stage: data.stage || '',
            message: data.message || '',
            currentFrame: data.current_frame || null,
            totalFrames: data.total_frames || null,
          })

          // 如果任务完成，更新状态
          if (data.status === 'completed') {
            updateTaskStatus(task.task_id, { status: 'completed', progress: 100 })

            // 获取完整结果
            const resultResponse = await axios.get(`/api/result/${task.task_id}/`)
            const result = resultResponse.data

            // 更新结果数据
            const record = records.value.find((r) => r.task_id === task.task_id)
            if (record) {
              // 更新原始视频路径（如果后端返回了）
              if (result.original_video_path) {
                record.video_path = result.original_video_path
              }
              // 更新结果数据
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
    }, 2000) // 每2秒轮询一次
  }

  // 停止全局轮询
  function stopGlobalPolling() {
    if (pollIntervalId !== null) {
      clearInterval(pollIntervalId)
      pollIntervalId = null
    }
  }

  // 初始化时启动全局轮询
  startGlobalPolling()

  return {
    records,
    selectedId,
    selectedRecord,
    showUploadPanel,
    selectedCellId,
    selectedCellData,
    compareRecords,
    sortConditions,
    selectRecord,
    clearSelection,
    createNewAnalysis,
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
  }
})
