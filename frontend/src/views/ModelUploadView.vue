<script setup lang="ts">
import '@/assets/styles/colors.css'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import Sidebar from '@/components/common/Sidebar.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { showToast } = useToast()

const selectedFile = ref<File | null>(null)
const isDragging = ref(false)
const isUploading = ref(false)
const errorMessage = ref('')

// 模型列表相关
const models = ref<Array<{ name: string; size_mb: number; path: string }>>([])
const isLoadingModels = ref(false)
const showDeleteDialog = ref(false)
const modelToDelete = ref<string | null>(null)
const isDeleting = ref(false)
const currentModelPath = ref('')

// 改名相关
const showRenameDialog = ref(false)
const modelToRename = ref<string | null>(null)
const newModelName = ref('')
const isRenaming = ref(false)

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
    // 获取当前用户名
    const currentUser = localStorage.getItem('currentUser')
    const username = currentUser ? JSON.parse(currentUser).username : ''

    if (!username) {
      errorMessage.value = '请先登录后再上传模型'
      isUploading.value = false
      return
    }

    const formData = new FormData()
    formData.append('model', selectedFile.value)
    formData.append('username', username)

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

// 加载模型列表
async function loadModels() {
  try {
    isLoadingModels.value = true
    const currentUser = localStorage.getItem('currentUser')
    const username = currentUser ? JSON.parse(currentUser).username : ''

    if (!username) {
      models.value = []
      currentModelPath.value = ''
      return
    }

    // 获取用户的model_base_path
    if (currentUser) {
      const userData = JSON.parse(currentUser)
      currentModelPath.value = userData.model_base_path || 'models'
    }

    const response = await axios.get('/api/models/', { params: { username } })
    models.value = response.data.models
  } catch (error) {
    console.error('加载模型列表失败:', error)
    models.value = []
  } finally {
    isLoadingModels.value = false
  }
}

// 显示删除确认对话框
function showDeleteConfirm(modelName: string) {
  modelToDelete.value = modelName
  showDeleteDialog.value = true
}

// 删除模型
async function handleDeleteConfirm() {
  if (!modelToDelete.value) return

  isDeleting.value = true
  try {
    const currentUser = localStorage.getItem('currentUser')
    const username = currentUser ? JSON.parse(currentUser).username : ''

    if (!username) {
      showToast('请先登录', 'error')
      return
    }

    await axios.delete('/api/models/delete/', {
      params: { username, model_name: modelToDelete.value }
    })

    showToast('模型已删除', 'success')
    // 重新加载模型列表
    await loadModels()
  } catch (error: any) {
    console.error('删除模型失败:', error)
    showToast(error.response?.data?.error || '删除模型失败', 'error')
  } finally {
    isDeleting.value = false
    modelToDelete.value = null
    showDeleteDialog.value = false
  }
}

function handleDeleteCancel() {
  modelToDelete.value = null
  showDeleteDialog.value = false
}

// 显示改名对话框
function showRenameInputDialog(modelName: string) {
  modelToRename.value = modelName
  newModelName.value = modelName
  showRenameDialog.value = true
}

// 确认改名
async function handleRenameConfirm() {
  if (!modelToRename.value || !newModelName.value) return

  isRenaming.value = true
  try {
    const currentUser = localStorage.getItem('currentUser')
    const username = currentUser ? JSON.parse(currentUser).username : ''

    if (!username) {
      showToast('请先登录', 'error')
      return
    }

    // 验证新名称
    if (!newModelName.value.trim()) {
      showToast('新模型名称不能为空', 'error')
      return
    }

    if (newModelName.value === modelToRename.value) {
      showToast('新名称与原名称相同', 'warning')
      showRenameDialog.value = false
      return
    }

    await axios.post('/api/models/rename/', {
      username,
      old_model_name: modelToRename.value,
      new_model_name: newModelName.value
    })

    showToast('模型名称修改成功', 'success')
    // 重新加载模型列表
    await loadModels()
  } catch (error: any) {
    console.error('修改模型名称失败:', error)
    showToast(error.response?.data?.error || '修改模型名称失败', 'error')
  } finally {
    isRenaming.value = false
    modelToRename.value = null
    newModelName.value = ''
    showRenameDialog.value = false
  }
}

// 取消改名
function handleRenameCancel() {
  modelToRename.value = null
  newModelName.value = ''
  showRenameDialog.value = false
}

