<script setup lang="ts">
import '@/assets/styles/colors.css'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const taskId = computed(() => String(route.query.taskId || ''))
const showGuideModal = ref(true)
const whitelistLibraries = ['math', 'statistics', 'numpy', 'matplotlib', 'matplotlib.pyplot', 'scipy', 'scipy.stats']
const codeText = ref(`import matplotlib.pyplot as plt\nimport numpy as np\n\nrows = task_data['rows']\nframes = np.array([r['frame'] for r in rows])\nareas = np.array([r['area'] for r in rows])\n\nplt.figure(figsize=(8, 4.5))\nplt.plot(frames, areas, linewidth=1.1)\nplt.title(f"Task {task_data['task_id']} Area Trend")\nplt.xlabel('Frame')\nplt.ylabel('Area')\nplt.grid(True, alpha=0.3)\n`)
const runOutput = ref('尚未执行。')
const imageUrl = ref('')
const isRunning = ref(false)
const isWarming = ref(false)
const warmupDone = ref(false)
const examples = ref<string[]>([])
const selectedExample = ref('')
const loadingExample = ref(false)

const exampleNameMap: Record<string, string> = {
  'case01_data_structure_and_basics.py': '案例01：数据结构与基础处理',
  'case02_histogram_speed_distribution.py': '案例02：速度分布直方图',
  'case03_scatter_multiframe_positions.py': '案例03：多帧位置散点图',
  'case04_heatmap_density_multiframe.py': '案例04：多帧密度热力图',
  'case05_normalized_trajectories.py': '案例05：归一化轨迹图',
  'case06_multi_metric_timeseries.py': '案例06：多指标时序图',
  'case07_distribution_panels.py': '案例07：指标分布四宫格',
  'case08_trajectory_3d_lines.py': '案例08：3D 轨迹线图',
  'case09_histogram_3d_multiframe.py': '案例09：多帧 3D 直方图',
  'case10_shape_activity_dashboard.py': '案例10：形态与活跃度看板',
}

function getExampleDisplayName(fileName: string): string {
  return exampleNameMap[fileName] || fileName
}

