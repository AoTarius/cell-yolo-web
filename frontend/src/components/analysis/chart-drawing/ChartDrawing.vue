<script setup lang="ts">
import '@/assets/styles/colors.css';
import { ref, reactive, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAnalysisStore } from '@/stores/analysisStore';

const router = useRouter();
const analysisStore = useAnalysisStore();

// 当前选中的任务ID（从store获取）
const selectedTaskId = computed(() => analysisStore.selectedId);

// 弹窗状态
const modalStates = ref({
  timeSeries: false,
  histogram: false,
  scatter: false,
  trajectory: false,
});

const props = defineProps<{
  embedded?: boolean  // 是否为嵌入模式
}>();

// 细胞特征选项（所有图表共用）
const cellFeatures = [
  { value: 'area', label: '面积 (Area)' },
  { value: 'speed', label: '速度 (Speed)' },
  { value: 'perimeter', label: '周长 (Perimeter)' },
  { value: 'circularity', label: '圆度 (Circularity)' },
  { value: 'aspect_ratio', label: '长宽比 (Aspect Ratio)' },
  { value: 'distance', label: '位移距离 (Distance)' },
  { value: 'migration_speed', label: '迁移速度 (Migration Speed)' },
  { value: 'mean_square_displacement', label: '平均平方位移 (MSD)' },
];

// 排序选项
const sortOptions = [
  { value: 'tracking_duration', label: '持续追踪度（帧数）' },
  { value: 'area', label: '面积' },
  { value: 'speed', label: '速度' },
  { value: 'circularity', label: '圆度' },
  { value: 'aspect_ratio', label: '长宽比' },
];

// ==========================================
// 1. 折线图参数配置
// ==========================================
const timeSeriesConfig = reactive({
  yAxisFeature: 'area',
  cellSelection: 'top' as 'top' | 'range' | 'all',
  sortBy: 'tracking_duration',
  topN: 10,
  cellRange: [1, 50] as [number, number],
  showAverage: false,
  lineType: 'smooth' as 'smooth' | 'line',
  showDataPoints: true,
});

// ==========================================
// 2. 直方图参数配置
// ==========================================
const histogramConfig = reactive({
  xAxisFeature: 'area',
  binCount: 10,
  statMode: 'average' as 'average' | 'frame',
  frameMode: 'single' as 'single' | 'quad',
  selectedFrame: 2,
  frameRange: [2, 100] as [number, number],
  showQuadGrid: false,
  selectedFrames: [2, 25, 50, 75] as number[],
  probabilityType: 'probability' as 'probability' | 'count',
});

// ==========================================
// 3. 散点图参数配置
// ==========================================
const scatterConfig = reactive({
  frameMode: 'single' as 'single' | 'quad' | 'sequence',
  selectedFrame: 2,
  selectedFrames: [2, 25, 50, 75] as number[],
  pointSize: 8,
  colorBy: 'cell_id' as 'cell_id' | 'area' | 'speed',
  showTrajectory: false,
  trajectoryLength: 10,
});

// ==========================================
// 4. 轨迹图参数配置
// ==========================================
const trajectoryConfig = reactive({
  trajectoryType: 'normal' as 'normal' | 'normalized' | '3d',
  colorMap: 'time' as 'time' | 'speed' | 'cell_id',
  cellSelection: 'top' as 'top' | 'range' | 'all',
  sortBy: 'tracking_duration',
  topN: 10,
  cellRange: [1, 50] as [number, number],
  lineWidth: 2,
  showStartPoint: false,
  showEndPoint: false,
  fadeEffect: false,
  normalizeOrigin: [0, 0] as [number, number],
});

// ==========================================
// 输入处理函数（解决TypeScript类型问题）
// ==========================================

// 直方图四帧输入处理
function handleHistogramFramesInput(event: Event) {
  const target = event.target as HTMLInputElement;
  if (!target) return;
  
  histogramConfig.selectedFrames = target.value
    .split(',')
    .map((s: string) => parseInt(s.trim(), 10))
    .filter((n: number) => !isNaN(n));
}

