# CellTrack 前端开发文档

## 项目概述

CellTrack 前端是基于 Vue 3 + TypeScript + Vite 构建的现代化 SPA 应用，用于细胞追踪分析的可视化展示。

## 技术栈

- **Vue 3.5.27** - Composition API
- **TypeScript 5.9.3** - 类型安全
- **Vite 7.3.1** - 构建工具
- **TailwindCSS 4.1.18** - 样式框架
- **Pinia 3.0.4** - 状态管理
- **Vue Router 5.0.1** - 路由管理
- **Axios 1.13.5** - HTTP 客户端

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API 服务层
│   │   └── analysisApi.ts        # 分析 API 封装
│   ├── assets/           # 静态资源
│   │   └── main.css      # 全局样式 (TailwindCSS)
│   ├── components/       # 组件
│   │   ├── analysis/     # 分析结果组件
│   │   │   ├── AnalysisResult.vue  # 分析结果主组件
│   │   │   ├── ResultHeader.vue    # 结果头部（含视图切换）
│   │   │   ├── VideoPlayer.vue     # 视频播放器（双视频+控制）
│   │   │   ├── CellPopulationChart.vue  # 细胞群体图表
│   │   │   ├── CellDetailList.vue  # 细胞详情列表
│   │   │   └── CellDetailPanel.vue # 细胞详情面板
│   │   ├── common/       # 通用组件
│   │   │   └── Sidebar.vue         # 侧边栏（历史记录列表）
│   │   ├── upload/       # 上传组件
│   │   │   └── UploadPanel.vue     # 上传视频面板
│   │   └── progress/     # 进度组件
│   │       └── ProgressView.vue    # 进度展示
│   ├── composables/      # 组合式函数
│   │   ├── useAnalysisApi.ts     # API 使用的组合式函数
│   │   └── useToast.ts          # Toast 提示组合式函数
│   ├── router/           # 路由配置
│   │   └── index.ts
│   ├── stores/           # Pinia 状态管理
│   │   ├── analysisStore.ts      # 分析记录状态
│   │   └── counter.ts            # 示例计数器（可删除）
│   ├── views/            # 页面视图
│   │   ├── CellTrackingView.vue  # 主页面
│   │   ├── ModelUploadView.vue    # 模型上传视图
│   │   └── ProgressView.vue       # 进度视图
│   ├── App.vue           # 根组件
│   └── main.ts           # 入口文件
├── public/               # 公共静态文件
├── vite.config.ts        # Vite 配置
├── tsconfig.json         # TypeScript 配置
└── package.json          # 依赖配置
```

## 核心功能模块

### 1. 状态管理 (analysisStore.ts)

使用 Pinia 管理全局状态，包括分析记录、细胞数据等。

#### 数据结构（符合需求文档 6.3节）

```typescript
// 分析记录（处理任务）
interface AnalysisRecord {
  task_id: string              // 任务ID
  video_name: string           // 视频文件名
  video_path: string           // 原始视频路径
  status: AnalysisStatus       // 状态：uploading | processing | completed | failed
  progress: number             // 处理进度 (0-100)
  start_time: Date             // 开始时间
  end_time?: Date              // 结束时间
  result?: ProcessResult       // 处理结果
}

// 处理结果
interface ProcessResult {
  output_video_path: string    // 标注视频路径
  cell_count: number           // 细胞总数
  total_frames: number         // 总帧数
  cells: CellData[]            // 细胞列表
}

// 细胞数据
interface CellData {
  cell_id: string              // 细胞ID (如 "Cell #1")
  frames: CellFrameData[]      // 每一帧的数据数组
}

// 单帧细胞数据
interface CellFrameData {
  frame_number: number         // 帧号
  position: Position           // 中心位置
  area: number                 // 细胞面积 (平方像素)
  velocity: Velocity           // 速度向量
  bounding_box: BoundingBox    // 边界框
}

// 位置信息
interface Position {
  x: number                    // X 坐标
  y: number                    // Y 坐标
}

// 速度信息
interface Velocity {
  vx: number                   // X方向速度分量
  vy: number                   // Y方向速度分量
  speed: number                // 速度大小
}

