<script setup lang="ts">
import { useAnalysisStore } from '@/stores/analysisStore'

const store = useAnalysisStore()

// 处理查看细胞详情
function handleViewCell(cellId: string) {
  store.selectCell(cellId)
}
</script>

<template>
  <div class="cell-list-section">
    <h3>细胞详细信息</h3>
    <div class="table-placeholder">
      <table class="cell-table">
        <thead>
          <tr>
            <th>细胞ID</th>
            <th>首次出现</th>
            <th>最后出现</th>
            <th>存活帧数</th>
            <th>平均尺寸</th>
            <th>平均置信度</th>
            <th>平均速度</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="cell in store.selectedRecord?.result?.cells || []" :key="cell.cell_id">
            <td>{{ cell.cell_id }}</td>
            <td>
              第 {{ cell.first_frame ?? '-' }} 帧
            </td>
            <td>
              第 {{ cell.last_frame ?? '-' }} 帧
            </td>
            <td>{{ cell.frame_count }} 帧</td>
            <td>{{ cell.avg_width }}×{{ cell.avg_height }} px</td>
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
  color: #fff;
  margin: 0 0 1rem 0;
  transition: color 0.3s;
}

:global(:root:not(.dark)) .cell-list-section h3 {
  color: #333;
}

.table-placeholder {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  overflow: hidden;
  transition: background 0.3s, border-color 0.3s;
}

:global(:root:not(.dark)) .table-placeholder {
  background: #fff;
  border-color: #e0e0e0;
}

.cell-table {
  width: 100%;
  border-collapse: collapse;
}

.cell-table th {
  background: #21262d;
  padding: 0.75rem 1rem;
  text-align: left;
  font-size: 0.875rem;
  font-weight: 600;
  color: #8b949e;
  border-bottom: 1px solid #30363d;
  transition: background 0.3s, border-color 0.3s, color 0.3s;
}

:global(:root:not(.dark)) .cell-table th {
  background: #f5f5f5;
  border-bottom-color: #e0e0e0;
  color: #666;
}

.cell-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #21262d;
  color: #c9d1d9;
  font-size: 0.875rem;
  transition: border-color 0.3s, color 0.3s;
}

:global(:root:not(.dark)) .cell-table td {
  border-bottom-color: #e0e0e0;
  color: #333;
}

.cell-table tbody tr:hover {
  background: #0d1117;
  transition: background 0.3s;
}

:global(:root:not(.dark)) .cell-table tbody tr:hover {
  background: #f5f5f5;
}

.btn-view {
  padding: 0.25rem 0.75rem;
  background: #21262d;
  color: #58a6ff;
  border: 1px solid #30363d;
  border-radius: 4px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

:global(:root:not(.dark)) .btn-view {
  background: #fff;
  color: #2196f3;
  border-color: #ccc;
}

.btn-view:hover {
  background: #1f6feb20;
  border-color: #58a6ff;
}

:global(:root:not(.dark)) .btn-view:hover {
  background: #e3f2fd;
  border-color: #2196f3;
}
</style>