// 散点图四帧输入处理
function handleScatterFramesInput(event: Event) {
  const target = event.target as HTMLInputElement;
  if (!target) return;
  
  scatterConfig.selectedFrames = target.value
    .split(',')
    .map((s: string) => parseInt(s.trim(), 10))
    .filter((n: number) => !isNaN(n));
}

// 打开弹窗
function openModal(chartType: keyof typeof modalStates.value) {
  if (!selectedTaskId.value) {
    alert('请先选择一个分析任务');
    return;
  }
  modalStates.value[chartType] = true;
}

// 关闭弹窗
function closeModal(chartType: keyof typeof modalStates.value) {
  modalStates.value[chartType] = false;
}

// 跳转到绘图页面
function goToDrawingCanvas(chartType: string, config: any) {
  sessionStorage.setItem('returnToChart', 'true')
  router.push({
    name: 'drawingCanvas',
    query: {
      type: chartType,
      taskId: selectedTaskId.value || '',
      config: JSON.stringify(config),
    },
  });
}

// 生成图表按钮处理
function generateTimeSeries() {
  goToDrawingCanvas('timeSeries', timeSeriesConfig);
}

function generateHistogram() {
  goToDrawingCanvas('histogram', histogramConfig);
}

function generateScatter() {
  goToDrawingCanvas('scatter', scatterConfig);
}

function generateTrajectory() {
  goToDrawingCanvas('trajectory', trajectoryConfig);
}
</script>

