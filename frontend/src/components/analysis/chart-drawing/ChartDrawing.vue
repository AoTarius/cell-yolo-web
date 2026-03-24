<script setup lang="ts">
import '@/assets/styles/colors.css';
import { ref } from 'vue';

// 当前选中的图表
const selectedChart = ref<number>(1);

// 图表列表
const charts = [1, 2, 3, 4];

// 弹窗状态
const modalStates = ref({
  timeSeries: false,
  histogram: false,
  scatter: false,
  trajectory: false,
});

// 打开弹窗
function openModal(chartType: keyof typeof modalStates.value) {
  modalStates.value[chartType] = true;
}

// 关闭弹窗
function closeModal(chartType: keyof typeof modalStates.value) {
  modalStates.value[chartType] = false;
}
</script>

<template>
  <div class="content">
    <div class="container">
      <!-- 折线图 -->
      <div class="card" @click="openModal('timeSeries')">
        <div class="image-box">
          <img src="./imgs/timeseries/1.png" alt="折线图" />
        </div>
        <p class="title">折线图</p>
      </div>

      <!-- 直方图 -->
      <div class="card" @click="openModal('histogram')">
        <div class="image-box">
          <img src="./imgs/histogram/1.png" alt="直方图" />
        </div>
        <p class="title">直方图</p>
      </div>

      <!-- 散点图 -->
      <div class="card" @click="openModal('scatter')">
        <div class="image-box">
          <img src="./imgs/scatter/1.png" alt="散点图" />
        </div>
        <p class="title">散点图</p>
      </div>

      <!-- 轨迹图 -->
      <div class="card" @click="openModal('trajectory')">
        <div class="image-box">
          <img src="./imgs/trajectory/1.png" alt="轨迹图" />
        </div>
        <p class="title">轨迹图</p>
      </div>
    </div>

    <!-- 弹窗 -->
    <div v-if="modalStates.timeSeries" class="modal">
      <div class="modal-content">
        <span class="close" @click="closeModal('timeSeries')">&times;</span>
        <p>这是折线图的弹窗内容。</p>
      </div>
    </div>

    <div v-if="modalStates.histogram" class="modal">
      <div class="modal-content">
        <span class="close" @click="closeModal('histogram')">&times;</span>
        <p>这是直方图的弹窗内容。</p>
      </div>
    </div>

    <div v-if="modalStates.scatter" class="modal">
      <div class="modal-content">
        <span class="close" @click="closeModal('scatter')">&times;</span>
        <p>这是散点图的弹窗内容。</p>
      </div>
    </div>

    <div v-if="modalStates.trajectory" class="modal">
      <div class="modal-content">
        <span class="close" @click="closeModal('trajectory')">&times;</span>
        <p>这是轨迹图的弹窗内容。</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.content {
  height: 100vh;
  background-color: var(--bg-main);
  padding: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
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
}

.card:hover {
  transform: scale(1.05);
  box-shadow: var(--shadow-md);
}

.image-box {
  width: 100%;
  height: 200px;
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
  border-radius: 12px;
}

.title {
  margin-top: 12px;
  font-size: 16px;
  color: var(--text-primary);
  font-weight: normal;
  text-align: center;
}

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
}

.modal-content {
  background-color: var(--bg-dialog);
  padding: 30px;
  border-radius: 10px;
  width: 50%;
  max-width: 600px;
  height: 50%;
  max-height: 400px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-lg);
}

.close {
  position: absolute;
  top: 15px;
  right: 15px;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-primary);
}
</style>