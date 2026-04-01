<script setup lang="ts">
import '@/assets/styles/colors.css'
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import ConfirmDialog from '@/components/common/dialog/ConfirmDialog.vue'
import { useToast } from '@/composables/useToast'
import { useUserStore } from '@/stores/userStore'

const { showToast } = useToast()
const userStore = useUserStore()

// ==================== 视频管理相关 ====================
const selectedVideoFile = ref<File | null>(null)
const isVideoDragging = ref(false)
const isVideoUploading = ref(false)
const videoErrorMessage = ref('')

const videos = ref<Array<{ id: number; name: string; size_mb: number; path: string; total_frames: number; duration: number }>>([])
const isLoadingVideos = ref(false)
const showVideoDeleteDialog = ref(false)
const videoToDelete = ref<{ id: number; name: string } | null>(null)
const isVideoDeleting = ref(false)
const currentVideoPath = ref('')

const showVideoRenameDialog = ref(false)
const videoToRename = ref<{ id: number; name: string } | null>(null)
const newVideoName = ref('')
const isVideoRenaming = ref(false)

// ==================== 视频管理函数 ====================
function handleVideoFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0 && target.files[0]) {
    selectedVideoFile.value = target.files[0]
    videoErrorMessage.value = ''
  }
}

function handleVideoDrop(event: DragEvent) {
  isVideoDragging.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0 && event.dataTransfer.files[0]) {
    selectedVideoFile.value = event.dataTransfer.files[0]
    videoErrorMessage.value = ''
  }
}

async function handleVideoUpload() {
  if (!selectedVideoFile.value) return

  isVideoUploading.value = true
  videoErrorMessage.value = ''

  try {
    if (!userStore.currentUser?.username) {
      videoErrorMessage.value = '请先登录后再上传视频'
      isVideoUploading.value = false
      return
    }

    const username = userStore.currentUser.username

    const formData = new FormData()
    formData.append('video', selectedVideoFile.value)
    formData.append('username', username)

    const response = await axios.post('/api/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    if (response.data.task_id) {
      showToast('视频上传成功！', 'success')
      await loadVideos()
      selectedVideoFile.value = null
    }
  } catch (error: any) {
    videoErrorMessage.value = error.response?.data?.error || '上传失败，请重试'
    showToast(error.response?.data?.error || '上传失败，请重试', 'error')
  } finally {
    isVideoUploading.value = false
  }
}

function handleVideoCancel() {
  selectedVideoFile.value = null
  videoErrorMessage.value = ''
}

async function loadVideos() {
  try {
    isLoadingVideos.value = true

    if (!userStore.currentUser?.username) {
      videos.value = []
      currentVideoPath.value = ''
      return
    }

    const username = userStore.currentUser.username
    currentVideoPath.value = userStore.currentUser.output_base_path ? `${userStore.currentUser.output_base_path}/videos` : 'videos'

    const response = await axios.get('/api/videos/', { params: { username } })
    const videoList = response.data?.videos
    const normalizedVideos = Array.isArray(videoList) ? videoList : []
    videos.value = normalizedVideos

  } catch (error) {
    console.error('加载视频列表失败:', error)
    videos.value = []
  } finally {
    isLoadingVideos.value = false
  }
}

function showVideoDeleteConfirm(videoId: number, videoName: string) {
  videoToDelete.value = { id: videoId, name: videoName }
  showVideoDeleteDialog.value = true
}

async function handleVideoDeleteConfirm() {
  if (!videoToDelete.value) return

  isVideoDeleting.value = true
  try {
    if (!userStore.currentUser?.username) {
      showToast('请先登录', 'error')
      return
    }

    const username = userStore.currentUser.username

    await axios.delete('/api/videos/delete/', {
      params: { username, video_id: videoToDelete.value.id }
    })

    showToast('视频已删除', 'success')
    await loadVideos()
  } catch (error: any) {
    console.error('删除视频失败:', error)
    showToast(error.response?.data?.error || '删除视频失败', 'error')
  } finally {
    isVideoDeleting.value = false
    videoToDelete.value = null
    showVideoDeleteDialog.value = false
  }
}

function handleVideoDeleteCancel() {
  videoToDelete.value = null
  showVideoDeleteDialog.value = false
}

function showVideoRenameInputDialog(videoId: number, videoName: string) {
  videoToRename.value = { id: videoId, name: videoName }
  newVideoName.value = videoName
  showVideoRenameDialog.value = true
}

async function handleVideoRenameConfirm() {
  if (!videoToRename.value || !newVideoName.value) return

  isVideoRenaming.value = true
  try {
    if (!userStore.currentUser?.username) {
      showToast('请先登录', 'error')
      return
    }

    const username = userStore.currentUser.username

    if (!newVideoName.value.trim()) {
      showToast('新视频名称不能为空', 'error')
      return
    }

    if (newVideoName.value === videoToRename.value.name) {
      showToast('新名称与原名称相同', 'warning')
      showVideoRenameDialog.value = false
      return
    }

    await axios.post('/api/videos/rename/', {
      username,
      video_id: videoToRename.value.id,
      new_video_name: newVideoName.value
    })

    showToast('视频名称修改成功', 'success')
    await loadVideos()
  } catch (error: any) {
    console.error('修改视频名称失败:', error)
    showToast(error.response?.data?.error || '修改视频名称失败', 'error')
  } finally {
    isVideoRenaming.value = false
    videoToRename.value = null
    newVideoName.value = ''
    showVideoRenameDialog.value = false
  }
}

