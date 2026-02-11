<script setup lang="ts">
import { ref } from 'vue'
import { useAnalysisStore } from '@/stores/analysisStore'

const store = useAnalysisStore()
const selectedFile = ref<File | null>(null)
const isDragging = ref(false)

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

function submitUpload() {
  if (selectedFile.value) {
    store.addRecord(selectedFile.value.name, selectedFile.value)
    selectedFile.value = null
  }
}

function clearFile() {
  selectedFile.value = null
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

      <div class="upload-actions">
        <button class="btn-submit" :disabled="!selectedFile" @click="submitUpload">
          开始分析
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
}

.upload-description {
  text-align: center;
  color: #8b949e;
  margin: 0 0 2rem 0;
}

.upload-area {
  border: 2px dashed #30363d;
  border-radius: 12px;
  padding: 3rem 2rem;
  background: #161b22;
  transition: all 0.3s;
  position: relative;
}

.upload-area.dragging {
  border-color: #1f6feb;
  background: #0d1520;
}

.upload-area.has-file {
  border-color: #238636;
  background: #0d1520;
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
}

.upload-text {
  font-size: 1.1rem;
  color: #c9d1d9;
  margin: 0 0 0.5rem 0;
}

.upload-hint {
  font-size: 0.9rem;
  color: #8b949e;
  margin: 0;
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
}

.file-size {
  font-size: 0.875rem;
  color: #8b949e;
  margin: 0;
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

.btn-clear:hover {
  background: #21262d;
  border-color: #8b949e;
  color: #c9d1d9;
}

.btn-clear svg {
  width: 16px;
  height: 16px;
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
</style>
