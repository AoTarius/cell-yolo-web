<script setup lang="ts">
import { ref, onMounted, nextTick, computed, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAnalysisStore, type AnalysisRecord } from '@/stores/analysisStore'
import { useUserStore } from '@/stores/userStore'
import { useToast } from '@/composables/useToast'
import { authApi } from '@/api/authApi'
import ConfirmDialog from './ConfirmDialog.vue'
import SettingsDialog from './SettingsDialog.vue'
import HistoryFilter, { type FilterCondition } from './HistoryFilter.vue'
import HistorySort, { type SortCondition } from './HistorySort.vue'
import axios from 'axios'
import '@/assets/styles/colors.css'

const props = defineProps<{
  compareMode?: boolean
}>()

const emit = defineEmits<{
  selectRecord: [record: AnalysisRecord]
}>()

const store = useAnalysisStore()
const userStore = useUserStore()
const router = useRouter()
const route = useRoute()
const { showToast } = useToast()

// 连接状态
const isConnected = ref(true)
let connectionCheckInterval: number | null = null

// 检查后端连接状态
async function checkConnection() {
  try {
    // 尝试调用一个简单的 API 来检查连接
    await axios.get('/api/tasks/', { timeout: 3000 })
    isConnected.value = true
  } catch (error) {
    isConnected.value = false
  }
}

// 计算用户头像首字母
const avatarInitials = computed(() => {
  try {
    const name = String(userStore.currentUser?.username || '').trim()
    if (!name) return ''
    const parts = name.split(/\s|[._-]+/).filter(Boolean)
    if (parts.length === 0) return name.slice(0, 2).toUpperCase()
    if (parts.length === 1) return (parts[0]?.slice(0, 2) || '').toUpperCase()
    return ((parts[0]?.[0] || '') + (parts[1]?.[0] || '')).toUpperCase()
  } catch (e) {
    return ''
  }
})

// 组件挂载时加载历史记录
onMounted(async () => {
  // 只有已登录用户才加载任务列表
  if (userStore.currentUser) {
    await store.loadHistoryTasks()
  }

  // 如果已登录，根据用户的 dark_mode 设置主题；否则从 localStorage 读取
  if (userStore.currentUser && userStore.currentUser.dark_mode !== undefined) {
    isDark.value = userStore.currentUser.dark_mode
  } else {
    const savedTheme = localStorage.getItem('theme')
    isDark.value = savedTheme !== 'light'
  }
  applyTheme()

  // 启动连接状态检查
  await checkConnection()
  connectionCheckInterval = window.setInterval(checkConnection, 10000) // 每10秒检查一次
})

// 组件卸载时清理定时器
onUnmounted(() => {
  if (connectionCheckInterval !== null) {
    clearInterval(connectionCheckInterval)
    connectionCheckInterval = null
  }
})

const showDeleteDialog = ref(false)
const taskToDelete = ref<string | null>(null)
const showRenameDialog = ref(false)
const taskToRename = ref<string | null>(null)
const newTaskName = ref('')
const isRenaming = ref(false)
const showSettingsDialog = ref(false)
const modelPath = ref('')
const outputPath = ref('')
const showFilterDialog = ref(false)
const isFiltering = ref(false)
const filteredRecords = ref<AnalysisRecord[]>([])
const showSortDialog = ref(false)
const sortConditions = ref<SortCondition[]>([
  {
    id: '1',
    field: 'createdAt',
    direction: 'desc'
  }
])

// 主题切换
const isDark = ref(true)

// Sidebar 折叠状态
const isCollapsed = ref(false)

// 切换 sidebar 折叠状态
function toggleSidebar() {
  isCollapsed.value = !isCollapsed.value
}

