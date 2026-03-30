<template>
  <div
    class="floating-window"
    :style="{ transform: `translate(${position.x}px, ${position.y}px)` }"
  >
    <!-- 悬浮按钮区域 -->
    <div
      class="floating-buttons"
      @mousedown="startDrag"
      @touchstart.prevent="startDrag"
    >
      <!-- 机器人按钮 -->
      <div class="window-icon" @click="toggleChat">
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <!-- 机器人头部 -->
          <rect x="5" y="3" width="14" height="16" rx="3" stroke="currentColor" stroke-width="2"/>
          <!-- 眼睛 -->
          <circle cx="9" cy="9" r="1.5" fill="currentColor"/>
          <circle cx="15" cy="9" r="1.5" fill="currentColor"/>
          <!-- 天线 -->
          <line x1="12" y1="3" x2="12" y2="1" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <circle cx="12" cy="1" r="1" fill="currentColor"/>
          <!-- 嘴巴 -->
          <path d="M8 14C8 14 10 15.5 12 15.5C14 15.5 16 14 16 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          <!-- 耳朵/天线 -->
          <line x1="5" y1="8" x2="3" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <line x1="19" y1="8" x2="21" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </div>

      <!-- 拖拽手柄 -->
      <div class="window-handle">
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <line x1="4" y1="6" x2="20" y2="6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <line x1="4" y1="12" x2="20" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <line x1="4" y1="18" x2="20" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </div>
    </div>

    <!-- AI对话窗口 -->
    <Transition name="slide-up">
      <div v-if="isExpanded" class="chat-window" @click.stop>

        <!-- 消息列表 -->
        <div class="chat-messages">
          <MessageList />
        </div>

        <!-- 输入区域 -->
        <div class="chat-input">
          <ChatInput />
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import MessageList from '@/components/ai/MessageList.vue'
import ChatInput from '@/components/ai/ChatInput.vue'

const position = reactive({ x: (typeof window !== 'undefined' ? window.innerWidth : 0) - 128, y: (typeof window !== 'undefined' ? window.innerHeight : 0) / 8 })
const isExpanded = ref(false)
const isDragging = ref(false)
const dragOffset = reactive({ x: 0, y: 0 })

const startDrag = (e: MouseEvent | TouchEvent) => {
  isDragging.value = true

  let clientX: number
  let clientY: number

  if ('touches' in e && e.touches[0]) {
    clientX = e.touches[0].clientX
    clientY = e.touches[0].clientY
  } else {
    const mouseEvent = e as MouseEvent
    clientX = mouseEvent.clientX
    clientY = mouseEvent.clientY
  }

  dragOffset.x = clientX - position.x
  dragOffset.y = clientY - position.y

  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.addEventListener('touchmove', onDrag, { passive: false })
  document.addEventListener('touchend', stopDrag)
}

const onDrag = (e: MouseEvent | TouchEvent) => {
  if (!isDragging.value) return

  let clientX: number
  let clientY: number

  if ('touches' in e && e.touches[0]) {
    clientX = e.touches[0].clientX
    clientY = e.touches[0].clientY
  } else {
    const mouseEvent = e as MouseEvent
    clientX = mouseEvent.clientX
    clientY = mouseEvent.clientY
  }

  let newX = clientX - dragOffset.x
  let newY = clientY - dragOffset.y

  // 边界检测：确保不超出屏幕
  const windowWidth = typeof window !== 'undefined' ? window.innerWidth : 0
  const windowHeight = typeof window !== 'undefined' ? window.innerHeight : 0
  const buttonSize = 64
  const chatWidth = 320
  const chatHeight = 450

  if (isExpanded.value) {
    // 展开时考虑对话窗口的尺寸
    newX = Math.max(0, Math.min(newX, windowWidth - chatWidth))
    newY = Math.max(0, Math.min(newY, windowHeight - chatHeight))
  } else {
    // 未展开时只有按钮
    newX = Math.max(0, Math.min(newX, windowWidth - buttonSize))
    newY = Math.max(0, Math.min(newY, windowHeight - buttonSize))
  }

  position.x = newX
  position.y = newY

  if ('preventDefault' in e) {
    e.preventDefault()
  }
}

const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
}

const toggleChat = () => {
  if (!isDragging.value) {
    isExpanded.value = !isExpanded.value
  }
}

const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  const windowElement = document.querySelector('.floating-window')
  if (windowElement && !windowElement.contains(target)) {
    isExpanded.value = false
  }
}

const handleResize = () => {
  if (typeof window !== 'undefined') {
    position.x = window.innerWidth - 64
    position.y = window.innerHeight / 2 - 16
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
})
</script>

<style scoped>
.floating-window {
  position: fixed;
  z-index: 9999;
  cursor: move;
  user-select: none;
  transition: transform 0.1s ease-out;
}

/* 悬浮按钮区域 */
.floating-buttons {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: white;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.window-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
  cursor: pointer;
  flex-shrink: 0;
}

.window-icon:hover {
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.6);
  transform: scale(1.05);
}

.window-handle {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--bg-sidebar, #adadad);
  color: var(--text-primary, #333);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.window-handle:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25);
  transform: scale(1.05);
}

/* AI对话窗口 */
.chat-window {
  position: absolute;
  top: 52px;
  right: 0;
  width: 640px;
  height: 450px;
  background: var(--bg-hover);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  padding-top: 40px;
}

.chat-input {
  padding: 12px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-hover  );
}

/* 动画 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>