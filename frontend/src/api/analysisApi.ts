import axios, { type AxiosProgressEvent } from 'axios'
import type {
  AnalysisRecord,
  CellData,
  ProcessResult,
} from '@/stores/analysisStore'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加 token 等认证信息
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // 统一错误处理
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// 上传进度回调类型
export type UploadProgressCallback = (progressEvent: AxiosProgressEvent) => void

/**
 * 分析 API 服务
 * 符合需求文档 7.1 节 API 接口设计
 */
export const analysisApi = {
  /**
   * 上传视频文件
   * POST /api/upload
   * @param file 视频文件
   * @param onProgress 上传进度回调
   * @returns AnalysisRecord
   */
  async upload(
    file: File,
    onProgress?: UploadProgressCallback
  ): Promise<AnalysisRecord> {
    const formData = new FormData()
    formData.append('video', file)

    const { data } = await api.post<AnalysisRecord>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: onProgress,
    })

    return data
  },

  /**
   * 启动处理任务
   * POST /api/process
   * @param taskId 任务ID
   * @param params 可选的模型参数
   * @returns 任务信息
   */
  async startProcess(
    taskId: string,
    params?: Record<string, any>
  ): Promise<{ task_id: string; status: string }> {
    const { data } = await api.post('/process', {
      task_id: taskId,
      params,
    })

    return data
  },

  /**
   * 查询任务状态
   * GET /api/status/:task_id
   * @param taskId 任务ID
   * @returns 任务状态和进度
   */
  async getStatus(taskId: string): Promise<{
    status: string
    progress: number
    current_frame?: number
    total_frames?: number
  }> {
    const { data } = await api.get(`/status/${taskId}`)
    return data
  },

  /**
   * 获取处理结果
   * GET /api/result/:task_id
   * @param taskId 任务ID
   * @returns 处理结果（包含完整的细胞数据）
   */
  async getResult(taskId: string): Promise<ProcessResult> {
    const { data } = await api.get<ProcessResult>(`/result/${taskId}`)
    return data
  },

  /**
   * 获取细胞数据列表
   * GET /api/cells/:task_id
   * @param taskId 任务ID
   * @returns 细胞数据数组
   */
  async getCells(taskId: string): Promise<CellData[]> {
    const { data } = await api.get<CellData[]>(`/cells/${taskId}`)
    return data
  },

  /**
   * 获取单个细胞数据
   * GET /api/cell/:task_id/:cell_id
   * @param taskId 任务ID
   * @param cellId 细胞ID
   * @returns 单个细胞的完整数据
   */
  async getCell(taskId: string, cellId: string): Promise<CellData> {
    const { data } = await api.get<CellData>(`/cell/${taskId}/${cellId}`)
    return data
  },

  /**
   * 导出数据
   * GET /api/export/:task_id
   * @param taskId 任务ID
   * @param format 导出格式（csv 或 json）
   * @returns Blob 数据
   */
  async exportData(
    taskId: string,
    format: 'csv' | 'json' = 'csv'
  ): Promise<Blob> {
    const { data } = await api.get(`/export/${taskId}`, {
      params: { format },
      responseType: 'blob',
    })

    return data
  },

  /**
   * 获取标注视频 URL
   * GET /api/video/:task_id
   * @param taskId 任务ID
   * @returns 视频 URL
   */
  getVideoUrl(taskId: string): string {
    return `${api.defaults.baseURL}/video/${taskId}`
  },

  /**
   * 下载标注视频
   * @param taskId 任务ID
   * @returns Blob 数据
   */
  async downloadVideo(taskId: string): Promise<Blob> {
    const { data } = await api.get(`/video/${taskId}`, {
      responseType: 'blob',
    })

    return data
  },
}

/**
 * WebSocket 连接管理器
 * 用于实时接收处理进度更新
 */
export class AnalysisWebSocket {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor(private url: string = 'ws://localhost:8000/ws') {}

  /**
   * 连接 WebSocket
   */
  connect(
    onMessage: (event: MessageEvent) => void,
    onError?: (event: Event) => void,
    onClose?: (event: CloseEvent) => void
  ): void {
    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = onMessage

      this.ws.onerror = (event) => {
        console.error('WebSocket error:', event)
        onError?.(event)
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', event)
        onClose?.(event)

        // 自动重连
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          console.log(
            `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
          )
          setTimeout(() => {
            this.connect(onMessage, onError, onClose)
          }, this.reconnectDelay * this.reconnectAttempts)
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
    }
  }

  /**
   * 发送消息
   */
  send(message: string | object): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const data = typeof message === 'string' ? message : JSON.stringify(message)
      this.ws.send(data)
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  /**
   * 订阅任务进度
   */
  subscribeTask(taskId: string): void {
    this.send({
      type: 'subscribe',
      task_id: taskId,
    })
  }

  /**
   * 取消订阅任务
   */
  unsubscribeTask(taskId: string): void {
    this.send({
      type: 'unsubscribe',
      task_id: taskId,
    })
  }

  /**
   * 关闭连接
   */
  close(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  /**
   * 检查连接状态
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}

/**
 * WebSocket 消息类型
 */
export interface WSMessage {
  type: 'progress' | 'status' | 'error' | 'complete'
  task_id: string
  data: {
    progress?: number
    status?: string
    current_frame?: number
    total_frames?: number
    message?: string
    error?: string
  }
}

export default api
