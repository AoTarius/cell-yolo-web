<script setup lang="ts">
import '@/assets/styles/colors.css'
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAnalysisStore } from '@/stores/analysisStore'
import { useUserStore } from '@/stores/userStore'
import { useAnalysisApi } from '@/composables/useAnalysisApi'
import { useToast } from '@/composables/useToast'
import { analysisApi } from '@/api/analysisApi'
import axios from 'axios'
import Sidebar from '@/components/common/layout/Sidebar.vue'

const router = useRouter()
const store = useAnalysisStore()
const userStore = useUserStore()
const api = useAnalysisApi()
const { showToast } = useToast()

const selectedFile = ref<File | null>(null)
const isDragging = ref(false)
const showAdvancedSettings = ref(false)
const currentOutputPath = ref('')

// 模型相关
const models = ref<Array<{ name: string; size_mb: number; path: string }>>([])
const selectedModel = ref('')  // 改为空字符串，表示未选择
const isLoadingModels = ref(false)
const hasModels = computed(() => models.value.length > 0)  // 判断是否有可用模型

function isImportedTaskModelName(name: string): boolean {
  const raw = (name || '').trim()
  if (!raw) return true
  const normalized = raw.replace(/\\/g, '/')
  // 约定：导入任务遗留模型通常为路径或带文件后缀的名称，不作为“我自己的可用模型”
  return normalized.includes('/') || /^[a-zA-Z]:/.test(raw) || /\.pt$/i.test(raw)
}

// 模型参数
const modelParams = ref({
  conf: 0.3,
  imgsz: 1024,
  fps: 10
})

// 是否正在上传或已上传
const isProcessing = computed(() => api.isUploading.value || api.uploadProgress.value === 100)

// 上传状态
const uploadProgress = ref(0)
const uploadStatus = ref<'idle' | 'uploading' | 'processing' | 'completed' | 'error'>('idle')
const uploadError = ref<string | null>(null)
const taskId = ref<string | null>(null)
const uploadStage = ref<string>('')
const uploadMessage = ref<string>('')
const currentFrame = ref<number | null>(null)
const totalFrames = ref<number | null>(null)

// 加载模型列表
async function loadModels() {
  try {
    isLoadingModels.value = true

    if (!userStore.currentUser?.username) {
      models.value = []
      selectedModel.value = ''
      return
    }

    const username = userStore.currentUser.username
    const data = await analysisApi.getModels(username)
    const rawModels = Array.isArray(data?.models) ? data.models : []
    models.value = rawModels.filter((model: { name: string }) => !isImportedTaskModelName(model.name))
    // 始终默认为空，让用户手动选择
    selectedModel.value = ''
  } catch (error) {
    console.error('加载模型列表失败:', error)
    models.value = []
    selectedModel.value = ''
  } finally {
    isLoadingModels.value = false
  }
}

// 组件挂载时加载模型列表
onMounted(() => {
  loadModels()

  // 获取用户的output_base_path
  if (userStore.currentUser) {
    currentOutputPath.value = userStore.currentUser.output_base_path || 'data/output/tasks'
  }
})

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0 && target.files[0]) {
    selectedFile.value = target.files[0]
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0 && event.dataTransfer.files[0]) {
    selectedFile.value = event.dataTransfer.files[0]
  }
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
  isDragging.value = true
}

function handleDragLeave(event: DragEvent) {
  // 防止从子元素触发 dragleave 事件
  if (event.target === event.currentTarget) {
    isDragging.value = false
  }
}