function downloadPlotImage() {
  if (!imageUrl.value) {
    runOutput.value = '当前没有可下载的图片，请先运行绘图。'
    return
  }

  const link = document.createElement('a')
  link.href = imageUrl.value
  const now = new Date()
  const stamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`
  const safeTaskId = String(taskId.value || 'task').replace(/[^a-zA-Z0-9_-]/g, '_')
  link.download = `free_plot_${safeTaskId}_${stamp}.png`
  link.click()
}

function closeGuideModal() {
  showGuideModal.value = false
}

async function ensureWarmup() {
  if (warmupDone.value || isWarming.value) return

  const username = userStore.currentUser?.username || ''
  if (!username) return

  isWarming.value = true
  runOutput.value = '正在初始化绘图环境（仅首次等待，完成后会保持常驻加速）...'

  try {
    const response = await fetch('/api/free-plot/warmup/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username }),
    })
    const payload = await response.json()

    if (!response.ok || !payload?.success) {
      const err = payload?.error || '预热失败'
      runOutput.value = `预热失败(HTTP ${response.status}): ${err}`
      return
    }

    warmupDone.value = true
    runOutput.value = '绘图环境已就绪，可以开始运行脚本。'
  } catch (error: any) {
    runOutput.value = `预热请求失败: ${error?.message || error}`
  } finally {
    isWarming.value = false
  }
}

async function loadExamples() {
  const username = userStore.currentUser?.username || ''
  if (!username) return

  try {
    const response = await fetch(`/api/free-plot/examples/?username=${encodeURIComponent(username)}`)
    const payload = await response.json()
    if (!response.ok || !payload?.success || !Array.isArray(payload?.examples)) {
      return
    }

    examples.value = payload.examples
    if (!selectedExample.value && examples.value.length > 0) {
      selectedExample.value = examples.value[0] || ''
    }
  } catch {
    // ignore list loading error in MVP
  }
}

async function importExample() {
  if (loadingExample.value) return
  if (!selectedExample.value) {
    runOutput.value = '请先选择一个案例。'
    return
  }

  const username = userStore.currentUser?.username || ''
  if (!username) {
    runOutput.value = '未检测到登录用户，无法导入案例。'
    return
  }

  loadingExample.value = true
  try {
    const response = await fetch(
      `/api/free-plot/examples/${encodeURIComponent(selectedExample.value)}/?username=${encodeURIComponent(username)}`
    )
    const payload = await response.json()
    if (!response.ok || !payload?.success) {
      runOutput.value = `导入失败(HTTP ${response.status}): ${payload?.error || '未知错误'}`
      return
    }

    codeText.value = String(payload.content || '')
    const loadedName = String(payload.name || selectedExample.value)
    runOutput.value = `已导入案例: ${getExampleDisplayName(loadedName)}`
  } catch (error: any) {
    runOutput.value = `导入案例失败: ${error?.message || error}`
  } finally {
    loadingExample.value = false
  }
}

function goBack() {
  const returnTo = String(route.query.returnTo || 'drawingCanvas')
  if (returnTo === 'compareResult') {
    router.push({ name: 'compareResult' })
    return
  }

  if (returnTo === 'cellTracking') {
    router.push({ name: 'cellTracking' })
    return
  }

  router.push({
    name: 'drawingCanvas',
    query: {
      taskId: taskId.value,
      type: 'scatter',
      returnTo,
    },
  })
}

async function runCode() {
  if (isRunning.value) return

  const username = userStore.currentUser?.username || ''
  if (!username) {
    runOutput.value = '未检测到登录用户，请重新登录后再试。'
    return
  }

  if (!taskId.value) {
    runOutput.value = '缺少任务ID，无法执行绘图。'
    return
  }

  await ensureWarmup()
  if (!warmupDone.value) {
    return
  }

  isRunning.value = true
  runOutput.value = '执行中，请稍候...'
  imageUrl.value = ''

  try {
    const response = await fetch('/api/free-plot/run/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username,
        task_id: taskId.value,
        code: codeText.value,
      }),
    })

    const payload = await response.json()
    if (!response.ok || !payload?.success) {
      const errorBlock = Array.isArray(payload?.validation_errors)
        ? payload.validation_errors.join('\n')
        : (payload?.error || '执行失败')
      runOutput.value = [
        `执行失败(HTTP ${response.status}):`,
        errorBlock,
        payload?.logs ? `\n日志:\n${payload.logs}` : '',
      ].filter(Boolean).join('\n')
      return
    }

    if (payload.image_base64) {
      imageUrl.value = `data:image/png;base64,${payload.image_base64}`
    }

    const meta = payload.task_data_meta || {}
    runOutput.value = [
      payload.logs || '执行成功。',
      `数据行数: ${meta.row_count ?? '-'}`,
      `是否截断: ${meta.truncated ? '是' : '否'}`,
    ].join('\n')
  } catch (error: any) {
    runOutput.value = `请求失败: ${error?.message || error}`
  } finally {
    isRunning.value = false
  }
}

onMounted(() => {
  void ensureWarmup()
  void loadExamples()
})
</script>

<template>
  <div class="free-plot-page">
    <div class="page-header">
      <button class="btn-back" @click="goBack">← 返回</button>
      <h2>自由绘图实验室</h2>
      <div class="task-pill">任务ID: {{ taskId || '未指定' }}</div>
    </div>

    <div class="page-content">
      <div class="editor-panel">
        <div class="panel-title">Python 脚本</div>
        <div class="example-toolbar">
          <select v-model="selectedExample" :disabled="loadingExample || examples.length === 0">
            <option value="" disabled>选择案例</option>
            <option v-for="item in examples" :key="item" :value="item">{{ getExampleDisplayName(item) }}</option>
          </select>
          <button class="btn-import" @click="importExample" :disabled="loadingExample || !selectedExample">
            {{ loadingExample ? '导入中...' : '导入案例' }}
          </button>
        </div>
        <textarea v-model="codeText" class="code-editor" spellcheck="false"></textarea>
        <div class="actions">
          <button class="btn-run" @click="runCode" :disabled="isRunning || isWarming">{{ isWarming ? '环境预热中...' : (isRunning ? '执行中...' : '运行绘图') }}</button>
        </div>
      </div>

      <div class="result-panel">
        <div class="panel-title-row">
          <div class="panel-title">运行结果</div>
          <button class="btn-download" @click="downloadPlotImage" :disabled="!imageUrl">下载图片</button>
        </div>
        <div class="output-box">{{ runOutput }}</div>
        <img v-if="imageUrl" :src="imageUrl" class="plot-image" alt="plot result" />
      </div>
    </div>

    <div v-if="showGuideModal" class="guide-mask" @click.self="closeGuideModal">
      <div class="guide-card">
        <h3>欢迎使用自由绘图</h3>
        <p>该功能面向熟悉 Python 的用户，用于对当前任务数据进行自定义绘图。</p>
        <ul>
          <li>仅允许访问你本人有权限的任务数据。</li>
          <li>仅允许白名单库：{{ whitelistLibraries.join(', ') }}。</li>
          <li>禁止文件系统、网络、系统命令与动态执行。</li>
          <li>首次进入会自动预热运行环境，后续执行会更快。</li>
          <li>每次运行都受执行时长与内存限制。</li>
        </ul>
        <p class="tip">继续即表示你已理解上述限制与安全规则。</p>
        <div class="guide-actions">
          <button class="btn-confirm" @click="closeGuideModal">我已了解，开始使用</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.free-plot-page {
  min-height: 100vh;
  background: var(--bg-main);
  display: flex;
  flex-direction: column;
}

.page-header {
  padding: 14px 18px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-card);
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-back,
.btn-run,
.btn-confirm,
.btn-import,
.btn-download {
  border: 1px solid var(--border-color);
  background: var(--bg-input);
  color: var(--text-primary);
  border-radius: 6px;
  padding: 8px 12px;
  cursor: pointer;
}

.btn-run,
.btn-confirm {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: #fff;
}

.btn-import {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
  background: transparent;
}

.btn-download {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
  background: transparent;
  padding: 6px 10px;
  font-size: 12px;
}

.btn-download:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-header h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: 18px;
}

.task-pill {
  margin-left: auto;
  font-size: 12px;
  color: var(--text-secondary);
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid var(--border-color);
}

.page-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 12px;
}

.editor-panel,
.result-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  min-height: 480px;
}

.panel-title {
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}

.panel-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.panel-title-row .panel-title {
  margin-bottom: 0;
}

.example-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.example-toolbar select {
  flex: 1;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-input);
  color: var(--text-primary);
  padding: 6px 8px;
}

.code-editor {
  width: 100%;
  flex: 1;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  padding: 10px;
  background: #0f172a;
  color: #e2e8f0;
  font-family: Consolas, 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  resize: none;
}

.actions {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

.output-box {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px;
  min-height: 120px;
  white-space: pre-wrap;
  color: var(--text-secondary);
  background: var(--bg-main);
}

.plot-image {
  margin-top: 10px;
  max-width: 100%;
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.guide-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1500;
}

.guide-card {
  width: min(620px, 92vw);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  color: var(--text-primary);
}

.guide-card h3 {
  margin: 0 0 10px;
}

.guide-card p {
  margin: 0 0 8px;
  color: var(--text-secondary);
}

.guide-card ul {
  margin: 6px 0 10px;
  padding-left: 20px;
  color: var(--text-secondary);
}

.tip {
  font-size: 12px;
  color: var(--text-muted);
}

.guide-actions {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 980px) {
  .page-content {
    grid-template-columns: 1fr;
  }
}
</style>