// 格式化时间
function formatTime(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

// 组件挂载时加载模型列表
import { onMounted } from 'vue'
onMounted(() => {
  loadModels()
})
</script>

<template>

  <div class="model-upload-view">

    <Sidebar />

    <main class="main-panel">

      <div class="content-container">

        <!-- 左侧：上传区域 -->
        <div class="upload-section">

          <div class="upload-header">

            <h1>上传模型</h1>

            <p class="subtitle">上传 YOLOv8 模型文件 (.pt 格式)</p>

          </div>

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
              <p class="path-label">当前模型存储路径：</p>
              <p class="path-value">{{ currentModelPath || '未设置' }}</p>
            </div>
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

        <!-- 分隔线 -->
        <div class="divider"></div>

        <!-- 右侧：模型列表 -->
        <div class="models-section">
          <div class="models-header">
            <h2>我的模型</h2>
          </div>

          <div class="models-list">
            <div v-if="isLoadingModels" class="loading-message">
              加载中...
            </div>
            <div v-else-if="models.length === 0" class="empty-message">
              <svg
                class="empty-icon"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"
                ></path>
              </svg>
              <p>暂无模型</p>
            </div>
            <div v-else class="model-items">
              <div
                v-for="model in models"
                :key="model.name"
                class="model-item"
              >
                <div class="model-icon">
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
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    ></path>
                  </svg>
                </div>
                <div class="model-info">
                  <p class="model-name">{{ model.name }}</p>
                  <p class="model-size">{{ formatFileSize(model.size_mb * 1024 * 1024) }}</p>
                </div>
                <div class="model-actions">
                  <button
                    class="btn-rename-model"
                    @click="showRenameInputDialog(model.name)"
                    :disabled="isRenaming"
                    title="重命名模型"
                  >
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
                        d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                      ></path>
                    </svg>
                  </button>
                  <button
                    class="btn-delete-model"
                    @click="showDeleteConfirm(model.name)"
                    :disabled="isDeleting"
                    title="删除模型"
                  >
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
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      ></path>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 删除确认对话框 -->
    <ConfirmDialog
      v-model:visible="showDeleteDialog"
      title="删除模型"
      :message="`确定要删除模型「${modelToDelete}」吗？此操作将删除模型文件和数据库记录，且无法恢复。`"
      type="danger"
      confirm-text="删除"
      cancel-text="取消"
      @confirm="handleDeleteConfirm"
      @cancel="handleDeleteCancel"
    />

    <!-- 改名对话框 -->
    <div v-if="showRenameDialog" class="rename-dialog-overlay" @click="handleRenameCancel">
      <div class="rename-dialog" @click.stop>
        <div class="rename-dialog-header">
          <h3>重命名模型</h3>
          <button class="btn-close-rename" @click="handleRenameCancel">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        <div class="rename-dialog-body">
          <div class="rename-field">
            <label class="rename-label">原名称</label>
            <input
              type="text"
              class="rename-input"
              :value="modelToRename"
              disabled
            />
          </div>
          <div class="rename-field">
            <label class="rename-label">新名称</label>
            <input
              type="text"
              class="rename-input"
              v-model="newModelName"
              placeholder="请输入新的模型名称"
              :disabled="isRenaming"
            />
          </div>
        </div>
        <div class="rename-dialog-footer">
          <button
            class="btn-cancel-rename"
            @click="handleRenameCancel"
            :disabled="isRenaming"
          >
            取消
          </button>
          <button
            class="btn-confirm-rename"
            @click="handleRenameConfirm"
            :disabled="isRenaming || !newModelName.trim()"
          >
            {{ isRenaming ? '修改中...' : '确认修改' }}
          </button>
        </div>
      </div>
    </div>
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
}

.content-container {
  flex: 1;
  display: grid;
  grid-template-columns: 2fr auto 1fr;
  gap: 1.5rem;
  padding: 2rem;
  overflow: hidden;
}

.upload-section {
  display: flex;
  flex-direction: column;
  min-height: 0;
  justify-content: center;
}

.upload-container {
  max-width: 600px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.divider {
  width: 1px;
  background: var(--border-color);
  height: 100%;
  align-self: stretch;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .divider {
  background: var(--border-color-light);
}

.models-section {
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding-top: 1rem;
}

.models-header {
  margin-bottom: 1.5rem;
}

.models-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
}

:global(:root:not(.dark)) .models-header h2 {
  color: var(--text-primary-light);
}

.models-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.loading-message,
.empty-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: var(--text-muted);
  gap: 1rem;
}

:global(:root:not(.dark)) .loading-message,
:global(:root:not(.dark)) .empty-message {
  color: var(--text-muted-light);
}

.empty-icon {
  width: 64px;
  height: 64px;
  opacity: 0.5;
}

.model-items {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.model-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  transition: all 0.2s;
}