// 边界框信息
interface BoundingBox {
  x: number                    // 左上角X坐标
  y: number                    // 左上角Y坐标
  width: number                // 宽度
  height: number               // 高度
}
```

#### 核心状态

- `records` - 所有分析记录列表
- `selectedId` - 当前选中的记录ID
- `selectedRecord` - 当前选中的记录对象 (computed)
- `selectedCellId` - 当前选中的细胞ID
- `selectedCellData` - 当前选中的细胞数据对象 (computed)
- `showUploadPanel` - 是否显示上传面板

#### 核心方法

- `selectRecord(id)` - 选择分析记录
- `createNewAnalysis()` - 创建新分析
- `addRecord(videoName, videoFile)` - 添加新记录
- `selectCell(cellId)` - 选择细胞并显示详情
- `backToResultList()` - 返回结果列表

### 2. 视频播放器功能

VideoPlayer.vue 组件提供强大的视频播放和控制功能。

#### 核心功能

**双视频对比播放**:
- 原始视频播放器
- 标注视频播放器
- 支持同时播放/暂停
- 支持同步帧控制

**布局切换**:
- 并排布局（side-by-side）：左右并排显示两个视频
- 上下布局（stacked）：上下堆叠显示两个视频

**播放控制**:
- 播放/暂停：控制视频播放状态
- 前进/后退一帧：精确控制视频播放位置
- 回到开头并暂停：重置视频到开始位置
- 播放速率调整：支持 0.25x, 0.5x, 0.75x, 1x, 1.5x, 2x 速率

**智能帧率计算**:
```typescript
function getVideoFps(): number {
  const totalFrames = props.record.result?.total_frames || 0
  const duration = props.record.result?.video_duration || 0
  if (duration > 0 && totalFrames > 0) {
    return totalFrames / duration
  }
  return 30 // 默认帧率
}
```

#### 状态管理

- `currentPlaybackRate` - 当前播放速率（默认 1x）
- `showRateMenu` - 速率菜单显示状态
- `videoLayoutMode` - 视频布局模式（side-by-side / stacked）

#### 事件处理

- `videoError` - 视频加载错误时触发

#### API 集成

- 原始视频：`/api/original-video/{taskId}/`
- 标注视频：`/api/video/{taskId}/`

### 3. 视图模式切换

在 `AnalysisResult.vue` 中实现整体视图和细化视图的切换。

#### 整体视图

展示完整的分析结果：
- 统计卡片（细胞总数、总帧数、视频时长）
- VideoPlayer 组件（双视频对比播放）
- CellPopulationChart（细胞群体图表）
- CellDetailList（细胞详情列表）

#### 细化视图

提供更详细的逐帧分析：
- 左侧区域：
  - 标注视频播放器
  - 视频功能栏（播放/暂停/帧控制/回到开头）
- 右侧区域：
  - 逐帧分析（待开发）

#### 切换逻辑

```typescript
// 切换记录时自动重置为整体模式
watch(() => props.record, () => {
  viewMode.value = 'overall'
})

// 切换视频记录时自动重置播放速率
watch(() => props.record.task_id, () => {
  currentPlaybackRate.value = 1
  showRateMenu.value = false
  if (originalVideoRef.value) {
    originalVideoRef.value.playbackRate = 1
  }
  if (annotatedVideoRef.value) {
    annotatedVideoRef.value.playbackRate = 1
  }
})
```

### 2. 数据流详解

#### 完整的数据层次结构

```
AnalysisRecord (分析记录/处理任务)
  ├─ task_id: 任务ID
  ├─ video_name: 视频文件名
  ├─ video_path: 原始视频路径
  ├─ status: 任务状态
  ├─ progress: 处理进度
  ├─ start_time: 开始时间
  ├─ end_time: 结束时间
  └─ result (ProcessResult)
      ├─ output_video_path: 标注视频路径
      ├─ cell_count: 细胞总数
      ├─ total_frames: 总帧数
      └─ cells: CellData[] (细胞列表)
          ├─ cell_id: 细胞ID
          └─ frames: CellFrameData[] (每一帧的数据)
              ├─ frame_number: 帧号
              ├─ position: {x, y} 中心位置
              ├─ area: 细胞面积
              ├─ velocity: {vx, vy, speed} 速度向量
              └─ bounding_box: {x, y, width, height} 边界框
```

#### 查看细胞详情的完整流程

```
1. 用户点击"查看详情"按钮
   ↓
2. handleViewCell(cellId) 被调用
   ↓
3. store.selectCell(cellId) 设置 selectedCellId
   ↓
4. selectedCellData (computed) 自动计算
   └─ 从 selectedRecord.result.cells 中查找匹配的细胞
   └─ 返回完整的 CellData 对象
   ↓
