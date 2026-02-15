<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAnalysisStore } from '@/stores/analysisStore'
import { useAnalysisApi } from '@/composables/useAnalysisApi'
import axios from 'axios'

const store = useAnalysisStore()
const api = useAnalysisApi()

const selectedFile = ref<File | null>(null)
const isDragging = ref(false)
const showAdvancedSettings = ref(false)

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

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
    selectedFile.value = event.dataTransfer.files[0]
  }
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
  isDragging.value = true
}

function handleDragLeave() {
  isDragging.value = false
}

async function submitUpload() {
  if (!selectedFile.value) return

  try {
    uploadStatus.value = 'uploading'
    uploadProgress.value = 0
    uploadError.value = null

    // 1. 上传视频
    const formData = new FormData()
    formData.append('video', selectedFile.value)

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
    uploadStatus.value = 'processing'

    // 2. 启动处理任务
    await axios.post('/api/process/', {
      task_id: taskId.value,
      conf: modelParams.value.conf,
      imgsz: modelParams.value.imgsz,
      fps: modelParams.value.fps,
    })

    // 3. 开始轮询任务状态
    pollTaskStatus()

    // 清理
    selectedFile.value = null

  } catch (error: any) {
    uploadStatus.value = 'error'
    uploadError.value = error.response?.data?.error || error.message || '处理失败'
    console.error('Upload error:', error)
  }
}