<template>
  <div class="content">
    <div class="header">
      <h2>图表绘制</h2>
      <p class="subtitle">
        当前任务: {{ selectedTaskId ? analysisStore.selectedRecord?.video_name : '未选择' }}
      </p>
    </div>

    <div class="container">
      <!-- 折线图 -->
      <div class="card" @click="openModal('timeSeries')">
        <div class="image-box">
          <img src="./imgs/timeseries/1.png" alt="折线图" />
        </div>
        <p class="title">折线图</p>
        <p class="desc">细胞特征随时间变化趋势</p>
      </div>

      <!-- 直方图 -->
      <div class="card" @click="openModal('histogram')">
        <div class="image-box">
          <img src="./imgs/histogram/1.png" alt="直方图" />
        </div>
        <p class="title">直方图</p>
        <p class="desc">细胞特征概率分布</p>
      </div>

      <!-- 散点图 -->
      <div class="card" @click="openModal('scatter')">
        <div class="image-box">
          <img src="./imgs/scatter/1.png" alt="散点图" />
        </div>
        <p class="title">散点图</p>
        <p class="desc">细胞空间位置分布</p>
      </div>

      <!-- 轨迹图 -->
      <div class="card" @click="openModal('trajectory')">
        <div class="image-box">
          <img src="./imgs/trajectory/1.png" alt="轨迹图" />
        </div>
        <p class="title">轨迹图</p>
        <p class="desc">细胞运动轨迹可视化</p>
      </div>
    </div>

    <!-- ==================== 折线图弹窗 ==================== -->
    <div v-if="modalStates.timeSeries" class="modal" @click.self="closeModal('timeSeries')">
      <div class="modal-content">
        <div class="modal-header">
          <h3>折线图配置</h3>
          <span class="close" @click="closeModal('timeSeries')">&times;</span>
        </div>

        <div class="modal-body">
          <div class="form-section">
            <h4>Y轴设置</h4>
            <div class="form-item">
              <label>特征指标</label>
              <select v-model="timeSeriesConfig.yAxisFeature">
                <option v-for="feat in cellFeatures" :key="feat.value" :value="feat.value">
                  {{ feat.label }}
                </option>
              </select>
            </div>
          </div>

          <div class="form-section">
            <h4>细胞选择</h4>
            <div class="form-item">
              <label>选择方式</label>
              <div class="radio-group">
                <label class="radio-label">
                  <input type="radio" v-model="timeSeriesConfig.cellSelection" value="top">
                  <span>Top N 排序</span>
                </label>
                <label class="radio-label">
                  <input type="radio" v-model="timeSeriesConfig.cellSelection" value="range">
                  <span>ID范围</span>
                </label>
                <label class="radio-label">
                  <input type="radio" v-model="timeSeriesConfig.cellSelection" value="all">
                  <span>全部细胞</span>
                </label>
              </div>
            </div>

            <!-- Top N 配置 -->
            <div v-if="timeSeriesConfig.cellSelection === 'top'" class="sub-form">
              <div class="form-item">
                <label>排序依据</label>
                <select v-model="timeSeriesConfig.sortBy">
                  <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </option>
                </select>
              </div>
              <div class="form-item">
                <label>Top N 数量: {{ timeSeriesConfig.topN }}</label>
                <input type="range" v-model.number="timeSeriesConfig.topN" min="1" max="50" />
              </div>
            </div>

            <!-- ID范围配置 -->
            <div v-if="timeSeriesConfig.cellSelection === 'range'" class="sub-form">
              <div class="form-item range-inputs">
                <label>细胞ID范围</label>
                <input type="number" v-model.number="timeSeriesConfig.cellRange[0]" placeholder="起始ID" />
                <span>至</span>
                <input type="number" v-model.number="timeSeriesConfig.cellRange[1]" placeholder="结束ID" />
              </div>
            </div>
          </div>

          <div class="form-section">
            <h4>显示选项</h4>
            <div class="form-item checkbox-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="timeSeriesConfig.showAverage">
                <span>显示群体平均线</span>
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="timeSeriesConfig.showDataPoints">
                <span>显示数据点标记</span>
              </label>
            </div>
            <div class="form-item">
              <label>线条样式</label>
              <select v-model="timeSeriesConfig.lineType">
                <option value="smooth">平滑曲线</option>
                <option value="line">折线</option>
              </select>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-secondary" @click="closeModal('timeSeries')">取消</button>
          <button class="btn-primary" @click="generateTimeSeries">生成图表</button>
        </div>
      </div>
    </div>

    <!-- ==================== 直方图弹窗 ==================== -->
    <div v-if="modalStates.histogram" class="modal" @click.self="closeModal('histogram')">
      <div class="modal-content">
        <div class="modal-header">
          <h3>直方图配置</h3>
          <span class="close" @click="closeModal('histogram')">&times;</span>
        </div>

        <div class="modal-body">
          <div class="form-section">
            <h4>X轴设置</h4>
            <div class="form-item">
              <label>特征指标</label>
              <select v-model="histogramConfig.xAxisFeature">
                <option v-for="feat in cellFeatures" :key="feat.value" :value="feat.value">
                  {{ feat.label }}
                </option>
              </select>
            </div>
            <div class="form-item">
              <label>分箱数量: {{ histogramConfig.binCount }}</label>
              <input type="range" v-model.number="histogramConfig.binCount" min="5" max="50" />
            </div>
          </div>

          <div class="form-section">
            <h4>统计模式</h4>
            <div class="form-item">
              <label>数据聚合方式</label>
              <div class="radio-group">
                <label class="radio-label">
                  <input type="radio" v-model="histogramConfig.statMode" value="average">
                  <span>全时段平均</span>
                </label>
                <label class="radio-label">
                  <input type="radio" v-model="histogramConfig.statMode" value="frame">
                  <span>逐帧统计</span>
                </label>
              </div>
            </div>

            <!-- 逐帧配置 -->
            <div v-if="histogramConfig.statMode === 'frame'" class="sub-form">
              <div class="form-item">
                <label>展示形式</label>
                <div class="radio-group">
                  <label class="radio-label">
                    <input type="radio" v-model="histogramConfig.frameMode" value="single">
                    <span>单帧</span>
                  </label>
                  <label class="radio-label">
                    <input type="radio" v-model="histogramConfig.frameMode" value="quad">
                    <span>四宫格</span>
                  </label>
                </div>
              </div>

              <div v-if="histogramConfig.frameMode === 'single'" class="form-item">
                <label>选择帧号</label>
                <input type="number" v-model.number="histogramConfig.selectedFrame" min="1" />
              </div>

              <div v-if="histogramConfig.frameMode === 'quad'" class="form-item">
                <label>四帧选择（逗号分隔）</label>
                <input type="text" 
                :value="histogramConfig.selectedFrames.join(', ')"
                @input="handleHistogramFramesInput" 
                placeholder="如: 1, 25, 50, 75" 
                />
              </div>
            </div>
          </div>

          <div class="form-section">
            <h4>Y轴设置</h4>
            <div class="form-item">
              <label>数值类型</label>
              <select v-model="histogramConfig.probabilityType">
                <option value="probability">分布概率（推荐）</option>
                <option value="count">频数统计</option>
              </select>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-secondary" @click="closeModal('histogram')">取消</button>
          <button class="btn-primary" @click="generateHistogram">生成图表</button>
        </div>
      </div>
    </div>

    <!-- ==================== 散点图弹窗 ==================== -->
    <div v-if="modalStates.scatter" class="modal" @click.self="closeModal('scatter')">
      <div class="modal-content">
        <div class="modal-header">
          <h3>散点图配置</h3>
          <span class="close" @click="closeModal('scatter')">&times;</span>
        </div>

        <div class="modal-body">
          <div class="form-section">
            <h4>展示模式</h4>
            <div class="form-item">
              <label>帧展示方式</label>
              <div class="radio-group">
                <label class="radio-label">
                  <input type="radio" v-model="scatterConfig.frameMode" value="single">
                  <span>单帧展示</span>
                </label>
                <label class="radio-label">
                  <input type="radio" v-model="scatterConfig.frameMode" value="quad">
                  <span>四宫格对比</span>
                </label>
                <label class="radio-label">
                  <input type="radio" v-model="scatterConfig.frameMode" value="sequence">
                  <span>连续播放</span>
                </label>
              </div>
            </div>

            <div v-if="scatterConfig.frameMode === 'single'" class="form-item">
              <label>选择帧号</label>
              <input type="number" v-model.number="scatterConfig.selectedFrame" min="1" />
            </div>

            <div v-if="scatterConfig.frameMode === 'quad'" class="form-item">
              <label>四帧选择（逗号分隔）</label>
              <input type="text" 
              :value="scatterConfig.selectedFrames.join(', ')" 
              @input="handleScatterFramesInput"
              placeholder="如: 1, 25, 50, 75" 
              />
            </div>
          </div>

          <div class="form-section">
            <h4>视觉设置</h4>
            <div class="form-item">
              <label>点大小: {{ scatterConfig.pointSize }}px</label>
              <input type="range" v-model.number="scatterConfig.pointSize" min="3" max="20" />
            </div>
            <div class="form-item">
              <label>着色依据</label>
              <select v-model="scatterConfig.colorBy">
                <option value="cell_id">细胞ID（区分不同细胞）</option>
                <option value="area">细胞面积</option>
                <option value="speed">细胞速度</option>
              </select>
            </div>
          </div>

          <div class="form-section">
            <h4>轨迹叠加</h4>
            <div class="form-item checkbox-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="scatterConfig.showTrajectory">
                <span>显示历史轨迹</span>
              </label>
            </div>
            <div v-if="scatterConfig.showTrajectory" class="sub-form">
              <div class="form-item">
                <label>轨迹长度（帧）: {{ scatterConfig.trajectoryLength }}</label>
                <input type="range" v-model.number="scatterConfig.trajectoryLength" min="3" max="30" />
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-secondary" @click="closeModal('scatter')">取消</button>
          <button class="btn-primary" @click="generateScatter">生成图表</button>
        </div>
      </div>
    </div>

    <!-- ==================== 轨迹图弹窗 ==================== -->
    <div v-if="modalStates.trajectory" class="modal" @click.self="closeModal('trajectory')">
      <div class="modal-content">
        <div class="modal-header">
          <h3>轨迹图配置</h3>
          <span class="close" @click="closeModal('trajectory')">&times;</span>
        </div>

        <div class="modal-body">
          <div class="form-section">
            <h4>轨迹类型</h4>
            <div class="form-item">
              <label>可视化模式</label>
              <div class="radio-group vertical">
                <label class="radio-label">
                  <input type="radio" v-model="trajectoryConfig.trajectoryType" value="normal">
                  <div class="radio-content">
                    <strong>普通轨迹图</strong>
                    <span class="radio-desc">原始坐标系中的真实运动路径</span>
                  </div>
                </label>
                <label class="radio-label">
                  <input type="radio" v-model="trajectoryConfig.trajectoryType" value="normalized">
                  <div class="radio-content">
                    <strong>起点归一化轨迹</strong>
                    <span class="radio-desc">所有细胞从同一起点(0,0)开始，便于对比运动模式</span>
                  </div>
                </label>
                <label class="radio-label">
                  <input type="radio" v-model="trajectoryConfig.trajectoryType" value="3d">
                  <div class="radio-content">
                    <strong>三维轨迹图</strong>
                    <span class="radio-desc">X-Y位置 + 时间维度的3D可视化</span>
                  </div>
                </label>
              </div>
            </div>
          </div>

          <div class="form-section">
            <h4>细胞选择</h4>
            <div class="form-item">
              <label>选择方式</label>
              <div class="radio-group">
                <label class="radio-label">
                  <input type="radio" v-model="trajectoryConfig.cellSelection" value="top">
                  <span>Top N 排序</span>
                </label>
                <label class="radio-label">
                  <input type="radio" v-model="trajectoryConfig.cellSelection" value="range">
                  <span>ID范围</span>
                </label>
                <label class="radio-label">
                  <input type="radio" v-model="trajectoryConfig.cellSelection" value="all">
                  <span>全部细胞</span>
                </label>
              </div>
            </div>

            <!-- Top N 配置 -->
            <div v-if="trajectoryConfig.cellSelection === 'top'" class="sub-form">
              <div class="form-item">
                <label>排序依据</label>
                <select v-model="trajectoryConfig.sortBy">
                  <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </option>
                </select>
              </div>
              <div class="form-item">
                <label>Top N 数量: {{ trajectoryConfig.topN }}</label>
                <input type="range" v-model.number="trajectoryConfig.topN" min="1" max="50" />
              </div>
            </div>

            <!-- ID范围配置 -->
            <div v-if="trajectoryConfig.cellSelection === 'range'" class="sub-form">
              <div class="form-item range-inputs">
                <label>细胞ID范围</label>
                <input type="number" v-model.number="trajectoryConfig.cellRange[0]" placeholder="起始ID" />
                <span>至</span>
                <input type="number" v-model.number="trajectoryConfig.cellRange[1]" placeholder="结束ID" />
              </div>
            </div>
          </div>

          <div class="form-section">
            <h4>视觉样式</h4>
            <div class="form-item">
              <label>颜色映射</label>
              <select v-model="trajectoryConfig.colorMap">
                <option value="time">时间渐变（推荐）</option>
                <option value="speed">速度映射</option>
                <option value="cell_id">细胞ID区分</option>
              </select>
            </div>
            <div class="form-item">
              <label>轨迹线宽: {{ trajectoryConfig.lineWidth }}px</label>
              <input type="range" v-model.number="trajectoryConfig.lineWidth" min="1" max="5" />
            </div>
            <div class="form-item checkbox-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="trajectoryConfig.showStartPoint">
                <span>标记起点（绿色）</span>
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="trajectoryConfig.showEndPoint">
                <span>标记终点（红色）</span>
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="trajectoryConfig.fadeEffect">
                <span>时间渐隐效果</span>
              </label>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-secondary" @click="closeModal('trajectory')">取消</button>
          <button class="btn-primary" @click="generateTrajectory">生成图表</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.content {
  min-height: 100vh;
  background-color: var(--bg-main);
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.header {
  margin-bottom: 32px;
  text-align: center;
}

.header h2 {
  color: var(--text-primary);
  font-size: 28px;
  margin-bottom: 8px;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
}

.container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 24px;
  padding: 24px;
  background-color: var(--bg-card);
  border: 2px solid var(--border-color);
  border-radius: 12px;
  max-width: 800px;
}