5. ResultPanel 检测到 store.selectedCellData 存在
   ↓
6. 显示 CellDetailPanel 组件
   └─ 传递 cellData prop (完整的细胞数据对象)
   ↓
7. CellDetailPanel 显示细胞详情
   ├─ 基本信息：从 cellData 获取
   ├─ 位置表格：从 cellData.positions 获取
   └─ 返回按钮：emit('back') → handleBackToList() → 清空 selectedCellId
```

#### 关键计算属性

**selectedCellData** (src/stores/analysisStore.ts:82-89):
```typescript
const selectedCellData = computed(() => {
  if (!selectedCellId.value || !selectedRecord.value?.result?.cells) {
    return null
  }
  return selectedRecord.value.result.cells.find(
    (cell) => cell.id === selectedCellId.value
  ) || null
})
```

这个计算属性的作用：
- 响应式地根据 `selectedCellId` 的变化
- 从当前选中的分析记录中查找对应的细胞数据
- 返回完整的 CellData 对象，包含所有位置信息
- 如果没有找到或没有数据，返回 null

### 3. 组件架构

#### 组件通信图

```
CellTrackingView (主页面)
  ├─ Sidebar (侧边栏)
  │   ├─ 新建分析按钮
  │   └─ 历史记录列表
  │       └─ 点击记录 → store.selectRecord(id)
  │
  └─ 主面板 (根据状态切换)
      ├─ WelcomePanel (欢迎界面)
      ├─ UploadPanel (上传面板)
      ├─ ProgressView (进度展示)
      └─ AnalysisResult (分析结果组件)
          ├─ ResultHeader (结果头部)
          │   ├─ 视频信息展示
          │   ├─ 视图模式切换（整体/细化）
          │   └─ 导出/下载按钮
          │
          └─ 结果内容 (根据 viewMode 切换)
              ├─ 整体模式 (viewMode === 'overall')
              │   ├─ 统计卡片
              │   ├─ VideoPlayer (视频播放器)
              │   │   ├─ 原始视频播放
              │   │   ├─ 标注视频播放
              │   │   ├─ 布局切换（并排/上下）
              │   │   ├─ 播放控制（播放/暂停/帧控制/速率调整）
              │   │   └─ 视频功能栏
              │   ├─ CellPopulationChart (细胞群体图表)
              │   └─ CellDetailList (细胞详情列表)
              │       └─ 点击"查看详情" → store.selectCell(cellId)
              │
              └─ 细化模式 (viewMode === 'detail')
                  ├─ 标注视频播放器
                  │   ├─ 视频显示
                  │   └─ 视频功能栏（播放/暂停/帧控制/回到开头）
                  └─ 逐帧分析区域
                      └─ 占位符（待开发）

  当 store.selectedCellData 存在时
  └─ CellDetailPanel (覆盖显示)
      ├─ 显示细胞详情
      └─ emit('back') 返回列表
```

#### 页面状态切换逻辑

在 `CellTrackingView.vue` 中使用计算属性控制显示：

```typescript
const currentPanel = computed(() => {
  if (store.showUploadPanel) return 'upload'
  if (store.selectedRecord) {
    if (store.selectedRecord.status === 'processing') return 'loading'
    if (store.selectedRecord.status === 'completed') return 'result'
  }
  return 'welcome'
})
```

#### 视图模式切换

在 `AnalysisResult.vue` 中实现整体/细化视图切换：

```typescript
// 视图模式：整体/细化
const viewMode = ref<'overall' | 'detail'>('overall')

// 监听 record 变化，切换记录时重置为整体模式
watch(() => props.record, () => {
  viewMode.value = 'overall'
})