:global(:root:not(.dark)) .model-item {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

.model-item:hover {
  border-color: var(--accent-blue);
}

.model-item .model-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-blue);
  background: var(--alpha-badge);
  border-radius: 6px;
}

.model-item .model-icon svg {
  width: 20px;
  height: 20px;
}

.model-info {
  flex: 1;
  min-width: 0;
}

.model-info .model-name {
  font-weight: 500;
  color: var(--text-primary);
  margin: 0 0 0.25rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:global(:root:not(.dark)) .model-info .model-name {
  color: var(--text-primary-light);
}

.model-info .model-size {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0;
}

:global(:root:not(.dark)) .model-info .model-size {
  color: var(--text-muted-light);
}

.btn-delete-model {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

:global(:root:not(.dark)) .btn-delete-model {
  color: var(--text-muted-light);
}

.btn-delete-model:hover:not(:disabled) {
  background: var(--danger-bg);
  color: var(--danger-light);
}

.btn-delete-model:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-delete-model svg {
  width: 16px;
  height: 16px;
}

.model-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.btn-rename-model {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

:global(:root:not(.dark)) .btn-rename-model {
  color: var(--text-muted-light);
}

.btn-rename-model:hover:not(:disabled) {
  background: var(--accent-blue);
  color: white;
}

.btn-rename-model:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-rename-model svg {
  width: 16px;
  height: 16px;
}

.upload-header {
  text-align: center;
  margin-bottom: 1.5rem;
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

.path-info-box {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--alpha-badge);
  border: 1px solid var(--border-color);
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

/* 改名对话框样式 */
.rename-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.rename-dialog {
  background: var(--bg-card);
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  min-width: 400px;
  max-width: 500px;
  animation: slideUp 0.3s ease;
}

:global(:root:not(.dark)) .rename-dialog {
  background: var(--bg-card-light);
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.rename-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

:global(:root:not(.dark)) .rename-dialog-header {
  border-color: var(--border-color-light);
}

.rename-dialog-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

:global(:root:not(.dark)) .rename-dialog-header h3 {
  color: var(--text-primary-light);
}

.btn-close-rename {
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

:global(:root:not(.dark)) .btn-close-rename {
  color: var(--text-muted-light);
}

.btn-close-rename:hover {
  background: var(--bg-input);
  color: var(--text-secondary);
}

:global(:root:not(.dark)) .btn-close-rename:hover {
  background: var(--bg-input-light);
  color: var(--text-primary-light);
}

.btn-close-rename svg {
  width: 20px;
  height: 20px;
}

.rename-dialog-body {
  padding: 1.5rem;
}

.rename-field {
  margin-bottom: 1rem;
}

.rename-field:last-child {
  margin-bottom: 0;
}

.rename-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

:global(:root:not(.dark)) .rename-label {
  color: var(--text-primary-light);
}

.rename-input {
  width: 100%;
  padding: 0.75rem 1rem;
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 0.875rem;
  transition: all 0.2s;
  outline: none;
}

:global(:root:not(.dark)) .rename-input {
  background: var(--bg-input-light);
  border-color: var(--border-color-light);
  color: var(--text-primary-light);
}

.rename-input:hover:not(:disabled) {
  border-color: var(--text-muted);
}

:global(:root:not(.dark)) .rename-input:hover:not(:disabled) {
  border-color: var(--text-disabled-light);
}

.rename-input:focus {
  border-color: var(--accent-blue);
}

.rename-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: var(--bg-main);
}

:global(:root:not(.dark)) .rename-input:disabled {
  background: var(--bg-main-light);
}

.rename-dialog-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1.5rem;
  border-top: 1px solid var(--border-color);
  justify-content: flex-end;
}

:global(:root:not(.dark)) .rename-dialog-footer {
  border-color: var(--border-color-light);
}

.btn-cancel-rename,
.btn-confirm-rename {
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-cancel-rename {
  background: var(--bg-input);
  color: var(--text-secondary);
}

:global(:root:not(.dark)) .btn-cancel-rename {
  background: var(--bg-input-light);
  color: var(--text-primary-light);
}

.btn-cancel-rename:hover:not(:disabled) {
  background: var(--bg-hover);
}

:global(:root:not(.dark)) .btn-cancel-rename:hover:not(:disabled) {
  background: var(--border-color-light);
}

.btn-confirm-rename {
  background: var(--accent-blue);
  color: white;
}

.btn-confirm-rename:hover:not(:disabled) {
  background: var(--btn-upload-hover);
}

.btn-cancel-rename:disabled,
.btn-confirm-rename:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>