<script setup lang="ts">
import '@/assets/styles/colors.css'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const taskId = computed(() => String(route.query.taskId || ''))
const showGuideModal = ref(true)
const codeText = ref(`# 示例: 请仅使用任务数据接口绘图\n# 运行接口接通后可使用以下模式:\n# data = load_task_data(task_id)\n# import matplotlib.pyplot as plt\n# plt.plot(data['frame'], data['area'])\n# plt.xlabel('Frame')\n# plt.ylabel('Area')\n# plt.title('Task Plot')\n# plt.show()\n`)
const runOutput = ref('尚未执行。当前为MVP界面骨架，后续将接入安全执行后端。')
const imageUrl = ref('')

function closeGuideModal() {
  showGuideModal.value = false
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

function runCode() {
  runOutput.value = [
    'MVP提示: 自由绘图后端尚未接通。',
    '下一步将接入安全执行接口 /api/free-plot/run/ 。',
    `当前任务ID: ${taskId.value || '未指定'}`,
  ].join('\n')
  imageUrl.value = ''
}
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
        <textarea v-model="codeText" class="code-editor" spellcheck="false"></textarea>
        <div class="actions">
          <button class="btn-run" @click="runCode">运行绘图</button>
        </div>
      </div>

      <div class="result-panel">
        <div class="panel-title">运行结果</div>
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
          <li>仅允许科学计算与绘图库白名单。</li>
          <li>禁止文件系统、网络、系统命令与动态执行。</li>
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
.btn-confirm {
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