function handleVideoRenameCancel() {
  videoToRename.value = null
  newVideoName.value = ''
  showVideoRenameDialog.value = false
}

// ==================== 工具函数 ====================
function formatDuration(seconds: number): string {
  if (!seconds || seconds <= 0) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

// ==================== 生命周期 ====================
onMounted(async () => {
  await loadVideos()
})

watch(
  () => userStore.currentUser?.username,
  async (username, oldUsername) => {
    if (!username || username === oldUsername) return
    await loadVideos()
  }
)
</script>

<template>
  <div class="video-manage-wrapper">
    <div class="section-header">
      <h2>视频管理</h2>
    </div>

    <!-- 视频上传区域 -->
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
          <p class="path-label">当前视频存储路径：</p>
          <p class="path-value">{{ currentVideoPath || '未设置' }}</p>
        </div>
      </div>

      <div
        class="upload-area"
        :class="{ 'has-file': selectedVideoFile }"
        @drop.prevent="handleVideoDrop"
        @dragover.prevent="isVideoDragging = true"
        @dragleave.prevent="isVideoDragging = false"
      >
        <div v-if="!selectedVideoFile" class="upload-placeholder">
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
          <p class="upload-hint">支持 .mp4, .avi, .mov, .mkv 格式</p>
          <input
            type="file"
            accept=".mp4,.avi,.mov,.mkv"
            class="file-input"
            @change="handleVideoFileSelect"
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
            <p class="file-name">{{ selectedVideoFile?.name }}</p>
            <p class="file-size">{{ formatFileSize(selectedVideoFile?.size || 0) }}</p>
          </div>
          <button class="btn-clear" @click="handleVideoCancel">
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
          :disabled="!selectedVideoFile || isVideoUploading"
          @click="handleVideoUpload"
        >
          {{ isVideoUploading ? '上传中...' : '确认上传' }}
        </button>
      </div>

      <div v-if="videoErrorMessage" class="error-message">
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
        <span>{{ videoErrorMessage }}</span>
        <button class="btn-close-error" @click="videoErrorMessage = ''">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
    </div>

    <!-- 视频列表 -->
    <div class="list-container">
      <div class="list-header">
        <h3>我的视频</h3>
      </div>
      <div class="list-content">
        <div v-if="isLoadingVideos" class="loading-message">
          加载中...
        </div>
        <div v-else-if="videos.length === 0" class="empty-message">
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
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
            ></path>
          </svg>
          <p>暂无视频</p>
        </div>
        <div v-else class="item-list">
          <div
            v-for="video in videos"
            :key="video.id"
            class="item"
          >
            <div class="item-icon video-icon">
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
                  d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                ></path>
              </svg>
            </div>
            <div class="item-info">
              <p class="item-name">{{ video.name }}</p>
              <p class="item-meta">{{ formatFileSize(video.size_mb * 1024 * 1024) }} | {{ formatDuration(video.duration) }} | {{ video.total_frames }} 帧</p>
            </div>
            <div class="item-actions">
              <button
                class="btn-rename"
                @click="showVideoRenameInputDialog(video.id, video.name)"
                :disabled="isVideoRenaming"
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
                @click="showVideoDeleteConfirm(video.id, video.name)"
                :disabled="isVideoDeleting"
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

    <!-- 视频删除确认对话框 -->
    <ConfirmDialog
      v-model:visible="showVideoDeleteDialog"
      title="删除视频"
      :message="`确定要删除视频「${videoToDelete?.name}」吗？此操作将删除视频文件和数据库记录，且无法恢复。`"
      type="danger"
      confirm-text="删除"
      cancel-text="取消"
      @confirm="handleVideoDeleteConfirm"
      @cancel="handleVideoDeleteCancel"
    />

    <!-- 视频改名对话框 -->
    <div v-if="showVideoRenameDialog" class="rename-dialog-overlay" @click="handleVideoRenameCancel">
      <div class="rename-dialog" @click.stop>
        <div class="rename-dialog-header">
          <h3>重命名视频</h3>
          <button class="btn-close-rename" @click="handleVideoRenameCancel">
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
              :value="videoToRename?.name"
              disabled
            />
          </div>
          <div class="rename-field">
            <label class="rename-label">新名称</label>
            <input
              type="text"
              class="rename-input"
              v-model="newVideoName"
              placeholder="请输入新的视频名称"
              :disabled="isVideoRenaming"
            />
          </div>
        </div>
        <div class="rename-dialog-footer">
          <button
            class="btn-cancel-rename"
            @click="handleVideoRenameCancel"
            :disabled="isVideoRenaming"
          >
            取消
          </button>
          <button
            class="btn-confirm-rename"
            @click="handleVideoRenameConfirm"
            :disabled="isVideoRenaming || !newVideoName.trim()"
          >
            {{ isVideoRenaming ? '修改中...' : '确认修改' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.video-manage-wrapper {
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