async function submitUpload() {
  if (!selectedFile.value) return

  if (!selectedModel.value) {
    uploadError.value = '请先选择一个模型'
    return
  }

  try {
    uploadStatus.value = 'uploading'
    uploadProgress.value = 0
    uploadError.value = null

    if (!userStore.currentUser?.username) {
      showToast('请先登录', 'error')
      return
    }

    const username = userStore.currentUser.username

    // 1. 上传视频
    const formData = new FormData()
    formData.append('video', selectedFile.value)
    formData.append('username', username)

    const uploadResponse = await axios.post('/api/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        }
      },
    })

    taskId.value = uploadResponse.data.task_id
    const videoId = uploadResponse.data.video_id
    uploadStatus.value = 'processing'

    // 2. 启动处理任务
    await axios.post('/api/process/', {
      task_id: taskId.value!,
      video_id: videoId,
      conf: modelParams.value.conf,
      imgsz: modelParams.value.imgsz,
      fps: modelParams.value.fps,
      model_name: selectedModel.value,
      username: username,
    })

    // 3. 添加处理中记录到 store（store 会自动轮询进度）
    const fileName = selectedFile.value.name
    store.addProcessingRecord({
      task_id: taskId.value!,
      video_name: fileName,
      video_path: uploadResponse.data.video_path || '',
      status: 'processing',
      progress: 0,
      start_time: new Date(),
    })

    // 4. 重置表单状态
    showAdvancedSettings.value = false
    selectedFile.value = null
    uploadStatus.value = 'idle'
    uploadProgress.value = 0
    taskId.value = null

    // 显示成功提示
    showToast(`分析任务已启动！视频 "${fileName}" 正在处理中...`, 'success')

    // 5. 跳转到主页并选中该任务
    router.push('/').then(() => {
      store.selectRecord(taskId.value!)
    })

  } catch (error: any) {
    uploadStatus.value = 'error'
    uploadError.value = error.response?.data?.error || error.message || '处理失败'
    console.error('Upload error:', error)
    showToast(error.response?.data?.error || error.message || '处理失败', 'error')
  }
}

function clearFile() {
  selectedFile.value = null
}

function getStageLabel(stage: string): string {
  const stageMap: Record<string, string> = {
    'extracting': '分解视频',
    'processing': 'YOLO 推理',
    'packaging': '生成结果',
    'status': '状态更新',
    'complete': '完成'
  }
  return stageMap[stage] || '处理中'
}
</script>