.card {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  background-color: var(--bg-card);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s, box-shadow 0.2s;
  padding: 16px;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.image-box {
  width: 100%;
  height: 180px;
  background-color: var(--bg-input);
  border: 2px solid var(--accent-blue);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.image-box img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 10px;
}

.title {
  margin-top: 12px;
  font-size: 18px;
  color: var(--text-primary);
  font-weight: 600;
}

.desc {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

/* 弹窗样式 */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--bg-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background-color: var(--bg-dialog);
  border-radius: 16px;
  width: 100%;
  max-width: 520px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  color: var(--text-primary);
  font-size: 20px;
  margin: 0;
}

.close {
  font-size: 28px;
  cursor: pointer;
  color: var(--text-secondary);
  line-height: 1;
  transition: color 0.2s;
}

.close:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--border-color);
  background-color: var(--bg-card);
}

/* 表单样式 */
.form-section {
  margin-bottom: 24px;
}

.form-section:last-child {
  margin-bottom: 0;
}

.form-section h4 {
  color: var(--text-primary);
  font-size: 14px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}

.form-item {
  margin-bottom: 16px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-item label {
  display: block;
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: 6px;
}

.form-item select,
.form-item input[type="number"],
.form-item input[type="text"] {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background-color: var(--bg-input);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.form-item select:focus,
.form-item input:focus {
  border-color: var(--accent-blue);
}

.form-item input[type="range"] {
  width: 100%;
  margin-top: 4px;
}

/* 单选按钮组 */
.radio-group {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.radio-group.vertical {
  flex-direction: column;
  gap: 12px;
}

.radio-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: var(--text-primary);
  font-size: 14px;
}

.radio-label input[type="radio"] {
  margin-right: 6px;
  cursor: pointer;
}

.radio-content {
  display: flex;
  flex-direction: column;
  margin-left: 4px;
}

.radio-content strong {
  font-weight: 500;
  color: var(--text-primary);
}

.radio-desc {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

/* 复选框组 */
.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: var(--text-primary);
  font-size: 14px;
}

.checkbox-label input[type="checkbox"] {
  margin-right: 8px;
  cursor: pointer;
}

/* 子表单 */
.sub-form {
  margin-top: 12px;
  padding: 12px;
  background-color: var(--bg-main);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

/* 范围输入 */
.range-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-inputs input {
  flex: 1;
}

.range-inputs span {
  color: var(--text-secondary);
  font-size: 13px;
}

/* 按钮 */
.btn-primary,
.btn-secondary {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background-color: var(--accent-blue);
  color: white;
}

.btn-primary:hover {
  background-color: var(--accent-blue-hover, #3a8bc7);
}

.btn-secondary {
  background-color: var(--bg-input);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background-color: var(--bg-main);
}

/* 响应式 */
@media (max-width: 640px) {
  .container {
    grid-template-columns: 1fr;
    grid-template-rows: repeat(4, auto);
  }

  .modal-content {
    max-width: 100%;
    max-height: 90vh;
    margin: 10px;
  }

  .radio-group {
    flex-direction: column;
    gap: 8px;
  }
}
</style>