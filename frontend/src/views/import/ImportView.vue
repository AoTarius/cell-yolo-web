<script setup lang="ts">
import '@/assets/styles/colors.css'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import { useToast } from '@/composables/useToast'
import Sidebar from '@/components/common/layout/Sidebar.vue'

const router = useRouter()
const userStore = useUserStore()
const { showToast } = useToast()

const selectedFile = ref<File | null>(null)
const isDragging = ref(false)
const isImporting = ref(false)
const importProgress = ref(0)
const importStatus = ref<'idle' | 'importing' | 'completed' | 'error'>('idle')
const importError = ref<string | null>(null)

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0 && target.files[0]) {
    selectedFile.value = target.files[0]
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0 && event.dataTransfer.files[0]) {
    const file = event.dataTransfer.files[0]
    // 检查文件是否是zip文件
    if (file.name.endsWith('.zip')) {
      selectedFile.value = file
    } else {
      showToast('请上传ZIP格式的数据包', 'error')
    }
  }
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
  isDragging.value = true
}

function handleDragLeave(event: DragEvent) {
  if (event.target === event.currentTarget) {
    isDragging.value = false
  }
}

function clearFile() {
  selectedFile.value = null
  importStatus.value = 'idle'
  importProgress.value = 0
  importError.value = null
}

async function handleImport() {
  if (!selectedFile.value) return

  try {
    isImporting.value = true
    importStatus.value = 'importing'
    importProgress.value = 0
    importError.value = null

    if (!userStore.currentUser?.username) {
      showToast('请先登录', 'error')
      return
    }

    // TODO: 实现导入逻辑
    // 这里暂时只模拟导入过程
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 200))
      importProgress.value = i
    }

    importStatus.value = 'completed'
    showToast('数据包导入成功！', 'success')

    // 3秒后跳转到主页
    setTimeout(() => {
      router.push('/')
    }, 3000)

  } catch (error: any) {
    importStatus.value = 'error'
    importError.value = error.message || '导入失败'
    showToast(importError.value || '导入失败', 'error')
  } finally {
    isImporting.value = false
  }
}
</script>

<template>
  <div class="import-view">
    <Sidebar />

    <main class="main-panel">
      <div class="import-container">
        <h2>导入分析数据</h2>
        <p class="import-description">上传ZIP格式的分析数据包，导入已完成的细胞跟踪分析结果</p>

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
            <p class="upload-text">拖拽ZIP数据包到此处，或点击选择</p>
            <p class="upload-hint">仅支持 ZIP 格式</p>
            <input
              type="file"
              accept=".zip"
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
              <p class="file-size">{{ selectedFile ? (selectedFile.size / 1024 / 1024).toFixed(2) : '0' }} MB</p>
            </div>
            <button class="btn-clear" @click="clearFile" :disabled="isImporting">
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

        <!-- 导入进度 -->
        <div v-if="importStatus === 'importing' || importStatus === 'completed'" class="upload-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${importProgress}%` }"></div>
          </div>
          <p class="progress-text">
            <span v-if="importStatus === 'importing'">导入中: {{ importProgress }}%</span>
            <span v-else>导入完成</span>
          </p>
        </div>

        <!-- 错误提示 -->
        <div v-if="importError" class="upload-error">
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
          <span>{{ importError }}</span>
          <button class="btn-close-error" @click="importError = null" aria-label="关闭错误提示">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>

        <div class="upload-actions">
          <button
            class="btn-submit"
            :disabled="!selectedFile || isImporting || importStatus === 'completed'"
            @click="handleImport"
          >
            {{
              importStatus === 'importing' ? '导入中...' :
              importStatus === 'completed' ? '导入完成' :
              '开始导入'
            }}
          </button>
        </div>

        <!-- 使用说明 -->
        <div class="usage-info">
          <h3>数据包说明</h3>
          <p>数据包应包含以下内容：</p>
          <ul>
            <li>result.json - 分析结果数据</li>
            <li>原始视频文件</li>
            <li>标注后的视频文件</li>
            <li>metadata.json - 任务元数据</li>
          </ul>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.import-view {
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

.import-container {
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

.import-description {
  text-align: center;
  color: var(--text-muted);
  margin: 0 0 2rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .import-description {
  color: var(--text-muted-light);
}

.upload-area {
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  padding: 3rem 2rem;
  background: var(--bg-card);
  transition: all 0.3s;
  position: relative;
  margin-bottom: 1.5rem;
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

.btn-clear:hover:not(:disabled) {
  background: var(--bg-input);
  border-color: var(--text-muted);
  color: var(--text-secondary);
}

:global(:root:not(.dark)) .btn-clear:hover:not(:disabled) {
  background: var(--bg-input-light);
  border-color: var(--text-disabled-light);
  color: var(--text-primary-light);
}

.btn-clear:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-clear svg {
  width: 16px;
  height: 16px;
}

.upload-progress {
  margin-bottom: 1.5rem;
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
  margin: 0;
  text-align: center;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .progress-text {
  color: var(--accent-blue);
}

.upload-error {
  margin-bottom: 1.5rem;
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
  margin-bottom: 2rem;
  text-align: center;
}

.btn-submit {
  padding: 0.75rem 2rem;
  background: var(--accent-blue);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-submit:hover:not(:disabled) {
  background: var(--accent-blue-hover);
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

.usage-info {
  padding: 1.5rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .usage-info {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

.usage-info h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.75rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .usage-info h3 {
  color: var(--text-primary-light);
}

.usage-info p {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin: 0 0 0.5rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .usage-info p {
  color: var(--text-primary-light);
}

.usage-info ul {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin: 0;
  padding-left: 1.5rem;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .usage-info ul {
  color: var(--text-primary-light);
}

.usage-info li {
  margin-bottom: 0.25rem;
}
</style>