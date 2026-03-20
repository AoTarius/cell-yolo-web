<script setup lang="ts">
import '@/assets/styles/colors.css'
import { ref, computed, onMounted, watch } from 'vue'
import { useAnalysisStore } from '@/stores/analysisStore'
import type { CellData } from '@/stores/analysisStore'

const store = useAnalysisStore()

// 从数据库加载的细胞数据（替代从 JSON 读取的数据）
const dbCells = ref<CellData[]>([])
const isLoading = ref(false)

// 加载细胞数据
async function loadCellsData() {
  if (!store.selectedRecord?.task_id) {
    return
  }

  isLoading.value = true
  try {
    dbCells.value = await store.loadCellsByTask(store.selectedRecord.task_id)
  } catch (error) {
    console.error('加载细胞数据失败:', error)
    dbCells.value = []
  } finally {
    isLoading.value = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadCellsData()
})

// 监听任务切换，自动重新加载数据
watch(() => store.selectedRecord?.task_id, (newTaskId, oldTaskId) => {
  if (newTaskId && newTaskId !== oldTaskId) {
    loadCellsData()
  }
})

// 排序状态
type SortColumn = 'cell_id' | 'first_frame' | 'last_frame' | 'frame_count' | 'avg_conf' | 'avg_velocity'
const sortColumn = ref<SortColumn | null>(null)
const sortDirection = ref<'asc' | 'desc'>('asc')

// 排序后的细胞列表
const sortedCells = computed(() => {
  // 优先使用从数据库加载的数据，如果没有则使用 JSON 中的数据（兼容性）
  const cells = dbCells.value.length > 0 ? dbCells.value : (store.selectedRecord?.result?.cells || [])
  if (!sortColumn.value) return cells

  const sorted = [...cells].sort((a, b) => {
    let comparison = 0

    switch (sortColumn.value) {
      case 'cell_id':
        // 提取数字部分进行比较
        const aIdStr = typeof a.cell_id === 'string' ? a.cell_id : String(a.cell_id)
        const bIdStr = typeof b.cell_id === 'string' ? b.cell_id : String(b.cell_id)
        const aId = parseInt(aIdStr.replace(/\D/g, '') || '0', 10)
        const bId = parseInt(bIdStr.replace(/\D/g, '') || '0', 10)
        comparison = aId - bId
        break
      case 'first_frame':
        comparison = (a.first_frame ?? 0) - (b.first_frame ?? 0)
        break
      case 'last_frame':
        comparison = (a.last_frame ?? 0) - (b.last_frame ?? 0)
        break
      case 'frame_count':
        comparison = (a.frame_count ?? 0) - (b.frame_count ?? 0)
        break
      case 'avg_conf':
        comparison = (a.avg_conf ?? 0) - (b.avg_conf ?? 0)
        break
      case 'avg_velocity':
        comparison = (a.avg_velocity ?? 0) - (b.avg_velocity ?? 0)
        break
    }

    // 应用排序方向
    if (sortDirection.value === 'desc') {
      comparison = -comparison
    }

    // 如果主排序值相同，使用细胞ID作为二级排序
    if (comparison === 0) {
      const aId2 = typeof a.cell_id === 'string' ? parseInt(a.cell_id.replace(/\D/g, '') || '0') : 0
      const bId2 = typeof b.cell_id === 'string' ? parseInt(b.cell_id.replace(/\D/g, '') || '0') : 0

      // 二级排序也遵循当前的排序方向
      let secondaryComparison = aId2 - bId2
      if (sortDirection.value === 'desc') {
        secondaryComparison = -secondaryComparison
      }
      comparison = secondaryComparison
    }

    return comparison
  })
  return sorted
})

// 处理排序
function handleSort(column: SortColumn) {
  if (sortColumn.value === column) {
    // 如果点击的是当前排序列，切换方向
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    // 如果点击的是新列，设置为升序
    sortColumn.value = column
    sortDirection.value = 'asc'
  }
}

// 获取排序图标
function getSortIcon(column: SortColumn) {
  if (sortColumn.value !== column) {
    // 未排序：显示灰色小三角（向上）
    return `
      <svg class="sort-icon sort-icon-neutral" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path>
      </svg>
    `
  }
  if (sortDirection.value === 'asc') {
    // 升序：显示蓝色向上三角
    return `
      <svg class="sort-icon sort-icon-active" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path>
      </svg>
    `
  }
  // 降序：显示蓝色向下三角
  return `
    <svg class="sort-icon sort-icon-active" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
    </svg>
  `
}

// 处理查看细胞详情
function handleViewCell(cellId: string) {
  store.selectCell(cellId)
}
</script>

