<script setup lang="ts">
import '@/assets/styles/colors.css'
import { computed, onMounted, ref, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const taskId = computed(() => String(route.query.taskId || ''))
const showGuideModal = ref(true)
const showPaletteModal = ref(false)
const whitelistLibraries = ['math', 'statistics', 'numpy', 'matplotlib', 'matplotlib.pyplot', 'scipy', 'scipy.stats']
const codeText = ref(`# 模板使用说明：\n# 1) task_data['rows'] 是后端给你的逐帧数据\n# 2) 修改下方“可调参数区”即可快速改变图表效果\n\nimport matplotlib.pyplot as plt\nimport numpy as np\n\nrows = task_data.get('rows', [])\nif not rows:\n    raise RuntimeError('当前任务没有可用数据。')\n\nframes = np.array([int(r.get('frame', 0)) for r in rows], dtype=int)\nareas = np.array([float(r.get('area', 0.0)) for r in rows], dtype=float)\n\n# ===== 可调参数区（建议优先改这里） =====\nfig_w, fig_h = 9, 4.8          # 图尺寸：越大越清晰\nline_color = '#2563eb'         # 折线颜色（可换成调色盘中的编码）\nline_width = 1.4               # 折线粗细\nmarker_size = 14               # 散点大小\ngrid_alpha = 0.28              # 网格透明度（0~1）\ntitle_text = f"Task {task_data.get('task_id')} Area Trend"\n# ====================================\n\nplt.figure(figsize=(fig_w, fig_h))\nplt.plot(frames, areas, linewidth=line_width, color=line_color, label='Area')\nstep = max(1, len(frames) // 28)\nplt.scatter(frames[::step], areas[::step], s=marker_size, color='#1d4ed8', alpha=0.9)\nplt.title(title_text)\nplt.xlabel('Frame')\nplt.ylabel('Area')\nplt.grid(True, alpha=grid_alpha)\nplt.legend()\nplt.tight_layout()\n`)
const runOutput = ref('尚未执行。')
const imageUrl = ref('')
const isRunning = ref(false)
const isWarming = ref(false)
const warmupDone = ref(false)
const examples = ref<string[]>([])
const selectedExample = ref('')
const loadingExample = ref(false)
const paletteColors: Array<{ name: string; code: string; usage: string }> = [
  { name: '深蓝', code: '#2563eb', usage: '主线/主图强调' },
  { name: '亮蓝', code: '#3b82f6', usage: '第二曲线' },
  { name: '青蓝', code: '#06b6d4', usage: '散点/辅助线' },
  { name: '绿色', code: '#16a34a', usage: '正向趋势' },
  { name: '橙色', code: '#f59e0b', usage: '警示/峰值' },
  { name: '红色', code: '#ef4444', usage: '异常点/负向趋势' },
  { name: '紫色', code: '#7c3aed', usage: '分组区分' },
  { name: '灰蓝', code: '#64748b', usage: '网格/次要元素' },
  { name: '海军蓝', code: '#1e3a8a', usage: '深色背景主曲线' },
  { name: '天蓝', code: '#0ea5e9', usage: '高亮辅助曲线' },
  { name: '薄荷绿', code: '#10b981', usage: '增长趋势' },
  { name: '柠檬黄', code: '#eab308', usage: '关键阈值' },
  { name: '珊瑚橙', code: '#fb923c', usage: '提示峰值区间' },
  { name: '玫红', code: '#ec4899', usage: '重点轨迹' },
  { name: '葡萄紫', code: '#a855f7', usage: '分类区分' },
  { name: '深灰', code: '#334155', usage: '网格与坐标轴弱化' },
]

const exampleNameMap: Record<string, string> = {
  'case01_data_structure_and_basics.py': '模板01：数据结构与基础处理',
  'case02_histogram_speed_distribution.py': '模板02：速度分布直方图',
  'case03_scatter_multiframe_positions.py': '模板03：多帧位置散点图',
  'case04_heatmap_density_multiframe.py': '模板04：多帧密度热力图',
  'case05_normalized_trajectories.py': '模板05：归一化轨迹图',
  'case06_multi_metric_timeseries.py': '模板06：多指标时序图',
  'case07_distribution_panels.py': '模板07：指标分布四宫格',
  'case08_trajectory_3d_lines.py': '模板08：3D 轨迹线图',
  'case09_histogram_3d_multiframe.py': '模板09：多帧 3D 直方图',
  'case10_shape_activity_dashboard.py': '模板10：形态与活跃度看板',
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

function exitGuideAndBack() {
  showGuideModal.value = false
  if (window.history.length > 1) {
    router.back()
    return
  }
  goBack()
}

function openPaletteModal() {
  showPaletteModal.value = true
}

function closePaletteModal() {
  showPaletteModal.value = false
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
    runOutput.value = '请先选择一个模板。'
    return
  }

  const username = userStore.currentUser?.username || ''
  if (!username) {
    runOutput.value = '未检测到登录用户，无法导入模板。'
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
    runOutput.value = `已导入模板: ${getExampleDisplayName(loadedName)}`
  } catch (error: any) {
    runOutput.value = `导入模板失败: ${error?.message || error}`
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

// --- CodeMirror 6 编辑器初始化 (按需懒加载以减小首包)
const editorContainer = ref<HTMLElement | null>(null)
let editorView: any = null

async function initCodeMirror() {
  if (!editorContainer.value) return
  try {
    const cmView = await import('@codemirror/view')
    const cmState = await import('@codemirror/state')
    const cmLanguage = await import('@codemirror/language')
    const cmPython = await import('@codemirror/lang-python')
    const lezerHighlight = await import('@lezer/highlight')

    const pythonHighlightStyle = cmLanguage.HighlightStyle.define([
      { tag: [lezerHighlight.tags.keyword, lezerHighlight.tags.modifier], color: '#569CD6' },
      { tag: [lezerHighlight.tags.string, lezerHighlight.tags.special(lezerHighlight.tags.string)], color: '#CE9178' },
      { tag: [lezerHighlight.tags.number, lezerHighlight.tags.bool, lezerHighlight.tags.null], color: '#B5CEA8' },
      { tag: [lezerHighlight.tags.comment], color: '#6A9955', fontStyle: 'italic' },
      { tag: [lezerHighlight.tags.function(lezerHighlight.tags.variableName), lezerHighlight.tags.labelName], color: '#DCDCAA' },
      { tag: [lezerHighlight.tags.variableName, lezerHighlight.tags.propertyName], color: '#9CDCFE' },
      { tag: [lezerHighlight.tags.operator, lezerHighlight.tags.punctuation], color: '#D4D4D4' },
    ])

    const editorTheme = cmView.EditorView.theme({
      '&': {
        height: '100%',
        color: '#d4d4d4',
        backgroundColor: '#0f172a',
      },
      '.cm-content': {
        fontFamily: "Consolas, 'Courier New', monospace",
        fontSize: '13px',
        lineHeight: '1.5',
        caretColor: '#d4d4d4',
      },
      '.cm-gutters': {
        backgroundColor: '#0f172a',
        color: '#6b7280',
        border: 'none',
      },
      '.cm-activeLine': {
        backgroundColor: 'rgba(148, 163, 184, 0.08)',
      },
      '.cm-selectionBackground, .cm-content ::selection': {
        backgroundColor: 'rgba(96, 165, 250, 0.25)',
      },
    })

    const updateListener = cmView.EditorView.updateListener.of((update: any) => {
      if (update.docChanged && editorView) {
        codeText.value = editorView.state.doc.toString()
      }
    })

    editorView = new cmView.EditorView({
      state: cmState.EditorState.create({
        doc: codeText.value,
        extensions: [
          cmPython.python(),
          editorTheme,
          cmLanguage.syntaxHighlighting(pythonHighlightStyle),
          updateListener,
        ],
      }),
      parent: editorContainer.value,
    })
  } catch (e) {
    // eslint-disable-next-line no-console
    console.warn('CodeMirror 初始化失败:', e)
  }
}

onMounted(() => {
  void initCodeMirror()
})

watch(codeText, (nextCode) => {
  if (!editorView) return
  const currentCode = editorView.state.doc.toString()
  if (currentCode === nextCode) return

  editorView.dispatch({
    changes: {
      from: 0,
      to: editorView.state.doc.length,
      insert: nextCode,
    },
  })
})

onBeforeUnmount(() => {
  if (editorView && editorView.destroy) editorView.destroy()
  editorView = null
})
</script>

<template>
  <div class="free-plot-page">
    <div class="page-header">
      <button class="btn-back" @click="goBack">← 返回</button>
      <h2>自由绘图实验室</h2>
      <button class="btn-palette" @click="openPaletteModal">图表调色盘</button>
      <div class="task-pill">任务ID: {{ taskId || '未指定' }}</div>
    </div>

    <div class="page-content">
      <div class="editor-panel">
        <div class="panel-title">Python 脚本</div>
        <div class="example-toolbar">
          <select v-model="selectedExample" :disabled="loadingExample || examples.length === 0">
            <option value="" disabled>选择模板</option>
            <option v-for="item in examples" :key="item" :value="item">{{ getExampleDisplayName(item) }}</option>
          </select>
          <button class="btn-import" @click="importExample" :disabled="loadingExample || !selectedExample">
            {{ loadingExample ? '导入中...' : '导入模板' }}
          </button>
        </div>
        <div ref="editorContainer" class="code-editor-cm"></div>
        <!-- 回退 textarea（隐藏，仅在 CodeMirror 加载失败时可见） -->
        <textarea v-model="codeText" class="code-editor" spellcheck="false" style="display:none"></textarea>
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
          <button class="btn-cancel" @click="exitGuideAndBack">退出</button>
          <button class="btn-confirm" @click="closeGuideModal">我已了解，开始使用</button>
        </div>
      </div>
    </div>

    <div v-if="showPaletteModal" class="guide-mask" @click.self="closePaletteModal">
      <div class="palette-card">
        <div class="palette-header">
          <h3>图表调色盘</h3>
          <button class="btn-cancel" @click="closePaletteModal">关闭</button>
        </div>
        <p>可将下列颜色编码直接粘贴到 Python 代码中，例如 color='#2563eb'。</p>
        <div class="palette-grid">
          <div v-for="item in paletteColors" :key="item.code" class="palette-item">
            <span class="palette-swatch" :style="{ backgroundColor: item.code }"></span>
            <div class="palette-meta">
              <div class="palette-name">{{ item.name }}</div>
              <div class="palette-code">{{ item.code }}</div>
              <div class="palette-usage">建议：{{ item.usage }}</div>
            </div>
          </div>
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
.btn-cancel,
.btn-import,
.btn-download,
.btn-palette {
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

.btn-palette {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
  background: transparent;
}

.btn-cancel {
  border-color: var(--border-color);
  color: var(--text-secondary);
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

.code-editor-cm {
  width: 100%;
  flex: 1;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: #0f172a;
  overflow: hidden;
}

.code-editor-cm :deep(.cm-editor) {
  height: 100%;
  color: #e2e8f0;
  font-family: Consolas, 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.code-editor-cm :deep(.cm-scroller) {
  overflow: auto;
}

.code-editor-cm :deep(.cm-content) {
  min-height: 100%;
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
  gap: 8px;
  justify-content: flex-end;
}

.palette-card {
  width: min(760px, 94vw);
  max-height: 82vh;
  overflow: auto;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  color: var(--text-primary);
}

.palette-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.palette-header h3 {
  margin: 0;
}

.palette-card p {
  margin: 0 0 12px;
  color: var(--text-secondary);
}

.palette-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.palette-item {
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 10px;
  display: flex;
  gap: 10px;
  align-items: center;
  background: var(--bg-main);
}

.palette-swatch {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}

.palette-meta {
  min-width: 0;
}

.palette-name {
  font-weight: 600;
  color: var(--text-primary);
}

.palette-code {
  font-family: Consolas, 'Courier New', monospace;
  color: var(--accent-blue);
  margin-top: 2px;
}

.palette-usage {
  margin-top: 2px;
  font-size: 12px;
  color: var(--text-secondary);
}

@media (max-width: 980px) {
  .page-content {
    grid-template-columns: 1fr;
  }

  .palette-grid {
    grid-template-columns: 1fr;
  }
}
</style>