// 应用主题
function applyTheme() {
  if (isDark.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

// 切换主题
async function toggleTheme() {
  const newMode = !isDark.value
  isDark.value = newMode

  // 更新本地状态和 localStorage
  if (newMode) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }

  // 如果已登录，更新数据库
  if (userStore.currentUser) {
    try {
      await authApi.updateUserDarkMode(userStore.currentUser.username, newMode)
      // 更新 store 中的用户信息
      userStore.currentUser.dark_mode = newMode
      localStorage.setItem('currentUser', JSON.stringify(userStore.currentUser))
    } catch (error) {
      console.error('更新用户颜色模式失败:', error)
      // 不影响本地切换，只记录错误
    }
  }
}

function formatDate(date: Date) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function handleRecordClick(record: AnalysisRecord) {
  // 如果在对比模式，触发 select-record 事件
  if (props.compareMode) {
    emit('selectRecord', record)
    return
  }

  // 如果不在主页，先跳转回主页
  if (route.path !== '/') {
    router.push('/').then(() => {
      store.selectRecord(record.task_id)
      // 等待 DOM 更新后滚动到顶部
      nextTick(() => {
        scrollToTop()
      })
    })
  } else {
    store.selectRecord(record.task_id)
    // 等待 DOM 更新后滚动到顶部
    nextTick(() => {
      scrollToTop()
    })
  }
}

// 滚动到顶部
function scrollToTop() {
  const resultContent = document.querySelector('.result-content')
  if (resultContent) {
    resultContent.scrollTop = 0
  }
}

function showDeleteConfirm(taskId: string, event: Event) {
  event.stopPropagation() // 阻止触发记录选择
  taskToDelete.value = taskId
  showDeleteDialog.value = true
}

async function handleDeleteConfirm() {
  if (taskToDelete.value) {
    try {
      await store.deleteRecord(taskToDelete.value)
      showToast('任务已成功删除', 'success')
    } catch (error) {
      console.error('删除失败:', error)
      showToast('删除任务失败', 'error')
    } finally {
      taskToDelete.value = null
    }
  }
}

function handleDeleteCancel() {
  taskToDelete.value = null
}

// 显示重命名对话框
function showRenameInputDialog(taskId: string, event: Event) {
  event.stopPropagation() // 阻止触发记录选择
  taskToRename.value = taskId
  const record = store.records.find(r => r.task_id === taskId)
  newTaskName.value = record?.task_name || record?.video_name || taskId
  showRenameDialog.value = true
}

// 确认重命名
async function handleRenameConfirm() {
  if (!taskToRename.value || !newTaskName.value) return

  isRenaming.value = true
  try {
    if (!userStore.currentUser?.username) {
      showToast('请先登录', 'error')
      return
    }

    const username = userStore.currentUser.username

    // 验证新名称
    if (!newTaskName.value.trim()) {
      showToast('新任务名称不能为空', 'error')
      return
    }

    const record = store.records.find(r => r.task_id === taskToRename.value)
    if (newTaskName.value === (record?.task_name || record?.video_name)) {
      showToast('新名称与原名称相同', 'warning')
      showRenameDialog.value = false
      return
    }

    await axios.post('/api/tasks/rename/', {
      username,
      task_id: taskToRename.value,
      new_task_name: newTaskName.value
    })

    showToast('任务名称修改成功', 'success')
    // 重新加载任务列表以更新显示
    await store.loadHistoryTasks()
    // 重置筛选状态以显示所有记录
    isFiltering.value = false
    filteredRecords.value = []
  } catch (error: any) {
    console.error('修改任务名称失败:', error)
    showToast(error.response?.data?.error || '修改任务名称失败', 'error')
  } finally {
    isRenaming.value = false
    taskToRename.value = null
    newTaskName.value = ''
    showRenameDialog.value = false
  }
}

// 取消重命名
function handleRenameCancel() {
  taskToRename.value = null
  newTaskName.value = ''
  showRenameDialog.value = false
}

function handleNewAnalysis() {
  // 如果不在主页，先跳转回主页
  if (route.path !== '/') {
    router.push('/').then(() => {
      store.createNewAnalysis()
    })
  } else {
    store.createNewAnalysis()
  }
}

function handleModelUpload() {
  // 清除历史记录选中状态
  store.clearSelection()
  router.push('/model-upload')
}

function handleCompare() {
  // 清除历史记录选中状态
  store.clearSelection()

  // 如果当前在对比页面，则返回主页；否则进入对比页面
  if (route.path === '/compare') {
    router.push('/')
  } else {
    router.push('/compare')
  }
}

function handleExport() {
  showToast('备用功能开发中...', 'info')
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

function handleSettings() {
  // 从 userStore 中读取用户的路径配置
  if (userStore.currentUser) {
    modelPath.value = userStore.currentUser.model_base_path || 'models'
    outputPath.value = userStore.currentUser.output_base_path || 'output'
  }
  showSettingsDialog.value = true
}

async function handleSettingsSave(savedModelPath: string, savedOutputPath: string) {
  modelPath.value = savedModelPath
  outputPath.value = savedOutputPath

  // 如果已登录，更新数据库
  if (userStore.currentUser) {
    try {
      await authApi.updateUserPaths(
        userStore.currentUser.username,
        savedModelPath,
        savedOutputPath
      )

      // 更新 store 中的用户信息
      userStore.currentUser.model_base_path = savedModelPath
      userStore.currentUser.output_base_path = savedOutputPath
      localStorage.setItem('currentUser', JSON.stringify(userStore.currentUser))

      showToast('设置已保存', 'success')
    } catch (error) {
      console.error('更新路径配置失败:', error)
      showToast('保存设置失败', 'error')
    }
  } else {
    showToast('设置已保存', 'success')
  }
}

function handleBrowseModel() {
  // TODO: 实现文件夹选择功能
  // 在 Web 环境中，可以使用 Electron 的 API 或文件选择器
  showToast('文件夹选择功能待实现', 'info')
}

function handleBrowseOutput() {
  // TODO: 实现文件夹选择功能
  showToast('文件夹选择功能待实现', 'info')
}

// 打开筛选器
function openFilter() {
  showFilterDialog.value = true
}

// 打开排序器
function openSort() {
  showSortDialog.value = true
}

// 应用排序
function handleSort(conditions: SortCondition[]) {
  sortConditions.value = conditions
  // 更新 store 中的排序条件
  store.setSortConditions(conditions)
  // 重新加载任务列表以应用排序
  store.loadHistoryTasks()
  showToast('排序已应用', 'success')
}

// 应用筛选
function handleFilter(conditions: FilterCondition[]) {
  if (conditions.length === 0) {
    isFiltering.value = false
    filteredRecords.value = []
    return
  }

  isFiltering.value = true
  filteredRecords.value = store.records.filter(record => {
    return conditions.every(condition => {
      const fieldValue = getFieldValue(record, condition.field)

      switch (condition.operator) {
        case 'equals':
          return fieldValue === condition.value
        case 'notEquals':
          return fieldValue !== condition.value
        case 'contains':
          return String(fieldValue).toLowerCase().includes(String(condition.value).toLowerCase())
        case 'notContains':
          return !String(fieldValue).toLowerCase().includes(String(condition.value).toLowerCase())
        case 'greaterThan':
          return Number(fieldValue) > Number(condition.value)
        case 'lessThan':
          return Number(fieldValue) < Number(condition.value)
        case 'greaterThanOrEqual':
          return Number(fieldValue) >= Number(condition.value)
        case 'lessThanOrEqual':
          return Number(fieldValue) <= Number(condition.value)
        case 'between':
          if (Array.isArray(condition.value) && condition.value.length === 2) {
            const numValue = Number(fieldValue)
            return numValue >= Number(condition.value[0]) && numValue <= Number(condition.value[1])
          }
          return false
        default:
          return true
      }
    })
  })

  showToast(`已筛选出 ${filteredRecords.value.length} 条记录`, 'success')
}

// 获取记录字段的值
function getFieldValue(record: AnalysisRecord, field: string): string | number {
  switch (field) {
    case 'status':
      return record.status
    case 'createTime':
      return new Date(record.start_time).getTime()
    case 'modelType':
      return record.model_name || record.result?.model_name || ''
    case 'fileName':
      return record.task_name || record.video_name
    case 'cellCount':
      return record.result?.cell_count || 0
    default:
      return ''
  }
}

// 计算显示的记录列表（应用筛选）
const displayRecords = computed(() => {
  if (isFiltering.value) {
    return filteredRecords.value
  }
  return store.records
})

// 判断是否应用了有效排序（非默认排序）
const isSorting = computed(() => {
  // 默认排序是单个条件：created_at desc
  const defaultSort = [{ field: 'createdAt', direction: 'desc' }]

  // 如果排序条件数量不是1，或者是多个条件，肯定是有效排序
  if (sortConditions.value.length !== 1) {
    return sortConditions.value.length > 0
  }

  // 如果是单个条件，检查是否与默认排序不同
  const current = sortConditions.value[0]!
  return current.field !== 'createdAt' || current.direction !== 'desc'
})
</script>

<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <div class="header-top">
        <h1 v-if="!isCollapsed">细胞跟踪分析</h1>
        <button class="btn-collapse" @click="toggleSidebar" :title="isCollapsed ? '展开侧边栏' : '收起侧边栏'">
          <svg v-if="!isCollapsed" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"></path>
          </svg>
          <svg v-else fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7"></path>
          </svg>
        </button>
      </div>
      <template v-if="!isCollapsed">
        <div class="action-buttons-grid">
          <button class="btn-new-analysis" @click="handleNewAnalysis">
            <span class="icon">+</span>
            新建分析
          </button>
          <button class="btn-upload-model" @click="handleModelUpload">
            <span class="icon">⚙</span>
            管理模型
          </button>
          <button class="btn-compare" @click="handleCompare">
            <span class="icon">⚖</span>
            对比分析
          </button>
          <button class="btn-export" @click="handleExport">
            <span class="icon">↓</span>
            备用按钮
          </button>
        </div>
      </template>
    </div>

    <div v-if="!isCollapsed" class="sidebar-content">
      <div class="section-header">
        <h2 class="section-title">历史记录</h2>
        <div class="section-actions">
          <button class="btn-sort" :class="{ active: isSorting }" @click="openSort" title="排序历史记录">
            <svg
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
                class="sort-icon"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12"
                ></path>
              </svg>
          </button>
          <button class="btn-filter" :class="{ active: isFiltering }" @click="openFilter" title="筛选历史记录">
            <svg
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
                class="filter-icon"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                ></path>
              </svg>
          </button>
        </div>
      </div>
      <div class="records-list">
        <div
          v-for="record in displayRecords"
          :key="record.task_id"
          class="record-item"
          :class="{ active: store.selectedId === record.task_id }"
          @click="handleRecordClick(record)"
        >
          <div class="record-header">
            <span class="record-name">{{ record.task_name || record.video_name }}</span>
            <div class="status-indicator">
              <span class="status-dot" :class="`dot-${record.status}`"></span>
              <span class="record-status" :class="`status-${record.status}`">
                {{
                  record.status === 'completed'
                    ? '已完成'
                    : record.status === 'processing'
                      ? '分析中'
                      : record.status === 'failed'
                        ? '失败'
                        : record.status
                }}
              </span>
            </div>
          </div>
          <div class="record-video">任务ID: {{ record.task_id }}</div>
          <div class="record-footer">
            <span class="record-time">{{ formatDate(record.start_time) }}</span>
            <span class="model-badge">
              <svg
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
                class="model-icon"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
                ></path>
              </svg>
              {{ record.model_name || record.result?.model_name || 'N/A' }}
            </span>
            <div class="task-actions">
              <button
                class="btn-rename"
                @click="showRenameInputDialog(record.task_id, $event)"
                title="重命名任务"
                :disabled="record.status === 'processing' || isRenaming"
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
                @click="showDeleteConfirm(record.task_id, $event)"
                title="删除记录"
                :disabled="record.status === 'processing'"
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

    <!-- 删除确认对话框 -->
    <ConfirmDialog
      v-model:visible="showDeleteDialog"
      title="删除记录"
      message="确定要删除这条记录吗？此操作将删除所有相关文件（包括原始视频、处理结果等），且无法恢复。"
      type="danger"
      confirm-text="删除"
      cancel-text="取消"
      @confirm="handleDeleteConfirm"
      @cancel="handleDeleteCancel"
    />

    <!-- 重命名对话框 -->
    <div v-if="showRenameDialog" class="rename-dialog-overlay" @click="handleRenameCancel">
      <div class="rename-dialog" @click.stop>
        <div class="rename-dialog-header">
          <h3>重命名任务</h3>
          <button class="btn-close-rename" @click="handleRenameCancel">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        <div class="rename-dialog-body">
          <div class="rename-field">
            <label class="rename-label">任务ID</label>
            <input
              type="text"
              class="rename-input"
              :value="taskToRename"
              disabled
            />
          </div>
          <div class="rename-field">
            <label class="rename-label">原名称</label>
            <input
              type="text"
              class="rename-input"
              :value="store.records.find(r => r.task_id === taskToRename)?.task_name || store.records.find(r => r.task_id === taskToRename)?.video_name"
              disabled
            />
          </div>
          <div class="rename-field">
            <label class="rename-label">新名称</label>
            <input
              type="text"
              class="rename-input"
              v-model="newTaskName"
              placeholder="请输入新的任务名称"
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
            :disabled="isRenaming || !newTaskName.trim()"
          >
            {{ isRenaming ? '修改中...' : '确认修改' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 设置对话框 -->
    <SettingsDialog
      v-model:visible="showSettingsDialog"
      :model-path="modelPath"
      :output-path="outputPath"
      @save="handleSettingsSave"
      @browse-model="handleBrowseModel"
      @browse-output="handleBrowseOutput"
    />

    <!-- 历史记录筛选器 -->
    <HistoryFilter
      v-model:visible="showFilterDialog"
      @filter="handleFilter"
    />

    <!-- 历史记录排序器 -->
    <HistorySort
      v-model:visible="showSortDialog"
      :current-sort="sortConditions"
      @sort="handleSort"
    />

    <!-- 底部状态栏 -->
    <div class="user-panel" v-if="userStore.currentUser && !isCollapsed">
      <div class="user-info">
        <div class="avatar">{{ avatarInitials }}</div>
        <div class="user-meta">
          <div class="user-name">{{ userStore.currentUser.username }}</div>
          <div class="user-sub">Signed in</div>
        </div>
      </div>
      <!-- 连接状态 -->
      <div class="connection-status">
        <div class="status-indicator" :class="{ connected: isConnected, disconnected: !isConnected }">
          <div class="status-dot"></div>
          <span class="status-text">{{ isConnected ? '已连接' : '未连接' }}</span>
        </div>
      </div>
    </div>

    <!-- 信息面板 -->
    <div class="info-panel">
      <div class="info-content">
        <template v-if="!isCollapsed">
          <button class="btn-theme-toggle" title="切换主题" @click="toggleTheme">
            <svg
              class="theme-icon"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <!-- 太阳图标（浅色模式显示） -->
              <path
                v-if="!isDark"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
              ></path>
              <!-- 月亮图标（深色模式显示） -->
              <path
                v-else
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"
              ></path>
            </svg>
          </button>
          <button class="btn-settings" title="设置" @click="handleSettings">
            <svg
              class="settings-icon"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              ></path>
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              ></path>
            </svg>
          </button>
          <button class="btn-logout" title="退出登录" @click="handleLogout">
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
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
              ></path>
            </svg>
          </button>
        </template>
        <!-- 折叠状态下显示主题切换按钮和设置按钮 -->
        <template v-else>
          <button class="btn-theme-toggle btn-collapsed" title="切换主题" @click="toggleTheme">
            <svg
              class="theme-icon"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <!-- 太阳图标（浅色模式显示） -->
              <path
                v-if="!isDark"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
              ></path>
              <!-- 月亮图标（深色模式显示） -->
              <path
                v-else
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"
              ></path>
            </svg>
          </button>
          <button class="btn-settings btn-collapsed" title="设置" @click="handleSettings">
            <svg
              class="settings-icon"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              ></path>
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              ></path>
            </svg>
          </button>
        </template>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 320px;
  height: 100vh;
  background: var(--bg-sidebar);
  color: var(--text-secondary);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-secondary);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.sidebar.collapsed {
  width: 70px;
  align-items: center;
}

.sidebar-header {
  padding: 1rem;
  border-bottom: 1px solid var(--border-secondary);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar.collapsed .sidebar-header {
  padding: 1.25rem 0.75rem;
  align-items: center;
  border-bottom: 1px solid var(--border-secondary);
}

.header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  margin-bottom: 1rem;
}

.sidebar.collapsed .header-top {
  justify-content: center;
  margin-bottom: 0;
}

.sidebar-header h1 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.btn-collapse {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: var(--bg-record-hover);
  border: 1px solid var(--border-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sidebar.collapsed .btn-collapse {
  width: 36px;
  height: 36px;
}

.btn-collapse:hover {
  background: var(--bg-hover);
  border-color: var(--border-hover);
  transform: translateY(-1px);
}

.btn-collapse:active {
  transform: scale(0.95);
}

.btn-collapse svg {
  width: 18px;
  height: 18px;
  transition: transform 0.3s ease;
}

.sidebar.collapsed .btn-collapse svg {
  width: 20px;
  height: 20px;
}

/* 按钮网格容器 */
.action-buttons-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.btn-new-analysis {
  width: 100%;
  padding: 0.75rem 0.5rem;
  background: var(--accent-blue);
  color: var(--text-primary);
  border: var(--border-color) 1px solid;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  transition: background 0.2s;
}

.btn-new-analysis:hover {
  background: var(--accent-blue-hover);
}

.btn-new-analysis .icon {
  font-size: 1.1rem;
  font-weight: 300;
}

.btn-upload-model {
  width: 100%;
  padding: 0.75rem 0.5rem;
  background: var(--btn-upload);
  color: var(--text-primary);
  border: var(--border-color) 1px solid;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  transition: background 0.2s;
}

.btn-upload-model:hover {
  background: var(--btn-upload-hover);
}

.btn-upload-model .icon {
  font-size: 1.1rem;
  font-weight: 300;
}

.btn-compare {
  width: 100%;
  padding: 0.75rem 0.5rem;
  background: var(--accent-purple);
  color: var(--text-primary);
  border: var(--border-color) 1px solid;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  transition: background 0.2s;
}

.btn-compare:hover {
  background: var(--accent-purple-hover);
}

.btn-compare .icon {
  font-size: 1.1rem;
  font-weight: 300;
}

.btn-export {
  width: 100%;
  padding: 0.75rem 0.5rem;
  background: var(--accent-green);
  color: var(--text-primary);
  border: var(--border-color) 1px solid;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  transition: background 0.2s;
}

.btn-export:hover {
  background: var(--accent-green-hover);
}

.btn-export .icon {
  font-size: 1.1rem;
  font-weight: 300;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.section-title {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-primary);
  margin: 0;
  font-weight: 600;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  padding: 0 0.5rem;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-filter {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: var(--bg-record-hover);
  border: 1px solid var(--border-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.btn-filter:hover {
  background: var(--bg-hover);
  border-color: var(--accent-blue);
  color: var(--accent-blue);
  transform: translateY(-1px);
}

.btn-filter:active {
  transform: scale(0.95);
}

.btn-filter.active {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

.btn-filter.active:hover {
  background: var(--accent-blue-hover);
  border-color: var(--accent-blue-hover);
  color: white;
}

.btn-filter .filter-icon {
  width: 14px;
  height: 14px;
}

.btn-sort {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: var(--bg-record-hover);
  border: 1px solid var(--border-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.btn-sort:hover {
  background: var(--bg-hover);
  border-color: var(--accent-blue);
  color: var(--accent-blue);
  transform: translateY(-1px);
}

.btn-sort:active {
  transform: scale(0.95);
}

.btn-sort.active {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

.btn-sort.active:hover {
  background: var(--accent-blue-hover);
  border-color: var(--accent-blue-hover);
  color: white;
}

.btn-sort .sort-icon {
  width: 14px;
  height: 14px;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.record-item {
  padding: 0.75rem;
  background: var(--bg-record);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: var(--border-color) 1px solid;
}

.record-item:hover {
  background: var(--bg-record-hover);
  border-color: var(--border-tertiary);
}

.record-item.active {
  background: var(--bg-record-active);
  border-color: var(--accent-blue);
}

.record-item.active .btn-delete:hover:not(:disabled) {
  background: var(--alpha-hover);
  color: var(--danger-light);
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.record-name {
  font-weight: 500;
  font-size: 0.95rem;
  color: var(--text-primary);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-completed {
  background: var(--success-light);
  box-shadow: var(--shadow-success);
}

.dot-processing {
  background: var(--warning);
  box-shadow: var(--shadow-warning);
  animation: pulse-orange 2s ease-in-out infinite;
}

.dot-failed {
  background: var(--danger-light);
  box-shadow: var(--shadow-danger);
}

@keyframes pulse-orange {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.record-status {
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-weight: 500;
}

.status-completed {
  background: var(--success-bg);
  color: var(--success-light);
}

.status-processing {
  background: var(--warning-bg);
  color: var(--warning);
}

.status-failed {
  background: var(--danger-bg);
  color: var(--danger-light);
}

.record-video {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-time {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.model-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.6rem;
  background: var(--alpha-badge);
  border: 1px solid var(--alpha-badge-hover);
  border-radius: 4px;
  color: var(--accent-blue);
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.2s;
}

:global(:root:not(.dark)) .model-badge {
  background: var(--alpha-badge);
  border-color: var(--alpha-badge-hover);
  color: var(--accent-blue);
}

.model-badge:hover {
  background: var(--alpha-badge-hover);
  border-color: var(--alpha-badge-hover);
  filter: brightness(1.1);
}

:global(:root:not(.dark)) .model-badge:hover {
  background: var(--alpha-badge-hover);
  border-color: var(--alpha-badge-hover);
  filter: brightness(1.1);
}

.model-icon {
  width: 12px;
  height: 12px;
}

.record-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.25rem;
}

.btn-delete {
  background: transparent;
  border: none;
  color: var(--text-disabled);
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
}

.record-item:hover .btn-delete {
  opacity: 1;
}

.btn-delete:hover:not(:disabled) {
  background: var(--alpha-hover);
  color: var(--danger-light);
}

.btn-delete:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.btn-delete svg {
  width: 16px;
  height: 16px;
}

/* 任务操作按钮组 */
.task-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

/* 重命名按钮 */
.btn-rename {
  background: transparent;
  border: none;
  color: var(--text-disabled);
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
}

.record-item:hover .btn-rename {
  opacity: 1;
}

.btn-rename:hover:not(:disabled) {
  color: var(--accent-blue);
}

.btn-rename:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.btn-rename svg {
  width: 16px;
  height: 16px;
}

/* 重命名对话框样式 */
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

/* 滚动条样式 */
.sidebar-content::-webkit-scrollbar {
  width: 8px;
}

.sidebar-content::-webkit-scrollbar-track {
  background: var(--bg-sidebar);
}

.sidebar-content::-webkit-scrollbar-thumb {
  background: var(--border-tertiary);
  border-radius: 4px;
}

.sidebar-content::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* 底部状态栏 */
.user-panel {
  margin-top: auto;
  padding: 18px 20px;
  border-top: 1px solid var(--border-secondary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-shrink: 0;
}

.sidebar.collapsed .user-panel {
  display: none;
}

/* 用户信息 */
.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(88, 166, 255, 0.3), rgba(88, 166, 255, 0.5));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  flex-shrink: 0;
}

.user-meta {
  display: flex;
  flex-direction: column;
  color: var(--text-secondary);
  flex: 1;
  min-width: 0;
}

.user-name {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-sub {
  color: var(--text-muted);
  font-size: 12px;
  margin-top: 2px;
}

/* 信息面板 */
.info-panel {
  padding: 16px 20px;
  height: 65px;
  background: var(--bg-sidebar);
  display: flex;
  align-items: center;
  border-top: 1px solid var(--border-secondary);
  backdrop-filter: blur(10px);
  flex-shrink: 0;
}

.sidebar.collapsed .info-panel {
  padding: 12px;
  height: auto;
  border-top: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-content {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  width: 100%;
  gap: 0.75rem;
}

.sidebar.collapsed .info-content {
  justify-content: center;
  flex-direction: column;
  gap: 12px;
}

/* 连接状态 */
.connection-status {
  display: flex;
  align-items: center;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.status-indicator.connected {
  background: var(--success-bg);
  color: var(--success-light);
  border: 1px solid var(--success);
}

.status-indicator.disconnected {
  background: var(--danger-bg);
  color: var(--danger-light);
  border: 1px solid var(--danger);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.status-indicator.connected .status-dot {
  background-color: var(--success-light);
  box-shadow: 0 0 8px var(--success-light);
}

.status-indicator.disconnected .status-dot {
  background-color: var(--danger-light);
  box-shadow: 0 0 8px var(--danger-light);
}

.status-text {
  font-size: 0.8rem;
  font-weight: 500;
}

/* 主题切换按钮 */
.btn-theme-toggle {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--bg-record-hover);
  border: 1px solid var(--border-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.btn-theme-toggle:hover {
  background: var(--bg-hover);
  border-color: var(--border-hover);
  transform: translateY(-1px);
}

.btn-theme-toggle:active {
  transform: scale(0.95);
}

.theme-icon {
  width: 20px;
  height: 20px;
  transition: all 0.3s ease;
}

/* 设置按钮 */
.btn-settings {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--bg-record-hover);
  border: 1px solid var(--border-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.btn-settings:hover {
  background: var(--bg-hover);
  border-color: var(--border-hover);
  transform: translateY(-1px);
}

.btn-settings:active {
  transform: scale(0.95);
}

.settings-icon {
  width: 20px;
  height: 20px;
  transition: all 0.3s ease;
}

/* 登出按钮 */
.btn-logout {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--bg-record-hover);
  border: 1px solid var(--border-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-left: auto;
}

.btn-logout:hover {
  background: var(--danger-bg);
  border-color: var(--danger-light);
  color: var(--danger-light);
  transform: translateY(-1px);
}

.btn-logout svg {
  width: 18px;
  height: 18px;
}

/* 折叠状态下按钮的样式 */
.btn-collapsed {
  width: 36px;
  height: 36px;
  margin: 0 auto;
}
</style>