<template>
  <div class="upload-view">
    <Sidebar />

    <main class="main-panel">
      <div class="upload-container">
        <h2>上传视频文件</h2>
        <p class="upload-description">上传细胞显微镜视频进行分析</p>

      <!-- 路径提示框 -->
      <div class="path-info-box">
        <svg
          class="path-icon"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          ></path>
        </svg>
        <div class="path-content">
          <p class="path-label">当前任务存储路径：</p>
          <p class="path-value">{{ currentOutputPath || '未设置' }}</p>
        </div>
      </div>

      <div
        class="upload-area"
        :class="{ dragging: isDragging, 'has-file': selectedFile }"
        @drop.prevent="handleDrop"
        @dragover.prevent="handleDragOver"
        @dragleave="handleDragLeave"
      >
        <div v-if="!selectedFile" class="upload-placeholder">
          <svg
            class="upload-icon"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            ></path>
          </svg>
          <p class="upload-text">拖拽视频文件到此处，或点击选择</p>
          <p class="upload-hint">支持 MP4, AVI, MOV 等格式</p>
          <input
            type="file"
            accept="video/*"
            class="file-input"
            @change="handleFileSelect"
          />
        </div>

        <div v-else class="file-info">
          <svg
            class="file-icon"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
            ></path>
          </svg>
          <div class="file-details">
            <p class="file-name">{{ selectedFile?.name }}</p>
            <p class="file-size">{{ selectedFile ? (selectedFile.size / 1024 / 1024).toFixed(2) : '0' }} MB</p>
          </div>
          <button class="btn-clear" @click="clearFile">
            <svg
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              ></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- 模型选择 -->
      <div class="model-selector">
        <label for="model-select" class="model-label">选择模型</label>
        <select
          id="model-select"
          v-model="selectedModel"
          class="model-select"
          :disabled="isLoadingModels || uploadStatus !== 'idle'"
        >
          <option value="" disabled>请选择模型</option>
          <option v-if="isLoadingModels" value="" disabled>加载中...</option>
          <option v-if="!isLoadingModels && models.length === 0" value="" disabled>暂无可用模型</option>
          <option v-for="model in models" :key="model.name" :value="model.name">
            {{ model.name }} ({{ model.size_mb }} MB)
          </option>
        </select>
        <p v-if="!isLoadingModels && models.length === 0" class="model-warning">
          ⚠️ 检测到没有可用的模型文件，请在"模型管理"中上传模型。
        </p>
      </div>

      <!-- 高级参数设置 -->
      <div class="advanced-settings">
        <button class="btn-toggle-settings" @click="showAdvancedSettings = !showAdvancedSettings">
          <span>高级参数设置</span>
          <svg
            class="chevron-icon"
            :class="{ expanded: showAdvancedSettings }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 9l-7 7-7-7"
            ></path>
          </svg>
        </button>

        <div v-show="showAdvancedSettings" class="settings-content">
          <div class="setting-item">
            <label for="conf" class="setting-label">
              置信度阈值 (Confidence)
              <span class="setting-value">{{ modelParams.conf }}</span>
            </label>
            <input
              id="conf"
              type="range"
              min="0.1"
              max="0.9"
              step="0.05"
              v-model.number="modelParams.conf"
              class="setting-slider"
            />
            <div class="setting-hint">值越大，检测越严格</div>
          </div>

          <div class="setting-item">
            <label for="imgsz" class="setting-label">
              图像尺寸 (Image Size)
              <span class="setting-value">{{ modelParams.imgsz }}px</span>
            </label>
            <select id="imgsz" v-model.number="modelParams.imgsz" class="setting-select">
              <option value="640">640px (快速)</option>
              <option value="1024">1024px (平衡)</option>
              <option value="1280">1280px (精确)</option>
            </select>
            <div class="setting-hint">影响检测精度和处理速度</div>
          </div>

          <div class="setting-item">
            <label for="fps" class="setting-label">
              输出视频帧率 (FPS)
              <span class="setting-value">{{ modelParams.fps }}</span>
            </label>
            <select id="fps" v-model.number="modelParams.fps" class="setting-select">
              <option value="5">5 fps</option>
              <option value="10">10 fps</option>
              <option value="15">15 fps</option>
              <option value="30">30 fps</option>
            </select>
            <div class="setting-hint">输出标注视频的帧率</div>
          </div>
        </div>
      </div>

      <!-- 上传进度 -->
      <div v-if="uploadStatus === 'uploading' || uploadStatus === 'processing'" class="upload-progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${uploadProgress}%` }"></div>
        </div>
        <p class="progress-text">
          <span v-if="uploadStatus === 'uploading'">上传中: {{ uploadProgress }}%</span>
          <span v-else>
            {{ getStageLabel(uploadStage) }}: {{ uploadProgress }}%
          </span>
        </p>
        <!-- 详细进度信息 -->
        <div v-if="uploadStatus === 'processing' && uploadMessage" class="progress-details">
          <p class="progress-message">{{ uploadMessage }}</p>
          <p v-if="currentFrame !== null && totalFrames !== null" class="progress-frame-info">
            帧: {{ currentFrame }} / {{ totalFrames }}
          </p>
        </div>
      </div>

      <!-- 错误提示 -->
      <div v-if="uploadError" class="upload-error">
        <svg
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          ></path>
        </svg>
        <span>{{ uploadError }}</span>
        <button class="btn-close-error" @click="uploadError = null" aria-label="关闭错误提示">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <div class="upload-actions">
        <button
          class="btn-submit"
          :disabled="!selectedFile || uploadStatus === 'uploading' || uploadStatus === 'processing' || !selectedModel"
          @click="submitUpload"
        >
          {{
            uploadStatus === 'uploading' ? '上传中...' :
            uploadStatus === 'processing' ? '处理中...' :
            !selectedModel ? '请选择模型' :
            '开始分析'
          }}
        </button>
      </div>
    </div>
    </main>
  </div>
</template>

<style scoped>
.upload-view {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: var(--bg-main);
  color: var(--text-secondary);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    sans-serif;
  position: fixed;
  top: 0;
  left: 0;
}

.main-panel {
  flex: 1;
  display: flex;
  overflow-y: auto;
  align-items: flex-start;
  justify-content: center;
}

.upload-container {
  max-width: 800px;
  width: 100%;
  display: flex;
  flex-direction: column;
  padding: 2rem;
  margin: 3rem auto;
}

h2 {
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
  text-align: center;
  transition: color 0.3s;
}

:global(:root:not(.dark)) h2 {
  color: var(--text-primary-light);
}

.upload-description {
  text-align: center;
  color: var(--text-muted);
  margin: 0 0 1.5rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .upload-description {
  color: var(--text-muted-light);
}

.path-info-box {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--alpha-badge);
  border: 2px dashed var(--border-color);
  border-radius: 6px;
  margin-bottom: 1.5rem;
  transition: all 0.2s;
}

:global(:root:not(.dark)) .path-info-box {
  background: var(--alpha-badge-light);
  border-color: var(--border-color-light);
}

