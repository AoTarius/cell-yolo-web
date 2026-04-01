<script setup lang="ts">
import '@/assets/styles/colors.css'
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import ConfirmDialog from '@/components/common/dialog/ConfirmDialog.vue'
import { useToast } from '@/composables/useToast'
import { useAnalysisStore } from '@/stores/analysisStore'
import { useUserStore } from '@/stores/userStore'

const router = useRouter()
const { showToast } = useToast()
const analysisStore = useAnalysisStore()
const userStore = useUserStore()

// ==================== 模型管理相关 ====================
const selectedModelFile = ref<File | null>(null)
const isModelDragging = ref(false)
const isModelUploading = ref(false)
const modelErrorMessage = ref('')

const models = ref<Array<{ name: string; size_mb: number; path: string }>>([])
const isLoadingModels = ref(false)
const showModelDeleteDialog = ref(false)
const modelToDelete = ref<string | null>(null)
const isModelDeleting = ref(false)
const currentModelPath = ref('')

const showModelRenameDialog = ref(false)
const modelToRename = ref<string | null>(null)
const newModelName = ref('')
const isModelRenaming = ref(false)

// ==================== 模型管理函数 ====================
function handleModelFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0 && target.files[0]) {
    selectedModelFile.value = target.files[0]
    modelErrorMessage.value = ''
  }
}

function handleModelDrop(event: DragEvent) {
  isModelDragging.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0 && event.dataTransfer.files[0]) {
    selectedModelFile.value = event.dataTransfer.files[0]
    modelErrorMessage.value = ''
  }
}

async function handleModelUpload() {
  if (!selectedModelFile.value) return

  isModelUploading.value = true
  modelErrorMessage.value = ''

  try {
    if (!userStore.currentUser?.username) {
      modelErrorMessage.value = '请先登录后再上传模型'
      isModelUploading.value = false
      return
    }

    const username = userStore.currentUser.username

    const formData = new FormData()
    formData.append('model', selectedModelFile.value)
    formData.append('username', username)

    const response = await axios.post('/api/models/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    if (response.data.status === 'success') {
      showToast('模型上传成功！', 'success')
      await loadModels()
      selectedModelFile.value = null
    }
  } catch (error: any) {
    modelErrorMessage.value = error.response?.data?.error || '上传失败，请重试'
    showToast(error.response?.data?.error || '上传失败，请重试', 'error')
  } finally {
    isModelUploading.value = false
  }
}

function handleModelCancel() {
  selectedModelFile.value = null
  modelErrorMessage.value = ''
}

async function loadModels() {
  try {
    isLoadingModels.value = true

    if (!userStore.currentUser?.username) {
      models.value = []
      currentModelPath.value = ''
      return
    }

    const username = userStore.currentUser.username
    currentModelPath.value = userStore.currentUser.model_base_path || 'models'

    const response = await axios.get('/api/models/', { params: { username } })
    const modelList = response.data?.models
    const normalizedModels = Array.isArray(modelList) ? modelList : []
    models.value = normalizedModels.filter((model: { name: string }) => !isImportedTaskModelName(model.name))

  } catch (error) {
    console.error('加载模型列表失败:', error)
    models.value = []
  } finally {
    isLoadingModels.value = false
  }
}

function isImportedTaskModelName(name: string): boolean {
  const raw = (name || '').trim()
  if (!raw) return true
  const normalized = raw.replace(/\\/g, '/')
  return normalized.includes('/') || /^[a-zA-Z]:/.test(raw) || /\.pt$/i.test(raw)
}

function showModelDeleteConfirm(modelName: string) {
  modelToDelete.value = modelName
  showModelDeleteDialog.value = true
}

async function handleModelDeleteConfirm() {
  if (!modelToDelete.value) return

  isModelDeleting.value = true
  try {
    if (!userStore.currentUser?.username) {
      showToast('请先登录', 'error')
      return
    }

    const username = userStore.currentUser.username

    await axios.delete('/api/models/delete/', {
      params: { username, model_name: modelToDelete.value }
    })

    showToast('模型已删除', 'success')
    await loadModels()
  } catch (error: any) {
    console.error('删除模型失败:', error)
    showToast(error.response?.data?.error || '删除模型失败', 'error')
  } finally {
    isModelDeleting.value = false
    modelToDelete.value = null
    showModelDeleteDialog.value = false
  }
}

function handleModelDeleteCancel() {
  modelToDelete.value = null
  showModelDeleteDialog.value = false
}