// 处理视图模式切换
function handleViewModeChange(mode: 'overall' | 'detail') {
  viewMode.value = mode
}
```

**整体模式** (viewMode === 'overall'):
- 显示统计卡片（细胞总数、总帧数、视频时长）
- 显示 VideoPlayer 组件（双视频对比播放）
- 显示 CellPopulationChart（细胞群体图表）
- 显示 CellDetailList（细胞详情列表）

**细化模式** (viewMode === 'detail'):
- 左侧：标注视频播放器 + 视频功能栏
- 右侧：逐帧分析区域（待开发）

### 4. 数据来源

#### 当前阶段（模拟数据）

使用 `generateMockCells()` 函数生成随机的细胞数据：

```typescript
function generateMockCells(count: number, frameCount: number): CellData[] {
  return Array.from({ length: count }, (_, i) => {
    const firstFrame = Math.floor(Math.random() * 20)
    const lastFrame = frameCount - Math.floor(Math.random() * 20)
    const frames = lastFrame - firstFrame
    const positions = Array.from({ length: Math.min(frames, 20) }, (_, j) => {
      // 生成位置数据...
    })
    return {
      id: `Cell #${i + 1}`,
      firstFrame,
      lastFrame,
      frameCount: frames,
      avgSpeed: Math.random() * 3 + 0.5,
      totalDistance: Math.random() * 300 + 100,
      positions,
    }
  })
}
```

#### 未来实现（对接后端 API）

后端 API 应返回以下格式的数据（符合需求文档 6.3节）：

```json
{
  "task_id": "task_001",
  "video_name": "sample.mp4",
  "video_path": "/uploads/sample.mp4",
  "status": "completed",
  "progress": 100,
  "start_time": "2024-02-10T10:00:00Z",
  "end_time": "2024-02-10T10:05:30Z",
  "result": {
    "output_video_path": "/outputs/sample_annotated.mp4",
    "cell_count": 25,
    "total_frames": 120,
    "cells": [
      {
        "cell_id": "Cell #1",
        "frames": [
          {
            "frame_number": 0,
            "position": {
              "x": 100.5,
              "y": 150.3
            },
            "area": 215.6,
            "velocity": {
              "vx": 2.3,
              "vy": 1.2,
              "speed": 2.59
            },
            "bounding_box": {
              "x": 90.5,
              "y": 140.3,
              "width": 20.0,
              "height": 20.0
            }
          },
          {
            "frame_number": 10,
            "position": {
              "x": 110.2,
              "y": 160.5
            },
            "area": 220.3,
            "velocity": {
              "vx": 2.5,
              "vy": 1.5,
              "speed": 2.92
            },
            "bounding_box": {
              "x": 100.2,
              "y": 150.5,
              "width": 20.0,
              "height": 20.0
            }
          }
          // ... 更多帧数据
        ]
      }
      // ... 更多细胞数据
    ]
  }
}
```

### 5. API 集成准备

#### 需要实现的 API 端点（符合需求文档第7节）

1. **上传视频并创建分析**
   - `POST /api/upload`
   - 请求：multipart/form-data (video file)
   - 响应：AnalysisRecord (status: 'processing', progress: 0)

2. **启动处理任务**
   - `POST /api/process`
   - 请求：{ task_id: string, params?: object }
   - 响应：{ task_id: string, status: string }

3. **获取任务状态**
   - `GET /api/status/:task_id`
   - 响应：{ status: AnalysisStatus, progress: number }

4. **获取处理结果**
   - `GET /api/result/:task_id`
   - 响应：ProcessResult (包含完整的细胞数据)

5. **获取细胞数据列表**
   - `GET /api/cells/:task_id`
   - 响应：CellData[]

6. **获取单个细胞数据**
   - `GET /api/cell/:task_id/:cell_id`
   - 响应：CellData

7. **导出分析数据**
   - `GET /api/export/:task_id`
   - 响应：CSV/JSON 文件

8. **获取标注视频**
   - `GET /api/video/:task_id`
   - 响应：视频文件流

#### Axios 配置示例

在 `src/api/analysisApi.ts` 中（已创建）：

```typescript
import axios from 'axios'
import type { AnalysisRecord } from '@/stores/analysisStore'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export const analysisApi = {
  // 上传视频
  async upload(file: File): Promise<AnalysisRecord> {
    const formData = new FormData()
    formData.append('video', file)
    const { data } = await api.post('/upload', formData)
    return data
  },

  // 启动处理任务
  async startProcess(taskId: string, params?: object): Promise<{ task_id: string, status: string }> {
    const { data } = await api.post('/process', { task_id: taskId, params })
    return data
  },

  // 获取任务状态
  async getStatus(taskId: string): Promise<{ status: string, progress: number }> {
    const { data } = await api.get(`/status/${taskId}`)
    return data
  },

  // 获取处理结果
  async getResult(taskId: string): Promise<ProcessResult> {
    const { data } = await api.get(`/result/${taskId}`)
    return data
  },

  // 获取细胞数据列表
  async getCells(taskId: string): Promise<CellData[]> {
    const { data } = await api.get(`/cells/${taskId}`)
    return data
  },

  // 获取单个细胞数据
  async getCell(taskId: string, cellId: string): Promise<CellData> {
    const { data } = await api.get(`/cell/${taskId}/${cellId}`)
    return data
  },

  // 导出数据
  async export(taskId: string, format: 'csv' | 'json' = 'csv') {
    const { data } = await api.get(`/export/${taskId}`, {
      params: { format },
      responseType: 'blob'
    })
    return data
  },

  // 获取标注视频URL
  getVideoUrl(taskId: string): string {
    return `${api.defaults.baseURL}/video/${taskId}`
  },
}
```

## 开发指南

### 运行开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

### 类型检查

```bash
npm run type-check
```

### 代码检查和修复

```bash
npm run lint
```

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

## 样式规范

### TailwindCSS v4

项目使用 TailwindCSS v4 作为样式框架，配置文件：`vite.config.ts`

```typescript
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    tailwindcss(),
  ],
})
```

### 设计系统

主题色：
- 背景色：`#0d1117` (深色背景)
- 卡片背景：`#161b22`
- 边框色：`#30363d`
- 主色调：`#58a6ff` (蓝色)
- 文字色：`#c9d1d9` (浅灰)
- 次要文字：`#8b949e`