<template>
  <div class="cell-list-section">
    <h3>细胞详细信息</h3>
    <div v-if="isLoading" class="loading-placeholder">
      <svg class="loading-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
      </svg>
      <p>加载细胞数据中...</p>
    </div>
    <div v-else class="table-placeholder">
      <table class="cell-table">
        <thead>
          <tr>
            <th class="sortable" @click="handleSort('cell_id')">
              <span>细胞ID</span>
              <span class="sort-icon-wrapper" v-html="getSortIcon('cell_id')"></span>
            </th>
            <th class="sortable" @click="handleSort('first_frame')">
              <span>首次出现</span>
              <span class="sort-icon-wrapper" v-html="getSortIcon('first_frame')"></span>
            </th>
            <th class="sortable" @click="handleSort('last_frame')">
              <span>最后出现</span>
              <span class="sort-icon-wrapper" v-html="getSortIcon('last_frame')"></span>
            </th>
            <th class="sortable" @click="handleSort('frame_count')">
              <span>存活帧数</span>
              <span class="sort-icon-wrapper" v-html="getSortIcon('frame_count')"></span>
            </th>
            <th class="sortable disabled">
              <span>平均尺寸</span>
              <span class="sort-icon-wrapper" v-html="getSortIcon('cell_id')"></span>
            </th>
            <th class="sortable" @click="handleSort('avg_conf')">
              <span>平均置信度</span>
              <span class="sort-icon-wrapper" v-html="getSortIcon('avg_conf')"></span>
            </th>
            <th class="sortable" @click="handleSort('avg_velocity')">
              <span>平均速度</span>
              <span class="sort-icon-wrapper" v-html="getSortIcon('avg_velocity')"></span>
            </th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="cell in sortedCells" :key="cell.cell_id">
            <td>{{ cell.cell_id }}</td>
            <td>
              第 {{ cell.first_frame ?? '-' }} 帧
            </td>
            <td>
              第 {{ cell.last_frame ?? '-' }} 帧
            </td>
            <td>{{ cell.frame_count }} 帧</td>
            <td>{{ cell.avg_width.toFixed(3) }}×{{ cell.avg_height.toFixed(3) }} px</td>
            <td>{{ cell.avg_conf.toFixed(2) }}</td>
            <td>
              {{
                cell.avg_velocity > 0
                  ? cell.avg_velocity.toFixed(2)
                  : '0.00'
              }}
              px/frame
            </td>
            <td>
              <button class="btn-view" @click="handleViewCell(cell.cell_id)">查看详情</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.cell-list-section {
  margin-bottom: 2rem;
}

.cell-list-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .cell-list-section h3 {
  color: var(--text-primary-light);
}

.loading-placeholder {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 3rem 2rem;
  text-align: center;
  color: var(--text-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .loading-placeholder {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

.loading-icon {
  width: 48px;
  height: 48px;
  animation: spin 1s linear infinite;
  color: var(--accent-blue);
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.loading-placeholder p {
  margin: 0;
  font-size: 1rem;
  color: var(--text-secondary);
}

.table-placeholder {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .table-placeholder {
  background: var(--bg-card-light);
  border-color: var(--border-color-light);
}

.cell-table {
  width: 100%;
  border-collapse: collapse;
}

.cell-table th {
  background: var(--bg-input);
  padding: 0.75rem 1rem;
  text-align: left;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-color);
  transition: background 0.3s, border-color 0.3s, color 0.3s;
}

:global(:root:not(.dark)) .cell-table th {
  background: var(--bg-hover);
  border-bottom-color: var(--border-color-light);
  color: var(--text-muted-light);
}

.cell-table th.sortable {
  cursor: pointer;
  user-select: none;
  transition: background 0.3s, color 0.3s;
}

.cell-table th.sortable:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

:global(:root:not(.dark)) .cell-table th.sortable:hover {
  background: var(--bg-input-light);
  color: var(--text-primary-light);
}

.cell-table th.sortable.disabled {
  cursor: default;
}

.cell-table th.sortable.disabled:hover {
  background: var(--bg-input);
  color: var(--text-muted);
}

:global(:root:not(.dark)) .cell-table th.sortable.disabled:hover {
  background: var(--bg-hover);
  color: var(--text-muted-light);
}

.cell-table th span {
  display: inline-block;
}

.cell-table th .sort-icon-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: 0.5rem;
  width: 14px;
  height: 14px;
  vertical-align: middle;
}

.cell-table th .sort-icon {
  width: 100%;
  height: 100%;
}

.cell-table th .sort-icon-neutral {
  color: var(--text-disabled);
  transition: color 0.2s;
}

:global(:root:not(.dark)) .cell-table th .sort-icon-neutral {
  color: var(--text-disabled-light);
}

.cell-table th .sort-icon-active {
  color: var(--accent-blue);
  transition: color 0.2s;
}

:global(:root:not(.dark)) .cell-table th .sort-icon-active {
  color: var(--accent-blue);
}

.cell-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--bg-input);
  color: var(--text-secondary);
  font-size: 0.875rem;
  transition: border-color 0.3s, color 0.3s;
}

:global(:root:not(.dark)) .cell-table td {
  border-bottom-color: var(--border-color-light);
  color: var(--text-primary-light);
}

.cell-table tbody tr:hover {
  background: var(--bg-main);
  transition: background 0.3s;
}

:global(:root:not(.dark)) .cell-table tbody tr:hover {
  background: var(--bg-main-light);
}

.btn-view {
  padding: 0.25rem 0.75rem;
  background: var(--bg-input);
  color: var(--accent-blue);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

:global(:root:not(.dark)) .btn-view {
  background: var(--bg-card-light);
  color: var(--accent-blue);
  border-color: var(--border-color-light);
}

.btn-view:hover {
  background: var(--alpha-badge);
  border-color: var(--accent-blue);
}

:global(:root:not(.dark)) .btn-view:hover {
  background: var(--upload-hover-bg);
  border-color: var(--accent-blue);
}
</style>