function showModelRenameInputDialog(modelName: string) {
  modelToRename.value = modelName
  newModelName.value = modelName
  showModelRenameDialog.value = true
}

async function handleModelRenameConfirm() {
  if (!modelToRename.value || !newModelName.value) return

  isModelRenaming.value = true
  try {
    if (!userStore.currentUser?.username) {
      showToast('请先登录', 'error')
      return
    }

    const username = userStore.currentUser.username

    if (!newModelName.value.trim()) {
      showToast('新模型名称不能为空', 'error')
      return
    }

    if (newModelName.value === modelToRename.value) {
      showToast('新名称与原名称相同', 'warning')
      showModelRenameDialog.value = false
      return
    }

    await axios.post('/api/models/rename/', {
      username,
      old_model_name: modelToRename.value,
      new_model_name: newModelName.value
    })

    showToast('模型名称修改成功', 'success')
    await loadModels()
    await analysisStore.loadHistoryTasks()
  } catch (error: any) {
    console.error('修改模型名称失败:', error)
    showToast(error.response?.data?.error || '修改模型名称失败', 'error')
  } finally {
    isModelRenaming.value = false
    modelToRename.value = null
    newModelName.value = ''
    showModelRenameDialog.value = false
  }
}

function handleModelRenameCancel() {
  modelToRename.value = null
  newModelName.value = ''
  showModelRenameDialog.value = false
}

// ==================== 工具函数 ====================
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

function getDisplayModelName(modelName: string): string {
  const raw = (modelName || '').trim()
  if (!raw) return '未命名模型'

  const normalized = raw.replace(/\\/g, '/')
  const isPathLike = normalized.includes('/') || normalized.toLowerCase().endsWith('.pt')

  if (!isPathLike) {
    return raw
  }

  const fileName = normalized.split('/').pop() || raw
  const baseName = fileName.replace(/\.pt$/i, '') || fileName
  return `${baseName}（导入视频使用）`
}

// ==================== 生命周期 ====================
onMounted(async () => {
  await loadModels()
})

watch(
  () => userStore.currentUser?.username,
  async (username, oldUsername) => {
    if (!username || username === oldUsername) return
    await loadModels()
  }
)
</script>

