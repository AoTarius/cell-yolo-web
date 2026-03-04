<script setup lang="ts">
import '@/assets/styles/colors.css'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import Sidebar from '@/components/common/Sidebar.vue'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { showToast } = useToast()

const selectedFile = ref<File | null>(null)
const isDragging = ref(false)
const isUploading = ref(false)
const errorMessage = ref('')

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0 && target.files[0]) {
    selectedFile.value = target.files[0]
    errorMessage.value = ''
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0 && event.dataTransfer.files[0]) {
    selectedFile.value = event.dataTransfer.files[0]
    errorMessage.value = ''
  }
}

async function handleUpload() {
  if (!selectedFile.value) return

  isUploading.value = true
  errorMessage.value = ''

  try {
    const formData = new FormData()
    formData.append('model', selectedFile.value)

    const response = await axios.post('/api/models/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    if (response.data.status === 'success') {
      showToast('模型上传成功！', 'success')
      // 2秒后返回主页
      setTimeout(() => {
        router.push('/')
      }, 2000)
    }
  } catch (error: any) {
    errorMessage.value = error.response?.data?.error || '上传失败，请重试'
    showToast(error.response?.data?.error || '上传失败，请重试', 'error')
  } finally {
    isUploading.value = false
  }
}

function handleCancel() {
  selectedFile.value = null
  errorMessage.value = ''
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}
</script>

<template>

  <div class="model-upload-view">

    <Sidebar />



    <main class="main-panel">

      <div class="upload-container">

        <div class="upload-header">

          <h1>上传模型</h1>

          <p class="subtitle">上传 YOLOv8 模型文件 (.pt 格式)</p>

        </div>



        <!-- 上传区域 -->

        <div

          class="upload-area"

          :class="{ 'has-file': selectedFile }"

          @drop.prevent="handleDrop"

          @dragover.prevent="isDragging = true"

          @dragleave.prevent="isDragging = false"

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

            <p class="upload-text">拖拽模型文件到此处，或点击选择</p>

            <p class="upload-hint">支持 .pt 格式</p>

            <input

              type="file"

              accept=".pt"

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

                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"

              ></path>

            </svg>

            <div class="file-details">

              <p class="file-name">{{ selectedFile?.name }}</p>

              <p class="file-size">{{ formatFileSize(selectedFile?.size || 0) }}</p>

            </div>

            <button class="btn-clear" @click="handleCancel">

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



        <!-- 上传按钮 -->

        <div class="upload-actions">

          <button

            class="btn-submit"

            :disabled="!selectedFile || isUploading"

            @click="handleUpload"

          >

            {{ isUploading ? '上传中...' : '确认上传' }}

          </button>

        </div>



        <!-- 错误提示 -->

        <div v-if="errorMessage" class="error-message">

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

          <span>{{ errorMessage }}</span>

          <button class="btn-close-error" @click="errorMessage = ''">

            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">

              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>

            </svg>

          </button>

        </div>

      </div>

    </main>

  </div>

</template>

<style scoped>
.model-upload-view {
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
  overflow: hidden;
  align-items: center;
  justify-content: center;
}

.upload-container {
  max-width: 600px;
  width: 100%;
  display: flex;
  flex-direction: column;
  padding: 2rem;
}

.upload-header {
  text-align: center;
  margin-bottom: 2rem;
}

.upload-header h1 {
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .upload-header h1 {
  color: var(--text-primary-light);
}

.subtitle {
  color: var(--text-muted);
  font-size: 1rem;
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .subtitle {
  color: var(--text-muted-light);
}

.upload-area {
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  padding: 3rem 2rem;
  background: var(--bg-card);
  transition: all 0.3s;
  position: relative;
}

:global(:root:not(.dark)) .upload-area {
  border-color: var(--border-color-light);
  background: var(--bg-card-light);
}

.upload-area:hover {
  border-color: var(--accent-blue);
  background: var(--upload-hover-bg);
}

:global(:root:not(.dark)) .upload-area:hover {
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

.upload-actions {
  margin-top: 1.5rem;
  text-align: center;
}

.btn-submit {
  padding: 0.75rem 2rem;
  background: var(--btn-upload);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-submit:hover:not(:disabled) {
  background: var(--btn-upload-hover);
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

.error-message {
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

:global(:root:not(.dark)) .error-message {
  background: var(--upload-error-bg);
  border-color: var(--danger-hover);
}

.error-message svg {
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
</style>