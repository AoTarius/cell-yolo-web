# API 集成指南

本文档说明如何在前端中使用后端 API 接口。

## 📁 文件结构

```
src/
├── api/
│   └── analysis.ts          # API 服务封装
├── composables/
│   └── useAnalysisApi.ts    # API 使用的组合式函数
└── stores/
    └── analysisStore.ts     # 状态管理（已集成 API 支持）
```

## 🔌 API 端点（符合需求文档 7.1 节）

### 1. 上传视频
```typescript
POST /api/upload
Content-Type: multipart/form-data

// 请求
FormData {
  video: File
}

// 响应
{
  task_id: string
  video_name: string
  video_path: string
  status: 'uploading' | 'processing'
  progress: 0
  start_time: Date
}
```

### 2. 启动处理任务
```typescript
POST /api/process

// 请求
{
  task_id: string
  params?: {
    // 可选的模型参数
    confidence_threshold?: number
    iou_threshold?: number
    ...
  }
}

// 响应
{
  task_id: string
  status: string
}
```

### 3. 查询任务状态
```typescript
GET /api/status/:task_id

// 响应
{
  status: 'processing' | 'completed' | 'failed'
  progress: number (0-100)
  current_frame?: number
  total_frames?: number
}
```

### 4. 获取处理结果
```typescript
GET /api/result/:task_id

// 响应
{
  output_video_path: string
  cell_count: number
  total_frames: number
  cells: CellData[]
}
```

### 5. 获取细胞数据列表
```typescript
GET /api/cells/:task_id

// 响应
CellData[]
```

### 6. 获取单个细胞数据
```typescript
GET /api/cell/:task_id/:cell_id

// 响应
{
  cell_id: string
  frames: [
    {
      frame_number: number
      position: { x: number, y: number }
      area: number
      velocity: { vx: number, vy: number, speed: number }
      bounding_box: { x: number, y: number, width: number, height: number }
    }
  ]
}
```

### 7. 导出数据
```typescript
GET /api/export/:task_id?format=csv|json

// 响应
Blob (CSV 或 JSON 文件)
```

### 8. 获取标注视频
```typescript
GET /api/video/:task_id

// 响应
Video file stream
```

## 🔧 使用方法

### 方式一：直接使用 API 服务

```typescript
import { analysisApi } from '@/api/analysis'

// 上传视频
const record = await analysisApi.upload(file, (progressEvent) => {
  const progress = (progressEvent.loaded / progressEvent.total) * 100
  console.log(`上传进度: ${progress}%`)
})

// 启动处理
await analysisApi.startProcess(record.task_id)

// 轮询状态
const statusInterval = setInterval(async () => {
  const status = await analysisApi.getStatus(record.task_id)

  if (status.status === 'completed') {
    clearInterval(statusInterval)
    const result = await analysisApi.getResult(record.task_id)
    console.log('处理完成:', result)
  }
}, 2000)
```

### 方式二：使用 Composable（推荐）

```typescript
import { useAnalysisApi } from '@/composables/useAnalysisApi'

const api = useAnalysisApi()

// 上传并分析（自动处理所有流程）
const record = await api.uploadAndAnalyze(file)

// 监听上传进度
watch(api.uploadProgress, (progress) => {
  console.log(`上传进度: ${progress}%`)
})

// 导出数据
await api.exportData(taskId, 'csv')

// 下载视频
await api.downloadVideo(taskId, videoName)
```

### 方式三：在组件中使用

```vue
<script setup lang="ts">
import { useAnalysisApi } from '@/composables/useAnalysisApi'

const api = useAnalysisApi()

async function handleUpload(file: File) {
  const record = await api.uploadAndAnalyze(file)

  if (record) {
    console.log('上传成功，任务ID:', record.task_id)
  } else {
    console.error('上传失败:', api.uploadError.value)
  }
}
</script>

<template>
  <div>
    <input type="file" @change="handleUpload($event.target.files[0])" />
    <div v-if="api.isUploading.value">
      上传进度: {{ api.uploadProgress.value }}%
    </div>
    <div v-if="api.uploadError.value" class="error">
      {{ api.uploadError.value }}
    </div>
  </div>
</template>
```

## 📡 WebSocket 实时更新

### 连接 WebSocket

```typescript
import { AnalysisWebSocket } from '@/api/analysis'

const ws = new AnalysisWebSocket('ws://localhost:8000/ws')

ws.connect(
  (event) => {
    const message = JSON.parse(event.data)
    console.log('收到消息:', message)

    // 处理不同类型的消息
    switch (message.type) {
      case 'progress':
        console.log(`进度: ${message.data.progress}%`)
        break
      case 'complete':
        console.log('任务完成')
        break
      case 'error':
        console.error('任务失败:', message.data.error)
        break
    }
  },
  (error) => console.error('WebSocket 错误:', error),
  (event) => console.log('WebSocket 关闭:', event)
)

// 订阅任务进度
ws.subscribeTask(taskId)

// 取消订阅
ws.unsubscribeTask(taskId)

// 关闭连接
ws.close()
```

### WebSocket 消息格式

```typescript
// 进度更新
{
  type: 'progress'
  task_id: string
  data: {
    progress: number
    current_frame?: number
    total_frames?: number
  }
}

// 状态变更
{
  type: 'status'
  task_id: string
  data: {
    status: 'processing' | 'completed' | 'failed'
    progress: number
  }
}

// 任务完成
{
  type: 'complete'
  task_id: string
  data: {
    message: string
  }
}

// 错误通知
{
  type: 'error'
  task_id: string
  data: {
    error: string
    message: string
  }
}
```

## 🔄 从模拟数据切换到真实 API

### 当前状态（使用模拟数据）

```typescript
// src/components/UploadPanel.vue
async function submitUpload() {
  if (selectedFile.value) {
    // 目前使用模拟数据
    store.addRecord(selectedFile.value.name, selectedFile.value)
    selectedFile.value = null
  }
}
```

### 切换到真实 API

```typescript
// src/components/UploadPanel.vue
async function submitUpload() {
  if (selectedFile.value) {
    // 使用真实 API（取消注释）
    const result = await api.uploadAndAnalyze(selectedFile.value)

    if (result) {
      selectedFile.value = null
    }
  }
}
```

## ⚙️ 配置

### 修改 API 基础 URL

```typescript
// src/api/analysis.ts
const api = axios.create({
  baseURL: '/api',  // 开发环境
  // baseURL: 'http://your-backend-server.com/api',  // 生产环境
  timeout: 30000,
})
```

### 配置代理（开发环境）

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
```

## 🧪 测试 API 集成

### 1. 测试上传

```bash
# 使用 curl 测试上传端点
curl -X POST http://localhost:8000/api/upload \
  -F "video=@test_video.mp4"
```

### 2. 测试状态查询

```bash
curl http://localhost:8000/api/status/task_001
```

### 3. 测试结果获取

```bash
curl http://localhost:8000/api/result/task_001
```

## 📝 注意事项

1. **错误处理**: 所有 API 调用都应该包含错误处理
2. **超时设置**: 上传大文件时可能需要增加超时时间
3. **进度监听**: 使用 WebSocket 比轮询更高效
4. **资源清理**: 组件卸载时记得关闭 WebSocket 连接
5. **类型安全**: 使用 TypeScript 类型确保数据结构正确

## 🔗 相关文档

- [DEVELOPMENT.md](./DEVELOPMENT.md) - 前端开发文档
- [软件需求分析文档](../软件需求分析文档_v1.md) - 完整需求文档
- [QUICK-START.md](../QUICK-START.md) - 快速启动指南