<template>
  <div class="model-manage-wrapper">
    <div class="section-header">
      <h2>模型管理</h2>
    </div>

    <!-- 模型上传区域 -->
    <div class="upload-area-container">
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

      <div
        class="upload-area"
        :class="{ 'has-file': selectedModelFile }"
        @drop.prevent="handleModelDrop"
        @dragover.prevent="isModelDragging = true"
        @dragleave.prevent="isModelDragging = false"
      >
        <div v-if="!selectedModelFile" class="upload-placeholder">
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
            @change="handleModelFileSelect"
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
            <p class="file-name">{{ selectedModelFile?.name }}</p>
            <p class="file-size">{{ formatFileSize(selectedModelFile?.size || 0) }}</p>
          </div>
          <button class="btn-clear" @click="handleModelCancel">
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
        <button
          class="btn-submit"
          :disabled="!selectedModelFile || isModelUploading"
          @click="handleModelUpload"
        >
          {{ isModelUploading ? '上传中...' : '确认上传' }}
        </button>
      </div>

      <div v-if="modelErrorMessage" class="error-message">
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
        <span>{{ modelErrorMessage }}</span>
        <button class="btn-close-error" @click="modelErrorMessage = ''">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
    </div>

    <!-- 模型列表 -->
    <div class="list-container">
      <div class="list-header">
        <h3>我的模型</h3>
      </div>
      <div class="list-content">
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
        <div v-else class="item-list">
          <div
            v-for="model in models"
            :key="model.name"
            class="item"
          >
            <div class="item-icon model-icon">
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
            <div class="item-info">
              <p class="item-name">{{ getDisplayModelName(model.name) }}</p>
              <p class="item-meta">{{ formatFileSize(model.size_mb * 1024 * 1024) }}</p>
            </div>
            <div class="item-actions">
              <button
                class="btn-rename"
                @click="showModelRenameInputDialog(model.name)"
                :disabled="isModelRenaming"
                title="重命名"
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
                class="btn-delete"
                @click="showModelDeleteConfirm(model.name)"
                :disabled="isModelDeleting"
                title="删除"
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

    <!-- 模型删除确认对话框 -->
    <ConfirmDialog
      v-model:visible="showModelDeleteDialog"
      title="删除模型"
      :message="`确定要删除模型「${modelToDelete}」吗？此操作将删除模型文件和数据库记录，且无法恢复。`"
      type="danger"
      confirm-text="删除"
      cancel-text="取消"
      @confirm="handleModelDeleteConfirm"
      @cancel="handleModelDeleteCancel"
    />

    <!-- 模型改名对话框 -->
    <div v-if="showModelRenameDialog" class="rename-dialog-overlay" @click="handleModelRenameCancel">
      <div class="rename-dialog" @click.stop>
        <div class="rename-dialog-header">
          <h3>重命名模型</h3>
          <button class="btn-close-rename" @click="handleModelRenameCancel">
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
              :disabled="isModelRenaming"
            />
          </div>
        </div>
        <div class="rename-dialog-footer">
          <button
            class="btn-cancel-rename"
            @click="handleModelRenameCancel"
            :disabled="isModelRenaming"
          >
            取消
          </button>
          <button
            class="btn-confirm-rename"
            @click="handleModelRenameConfirm"
            :disabled="isModelRenaming || !newModelName.trim()"
          >
            {{ isModelRenaming ? '修改中...' : '确认修改' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.model-manage-wrapper {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  min-width: 0;
  padding-bottom: 2rem;
}

.section-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
}

:global(:root:not(.dark)) .section-header h2 {
  color: var(--text-primary-light);
}

.upload-area-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.path-info-box {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--alpha-badge);
  border: 2px dashed var(--border-color);
  border-radius: 6px;
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

.upload-area {
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  padding: 2rem 1.5rem;
  background: var(--bg-card);
  transition: all 0.3s;
  position: relative;
  min-height: 180px;
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
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.upload-icon {
  width: 48px;
  height: 48px;
  color: var(--text-muted);
  transition: color 0.3s;
}

:global(:root:not(.dark)) .upload-icon {
  color: var(--text-disabled-light);
}

.upload-text {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .upload-text {
  color: var(--text-primary-light);
}

.upload-hint {
  font-size: 0.875rem;
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
  width: 40px;
  height: 40px;
  color: var(--accent-blue);
  flex-shrink: 0;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 0.95rem;
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
  width: 28px;
  height: 28px;
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
  width: 14px;
  height: 14px;
}

.upload-actions {
  display: flex;
  justify-content: center;
}

.btn-submit {
  padding: 0.65rem 1.5rem;
  background: var(--btn-upload);
  color: white;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 0.95rem;
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
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.btn-close-error {
  width: 20px;
  height: 20px;
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
  width: 14px;
  height: 14px;
}

.list-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 300px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

:global(:root:not(.dark)) .list-container {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

.list-header {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
}

:global(:root:not(.dark)) .list-header {
  border-color: var(--border-color-light);
}

.list-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
}

:global(:root:not(.dark)) .list-header h3 {
  color: var(--text-primary-light);
}

.list-content {
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
  width: 48px;
  height: 48px;
  opacity: 0.5;
}

.item-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
}

.item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--bg-main);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  transition: all 0.2s;
}

:global(:root:not(.dark)) .item {
  background: var(--bg-main-light);
  border-color: var(--border-color-light);
}

.item:hover {
  border-color: var(--accent-blue);
}

.item-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-blue);
  background: var(--alpha-badge);
  border-radius: 6px;
}

.item-icon svg {
  width: 18px;
  height: 18px;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-weight: 500;
  color: var(--text-primary);
  margin: 0 0 0.25rem 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.95rem;
}

:global(:root:not(.dark)) .item-name {
  color: var(--text-primary-light);
}

.item-meta {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin: 0;
}

:global(:root:not(.dark)) .item-meta {
  color: var(--text-muted-light);
}

.item-actions {
  display: flex;
  gap: 0.35rem;
  align-items: center;
}

.btn-rename,
.btn-delete {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
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

:global(:root:not(.dark)) .btn-rename,
:global(:root:not(.dark)) .btn-delete {
  color: var(--text-muted-light);
}

.btn-rename:hover:not(:disabled) {
  color: var(--accent-blue);
}

.btn-delete:hover:not(:disabled) {
  color: var(--danger-light);
}

.btn-rename:disabled,
.btn-delete:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-rename svg,
.btn-delete svg {
  width: 14px;
  height: 14px;
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
  border: 1px solid var(--border-color);
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
  background: var(--accent-blue-hover);
}

.btn-cancel-rename:disabled,
.btn-confirm-rename:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