### 组件样式

使用 scoped 样式避免样式污染：

```vue
<style scoped>
.my-component {
  /* 组件特定样式 */
}
</style>
```

## 调试技巧

### Vue DevTools

安装 Vue.js devtools 浏览器扩展，可以：
- 查看组件树
- 检查 Pinia 状态
- 追踪事件
- 查看路由状态

### TypeScript 类型提示

在 VS Code 中，安装 Volar 扩展获得完整的类型提示和智能补全。

### 常见问题

1. **组件样式不生效**
   - 检查是否使用了 `scoped` 属性
   - 确认 TailwindCSS 类名是否正确

2. **状态更新不响应**
   - 确保使用 `ref` 或 `reactive` 包装响应式数据
   - 检查计算属性的依赖是否正确

3. **路由跳转失败**
   - 检查路由配置是否正确
   - 确认路由名称或路径是否匹配

## API 集成状态

### ✅ 已实现
- [x] API 服务封装 (src/api/analysisApi.ts)
- [x] Composable 函数 (src/composables/useAnalysisApi.ts)
- [x] Toast 提示组合式函数 (src/composables/useToast.ts)
- [x] WebSocket 实时更新支持
- [x] 上传进度显示
- [x] 数据导出功能（CSV/JSON）
- [x] 视频下载功能
- [x] 状态轮询机制
- [x] Store 集成支持
- [x] 视频播放器 API 集成（原始视频/标注视频）
- [x] 视图模式切换功能
- [x] 视频播放控制功能（播放/暂停/帧控制/速率调整）

### 🔄 待对接
- [ ] 后端 API 实现（当前使用模拟数据）
- [ ] WebSocket 服务端实现
- [ ] 在 UploadPanel.vue 中启用真实 API 调用（当前被注释）
- [ ] 逐帧分析数据 API

详细信息请查看 [API-INTEGRATION.md](./API-INTEGRATION.md)

## 待实现功能

### ✅ 已完成
- [x] 对接后端 API（API 封装已完成）
- [x] 视频播放器功能（双视频对比、布局切换、播放控制）
- [x] 视图模式切换（整体/细化视图）
- [x] 细化视图基础结构（视频播放器 + 逐帧分析区域）
- [x] 视频功能栏（播放/暂停/帧控制/速率调整/回到开头）
- [x] 结果头部组件（视图切换、导出功能）
- [x] 细胞群体图表组件
- [x] 细胞详情列表组件
- [x] Toast 提示功能
- [x] 数据导出功能（CSV/JSON）
- [x] 视频下载功能
- [x] 状态轮询机制

### 🔄 待开发
- [ ] 逐帧分析功能（细化视图右侧区域）
- [ ] 添加 3D 轨迹可视化（Three.js / D3.js）
- [ ] 添加数据筛选和排序
- [ ] 实现轨迹动画播放
- [ ] 添加用户认证
- [ ] 添加错误处理和重试机制
- [ ] 优化大数据集的渲染性能
- [ ] 添加单元测试
- [ ] 添加模型上传功能

## 参考文档

- [Vue 3 文档](https://cn.vuejs.org/)
- [Vite 文档](https://cn.vitejs.dev/)
- [Pinia 文档](https://pinia.vuejs.org/zh/)
- [TailwindCSS 文档](https://tailwindcss.com/)
- [TypeScript 文档](https://www.typescriptlang.org/)