async function pollTaskStatus() {
  if (!taskId.value) return

  const pollInterval = setInterval(async () => {
    try {
      const response = await axios.get(`/api/status/${taskId.value}/`)
      const data = response.data

      // 更新进度
      uploadProgress.value = data.progress || 0
      uploadStage.value = data.stage || ''
      uploadMessage.value = data.message || ''
      currentFrame.value = data.current_frame || null
      totalFrames.value = data.total_frames || null

      // 如果任务完成
      if (data.status === 'completed') {
        clearInterval(pollInterval)
        uploadStatus.value = 'completed'

        // 获取完整结果
        const resultResponse = await axios.get(`/api/result/${taskId.value}/`)
        const result = resultResponse.data

        // 添加到 store
        store.addUploadedRecord({
          task_id: result.task_id,
          video_name: result.original_video_path.split('/').pop() || 'Unknown',
          video_path: result.original_video_path,
          status: 'completed',
          progress: 100,
          start_time: new Date(result.created_at),
          result: {
            output_video_path: result.annotated_video_path,
            cell_count: result.cell_count,
            total_frames: result.total_frames,
            cells: [], // 可以根据 frame_labels 解析出细胞数据
          },
        })
      } else if (data.status === 'failed') {
        clearInterval(pollInterval)
        uploadStatus.value = 'error'
        uploadError.value = data.error || '处理失败'
      }
    } catch (error: any) {
      clearInterval(pollInterval)
      uploadStatus.value = 'error'
      uploadError.value = error.response?.data?.error || error.message || '查询状态失败'
    }
  }, 2000) // 每2秒轮询一次

  return pollInterval
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
  <div class="upload-panel">
    <div class="upload-container">
      <h2>上传视频文件</h2>
      <p class="upload-description">上传细胞显微镜视频进行分析</p>

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
            <p class="file-name">{{ selectedFile.name }}</p>
            <p class="file-size">{{ (selectedFile.size / 1024 / 1024).toFixed(2) }} MB</p>
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
      </div>

      <div class="upload-actions">
        <button
          class="btn-submit"
          :disabled="!selectedFile || uploadStatus === 'uploading' || uploadStatus === 'processing'"
          @click="submitUpload"
        >
          {{
            uploadStatus === 'uploading' ? '上传中...' :
            uploadStatus === 'processing' ? '处理中...' :
            '开始分析'
          }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.upload-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: #0d1117;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .upload-panel {
  background: #f5f5f5;
}

.upload-container {
  max-width: 600px;
  width: 100%;
}

h2 {
  font-size: 2rem;
  font-weight: 600;
  color: #fff;
  margin: 0 0 0.5rem 0;
  text-align: center;
  transition: color 0.3s;
}

:global(:root:not(.dark)) h2 {
  color: #333;
}

.upload-description {
  text-align: center;
  color: #8b949e;
  margin: 0 0 2rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .upload-description {
  color: #666;
}

.upload-area {
  border: 2px dashed #30363d;
  border-radius: 12px;
  padding: 3rem 2rem;
  background: #161b22;
  transition: all 0.3s;
  position: relative;
}

:global(:root:not(.dark)) .upload-area {
  border-color: #ccc;
  background: #fff;
}

.upload-area.dragging {
  border-color: #1f6feb;
  background: #0d1520;
}

:global(:root:not(.dark)) .upload-area.dragging {
  border-color: #2196f3;
  background: #e3f2fd;
}

.upload-area.has-file {
  border-color: #238636;
  background: #0d1520;
}

:global(:root:not(.dark)) .upload-area.has-file {
  border-color: #4caf50;
  background: #e8f5e9;
}

.upload-placeholder {
  text-align: center;
  position: relative;
  cursor: pointer;
}

.upload-icon {
  width: 64px;
  height: 64px;
  color: #8b949e;
  margin: 0 auto 1rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .upload-icon {
  color: #999;
}

.upload-text {
  font-size: 1.1rem;
  color: #c9d1d9;
  margin: 0 0 0.5rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .upload-text {
  color: #333;
}

.upload-hint {
  font-size: 0.9rem;
  color: #8b949e;
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .upload-hint {
  color: #666;
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
  background: #0d1117;
  border-radius: 8px;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .file-info {
  background: #f5f5f5;
}

.file-icon {
  width: 48px;
  height: 48px;
  color: #58a6ff;
  flex-shrink: 0;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 1rem;
  color: #c9d1d9;
  margin: 0 0 0.25rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .file-name {
  color: #333;
}

.file-size {
  font-size: 0.875rem;
  color: #8b949e;
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .file-size {
  color: #666;
}

.btn-clear {
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: 1px solid #30363d;
  border-radius: 6px;
  color: #8b949e;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

:global(:root:not(.dark)) .btn-clear {
  border-color: #ccc;
  color: #666;
}

.btn-clear:hover {
  background: #21262d;
  border-color: #8b949e;
  color: #c9d1d9;
}

:global(:root:not(.dark)) .btn-clear:hover {
  background: #e0e0e0;
  border-color: #999;
  color: #333;
}

.btn-clear svg {
  width: 16px;
  height: 16px;
}

.advanced-settings {
  margin-top: 1.5rem;
}

.btn-toggle-settings {
  width: 100%;
  padding: 0.75rem 1rem;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  color: #c9d1d9;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

:global(:root:not(.dark)) .btn-toggle-settings {
  background: #fff;
  border-color: #ccc;
  color: #333;
}

.btn-toggle-settings:hover {
  background: #21262d;
  border-color: #58a6ff;
}

:global(:root:not(.dark)) .btn-toggle-settings:hover {
  background: #f5f5f5;
  border-color: #2196f3;
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
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  animation: slideDown 0.3s ease;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .settings-content {
  background: #fff;
  border-color: #ccc;
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
  color: #c9d1d9;
  margin-bottom: 0.5rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .setting-label {
  color: #333;
}

.setting-value {
  background: #21262d;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-size: 0.8rem;
  color: #58a6ff;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .setting-value {
  background: #e0e0e0;
  color: #2196f3;
}

.setting-slider {
  width: 100%;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: #21262d;
  border-radius: 3px;
  outline: none;
  cursor: pointer;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .setting-slider {
  background: #e0e0e0;
}

.setting-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  background: #58a6ff;
  border-radius: 50%;
  cursor: pointer;
  transition: background 0.2s;
}

.setting-slider::-webkit-slider-thumb:hover {
  background: #1f6feb;
}

.setting-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: #58a6ff;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: background 0.2s;
}

.setting-slider::-moz-range-thumb:hover {
  background: #1f6feb;
}

.setting-select {
  width: 100%;
  padding: 0.5rem;
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 6px;
  color: #c9d1d9;
  font-size: 0.9rem;
  cursor: pointer;
  transition: border-color 0.2s, background 0.3s;
}

:global(:root:not(.dark)) .setting-select {
  background: #fff;
  border-color: #ccc;
  color: #333;
}

.setting-select:hover {
  border-color: #58a6ff;
}

:global(:root:not(.dark)) .setting-select:hover {
  border-color: #2196f3;
}

.setting-select:focus {
  outline: none;
  border-color: #58a6ff;
}

.setting-hint {
  font-size: 0.8rem;
  color: #8b949e;
  margin-top: 0.5rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .setting-hint {
  color: #666;
}

.upload-progress {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #161b22;
  border-radius: 8px;
  border: 1px solid #30363d;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .upload-progress {
  background: #fff;
  border-color: #ccc;
}

.progress-bar {
  height: 8px;
  background: #21262d;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .progress-bar {
  background: #e0e0e0;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #238636, #2ea043);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.875rem;
  color: #58a6ff;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  text-align: center;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .progress-text {
  color: #2196f3;
}

.progress-details {
  text-align: center;
}

.progress-message {
  font-size: 0.8rem;
  color: #8b949e;
  margin: 0 0 0.25rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .progress-message {
  color: #666;
}

.progress-frame-info {
  font-size: 0.8rem;
  color: #58a6ff;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .progress-frame-info {
  color: #2196f3;
}

.upload-error {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: #1c1917;
  border: 1px solid #dc2626;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #f87171;
  font-size: 0.875rem;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .upload-error {
  background: #fff5f5;
  border-color: #ef4444;
}

.upload-error svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.upload-actions {
  margin-top: 1.5rem;
  text-align: center;
}

.btn-submit {
  padding: 0.75rem 2rem;
  background: #238636;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-submit:hover:not(:disabled) {
  background: #2ea043;
}

.btn-submit:disabled {
  background: #21262d;
  color: #6e7681;
  cursor: not-allowed;
}

:global(:root:not(.dark)) .btn-submit:disabled {
  background: #e0e0e0;
  color: #999;
}
</style>
