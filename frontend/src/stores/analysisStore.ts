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
  frames: CellFrameData[] // 每一帧的数据
}

// 处理结果数据
export interface ProcessResult {
  output_video_path: string // 标注视频路径
  cell_count: number // 细胞总数
  total_frames: number // 总帧数
  video_duration: number // 视频时长（秒）
  cells: CellData[] // 细胞列表数据
}

// 分析记录（符合需求文档 6.3.2）
export interface AnalysisRecord {
  task_id: string // 任务ID
  video_name: string // 视频文件名
  video_path: string // 原始视频路径
  status: AnalysisStatus // 任务状态
  progress: number // 处理进度 (0-100)
  start_time: Date // 开始时间
  end_time?: Date // 结束时间
  result?: ProcessResult // 处理结果
}

export const useAnalysisStore = defineStore('analysis', () => {
  // 生成模拟细胞数据的辅助函数（符合新数据结构）
  function generateMockCells(count: number, totalFrames: number): CellData[] {
    return Array.from({ length: count }, (_, i) => {
      const firstFrame = Math.floor(Math.random() * 20)
      const lastFrame = totalFrames - Math.floor(Math.random() * 20)
      const framesToGenerate = Math.min(lastFrame - firstFrame, 50) // 限制生成帧数

      // 使用 for 循环生成每一帧的数据（避免闭包问题）
      const frames: CellFrameData[] = []
      let prevX = Math.random() * 500
      let prevY = Math.random() * 500

      for (let j = 0; j < framesToGenerate; j++) {
        const frameNumber = firstFrame + Math.floor((j * (lastFrame - firstFrame)) / framesToGenerate)

        // 生成新位置（在前一帧基础上略微移动）
        const dx = (Math.random() - 0.5) * 10
        const dy = (Math.random() - 0.5) * 10
        const x = prevX + dx
        const y = prevY + dy

        frames.push({
          frame_number: frameNumber,
          position: { x, y },
          area: Math.random() * 200 + 100, // 100-300 平方像素
          velocity: {
            vx: dx,
            vy: dy,
            speed: Math.sqrt(dx * dx + dy * dy),
          },
          bounding_box: {
            x: x - 10,
            y: y - 10,
            width: 20 + Math.random() * 10,
            height: 20 + Math.random() * 10,
          },
        })

        // 更新前一帧位置
        prevX = x
        prevY = y
      }

      return {
        cell_id: `Cell #${i + 1}`,
        frames,
      }
    })
  }

  // 预制记录（示例数据）
  const PRESET_RECORDS: AnalysisRecord[] = [
    {
      task_id: 'demo_001',
      video_name: 'sample_video_1.mp4',
      video_path: '/uploads/sample_video_1.mp4',
      status: 'completed',
      progress: 100,
      start_time: new Date('2024-02-10 10:00:00'),
      end_time: new Date('2024-02-10 10:05:30'),
      result: {
        output_video_path: '/outputs/sample_video_1_annotated.mp4',
        cell_count: 25,
        total_frames: 120,
        video_duration: 4.0, // 120帧 / 30fps
        cells: generateMockCells(25, 120),
      },
    },
    {
      task_id: 'demo_002',
      video_name: 'sample_video_2.mp4',
      video_path: '/uploads/sample_video_2.mp4',
      status: 'completed',
      progress: 100,
      start_time: new Date('2024-02-10 14:30:00'),
      end_time: new Date('2024-02-10 14:38:20'),
      result: {
        output_video_path: '/outputs/sample_video_2_annotated.mp4',
        cell_count: 18,
        total_frames: 200,
        video_duration: 6.67, // 200帧 / 30fps
        cells: generateMockCells(18, 200),
      },
    },
  ]

  // 所有分析记录
  const records = ref<AnalysisRecord[]>([])

  // 当前选中的分析记录ID
  const selectedId = ref<string | null>(null)

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

  // 选择记录
  function selectRecord(id: string) {
    selectedId.value = id
    showUploadPanel.value = false
    selectedCellId.value = null // 重置细胞选择
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

  // 加载历史任务
  async function loadHistoryTasks() {
    try {
      const response = await axios.get('/api/tasks/')
      const historyTasks = response.data.tasks || []

      // 转换后端数据为前端格式
      const convertedRecords: AnalysisRecord[] = historyTasks.map((task: any) => {
        // 确保 result 对象存在且格式正确
        const result: ProcessResult = {
          output_video_path: task.annotated_video_path || '',
          cell_count: task.cell_count || 0,
          total_frames: task.total_frames || 0,
          video_duration: task.video_duration || 0,
          cells: [], // 从 summary 解析细胞数据
        }

        // 如果有 summary，尝试解析细胞数据
        if (task.summary && typeof task.summary === 'object') {
          // summary 可能包含细胞统计信息
        }

        return {
          task_id: task.task_id,
          video_name: task.original_video_path.split('/').pop() || 'Unknown',
          video_path: task.original_video_path,
          status: 'completed' as AnalysisStatus,
          progress: 100,
          start_time: new Date(task.created_at),
          end_time: new Date(),
          result,
        }
      })

      // 合并历史任务和预制记录（历史任务在前）
      records.value = [...convertedRecords, ...PRESET_RECORDS]
    } catch (error) {
      console.error('加载历史任务失败:', error)
      // 加载失败时只显示预制记录
      records.value = PRESET_RECORDS
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
          cells: generateMockCells(cellCount, totalFrames),
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

  return {
    records,
    selectedId,
    selectedRecord,
    showUploadPanel,
    selectedCellId,
    selectedCellData,
    selectRecord,
    createNewAnalysis,
    addRecord,
    selectCell,
    backToResultList,
    addUploadedRecord,
    updateTaskStatus,
    updateTaskResult,
    loadHistoryTasks,
  }
})