.path-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: var(--accent-blue);
}

.path-content {
  flex: 1;
  min-width: 0;
}

.path-label {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0 0 0.25rem 0;
}

:global(:root:not(.dark)) .path-label {
  color: var(--text-muted-light);
}

.path-value {
  font-size: 0.875rem;
  color: var(--text-primary);
  margin: 0;
  font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:global(:root:not(.dark)) .path-value {
  color: var(--text-primary-light);
}

:global(:root:not(.dark)) .upload-description {
  color: var(--text-muted-light);
}

.upload-area {
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  padding: 3rem 2rem;
  background: var(--bg-card);
  transition: all 0.3s;
  position: relative;
  margin-top: 0;
}

:global(:root:not(.dark)) .upload-area {
  border-color: var(--border-color-light);
  background: var(--bg-card-light);
}

.upload-area.dragging {
  border-color: var(--accent-blue);
  background: var(--upload-hover-bg);
}

:global(:root:not(.dark)) .upload-area.dragging {
  border-color: var(--accent-blue);
  background: var(--upload-hover-bg);
}

.upload-area.has-file {
  border-color: var(--success);
  background: var(--upload-hover-bg);
}

:global(:root:not(.dark)) .upload-area.has-file {
  border-color: var(--success-light);
  background: var(--upload-success-bg);
}

.upload-placeholder {
  text-align: center;
  position: relative;
  cursor: pointer;
}

.upload-icon {
  width: 64px;
  height: 64px;
  color: var(--text-muted);
  margin: 0 auto 1rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .upload-icon {
  color: var(--text-disabled-light);
}

.upload-text {
  font-size: 1.1rem;
  color: var(--text-secondary);
  margin: 0 0 0.5rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .upload-text {
  color: var(--text-primary-light);
}

.upload-hint {
  font-size: 0.9rem;
  color: var(--text-muted);
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .upload-hint {
  color: var(--text-muted-light);
}

.file-input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: var(--bg-main);
  border-radius: 8px;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .file-info {
  background: var(--bg-main-light);
}

.file-icon {
  width: 48px;
  height: 48px;
  color: var(--accent-blue);
  flex-shrink: 0;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0 0 0.25rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .file-name {
  color: var(--text-primary-light);
}

.file-size {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .file-size {
  color: var(--text-muted-light);
}

.btn-clear {
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

:global(:root:not(.dark)) .btn-clear {
  border-color: var(--border-color-light);
  color: var(--text-muted-light);
}

.btn-clear:hover {
  background: var(--bg-input);
  border-color: var(--text-muted);
  color: var(--text-secondary);
}

:global(:root:not(.dark)) .btn-clear:hover {
  background: var(--bg-input-light);
  border-color: var(--text-disabled-light);
  color: var(--text-primary-light);
}

.btn-clear svg {
  width: 16px;
  height: 16px;
}

.model-selector {
  margin-top: 1.5rem;
}

.model-label {
  display: block;
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .model-label {
  color: var(--text-primary-light);
}

.model-select {
  width: 100%;
  padding: 0.75rem 1rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%238b949e' d='M6 9L1 4h10z'/%3E%3C/svg%3E") !important;
  background-repeat: no-repeat !important;
  background-position: right 1rem center !important;
  padding-right: 2.5rem;
}

:global(:root:not(.dark)) .model-select {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
  color: var(--text-primary-light);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23666' d='M6 9L1 4h10z'/%3E%3C/svg%3E") !important;
}

.model-select:hover:not(:disabled) {
  background: var(--bg-input);
  border-color: var(--accent-blue);
}

:global(:root:not(.dark)) .model-select:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--accent-blue);
}

.model-select:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px var(--alpha-focus);
}

:global(:root:not(.dark)) .model-select:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px var(--alpha-focus);
}

.model-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.model-warning {
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: var(--danger-bg);
  border-left: 3px solid var(--danger);
  color: var(--danger-light);
  font-size: 0.8rem;
  border-radius: 4px;
  transition: all 0.3s;
}

:global(:root:not(.dark)) .model-warning {
  background: var(--danger-bg);
  border-left-color: var(--danger-hover);
  color: var(--danger-hover);
}

.advanced-settings {
  margin-top: 1.5rem;
}

.btn-toggle-settings {
  width: 100%;
  padding: 0.75rem 1rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

:global(:root:not(.dark)) .btn-toggle-settings {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
  color: var(--text-primary-light);
}

.btn-toggle-settings:hover {
  background: var(--bg-input);
  border-color: var(--accent-blue);
}

:global(:root:not(.dark)) .btn-toggle-settings:hover {
  background: var(--bg-hover);
  border-color: var(--accent-blue);
}

.chevron-icon {
  width: 16px;
  height: 16px;
  transition: transform 0.3s;
}

.chevron-icon.expanded {
  transform: rotate(180deg);
}

.settings-content {
  margin-top: 1rem;
  padding: 1.5rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  animation: slideDown 0.3s ease;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .settings-content {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.setting-item {
  margin-bottom: 1.5rem;
}

.setting-item:last-child {
  margin-bottom: 0;
}

.setting-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .setting-label {
  color: var(--text-primary-light);
}

.setting-value {
  background: var(--bg-input);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-size: 0.8rem;
  color: var(--accent-blue);
  transition: background 0.3s;
}

:global(:root:not(.dark)) .setting-value {
  background: var(--bg-input-light);
  color: var(--accent-blue);
}

.setting-slider {
  width: 100%;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--text-secondary);
  border-radius: 3px;
  outline: none;
  cursor: pointer;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .setting-slider {
  background: var(--bg-input-light);
}

.setting-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  background: var(--accent-blue);
  border-radius: 50%;
  cursor: pointer;
  transition: background 0.2s;
}

.setting-slider::-webkit-slider-thumb:hover {
  background: var(--accent-blue-hover);
}

.setting-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: var(--accent-blue);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: background 0.2s;
}

.setting-slider::-moz-range-thumb:hover {
  background: var(--accent-blue-hover);
}

.setting-select {
  width: 100%;
  padding: 0.75rem 1rem;
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%238b949e' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 1rem center;
  padding-right: 2.5rem;
  font-weight: 500;
}

:global(:root:not(.dark)) .setting-select {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
  color: var(--text-primary-light);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23666' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
}

.setting-select:hover {
  background: var(--bg-input);
  border-color: var(--accent-blue);
  color: var(--text-secondary);
}

:global(:root:not(.dark)) .setting-select:hover {
  background: var(--bg-hover);
  border-color: var(--accent-blue);
  color: var(--text-primary-light);
}

.setting-select:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px var(--alpha-focus);
}

:global(:root:not(.dark)) .setting-select:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px var(--alpha-focus);
}

.setting-hint {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 0.5rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .setting-hint {
  color: var(--text-muted-light);
}

.upload-progress {
  margin-top: 1.5rem;
  padding: 1rem;
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .upload-progress {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

.progress-bar {
  height: 8px;
  background: var(--bg-input);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .progress-bar {
  background: var(--bg-input-light);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--success), var(--success-hover));
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.875rem;
  color: var(--accent-blue);
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  text-align: center;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .progress-text {
  color: var(--accent-blue);
}

.progress-details {
  text-align: center;
}

.progress-message {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin: 0 0 0.25rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .progress-message {
  color: var(--text-muted-light);
}

.progress-frame-info {
  font-size: 0.8rem;
  color: var(--accent-blue);
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .progress-frame-info {
  color: var(--accent-blue);
}

.upload-error {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: var(--bg-toast);
  border: 1px solid var(--danger);
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--danger-light);
  font-size: 0.875rem;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .upload-error {
  background: var(--upload-error-bg);
  border-color: var(--danger-hover);
}

.upload-error svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.btn-close-error {
  width: 24px;
  height: 24px;
  padding: 0;
  background: transparent;
  border: none;
  color: var(--danger-light);
  cursor: pointer;
  margin-left: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.btn-close-error:hover {
  background: var(--danger-bg);
}

.btn-close-error svg {
  width: 16px;
  height: 16px;
}

.upload-actions {
  margin-top: 1.5rem;
  text-align: center;
}

.btn-submit {
  padding: 0.75rem 2rem;
  background: var(--success);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-submit:hover:not(:disabled) {
  background: var(--success-hover);
}

.btn-submit:disabled {
  background: var(--bg-input);
  color: var(--text-disabled);
  cursor: not-allowed;
}

:global(:root:not(.dark)) .btn-submit:disabled {
  background: var(--bg-input-light);
  color: var(--text-disabled-light);
}
</style>