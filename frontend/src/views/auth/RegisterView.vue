<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { authApi, type User } from '@/api/authApi'

const router = useRouter()

// 表单数据
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const modelBasePath = ref('')
const outputBasePath = ref('')
const showPathSettings = ref(false)

const hasCustomPaths = computed(() => {
  return !!modelBasePath.value.trim() || !!outputBasePath.value.trim()
})

const pathStatusText = computed(() => {
  if (hasCustomPaths.value) {
    return '当前：已自定义路径'
  }

  const userSegment = username.value.trim() || '{用户名}'
  return `当前：使用默认路径（项目根目录/.user-storage/${userSegment}/...）`
})

// 加载状态
const isLoading = ref(false)
const errorMessage = ref('')

// 主题切换
const isDark = ref(true)

// 初始化主题状态
onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  isDark.value = savedTheme !== 'light'
  applyTheme()
})

// 切换主题
function toggleTheme() {
  isDark.value = !isDark.value
  applyTheme()
}

function applyTheme() {
  if (isDark.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

// 表单处理
async function handleSubmit(event: Event) {
  event.preventDefault()
  errorMessage.value = ''

  // 验证输入
  if (!username.value.trim() || !password.value) {
    errorMessage.value = '用户名和密码不能为空'
    return
  }

  // 验证密码长度
  if (password.value.length < 6) {
    errorMessage.value = '密码长度至少为6位'
    return
  }

  // 验证密码确认
  if (password.value !== confirmPassword.value) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }

  isLoading.value = true

  try {
    // 调用后端注册 API
    const response = await authApi.register(
      username.value.trim(),
      password.value,
      modelBasePath.value.trim() || undefined,
      outputBasePath.value.trim() || undefined
    )

    if (response.status === 'success' && response.user) {
      // 注册成功，跳转到登录页面
      errorMessage.value = ''
      alert('注册成功！请登录')
      router.push('/login')
    } else {
      errorMessage.value = '注册失败，请重试'
    }
  } catch (error: any) {
    console.error('Register error:', error)

    // 处理错误响应
    if (error.response?.data?.error) {
      errorMessage.value = error.response.data.error
    } else if (error.message) {
      errorMessage.value = error.message
    } else {
      errorMessage.value = '注册失败，请检查网络连接'
    }
  } finally {
    isLoading.value = false
  }
}

// 返回登录页面
function goToLogin() {
  router.push('/login')
}
</script>

<template>
  <div class="register-container">
    <!-- 主题切换按钮 -->
    <button class="theme-toggle" title="切换主题" @click="toggleTheme">
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

    <div class="register-card">
      <form @submit="handleSubmit">
        <h2>用户注册</h2>

        <!-- 错误消息 -->
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <div class="input-box">
          <input type="text" v-model="username" required :disabled="isLoading">
          <span>用户名</span>
          <i></i>
        </div>

        <div class="input-box">
          <input type="password" v-model="password" required :disabled="isLoading">
          <span>密码（至少6位）</span>
          <i></i>
        </div>

        <div class="input-box">
          <input type="password" v-model="confirmPassword" required :disabled="isLoading">
          <span>确认密码</span>
          <i></i>
        </div>

        <div class="path-settings">
          <button
            type="button"
            class="path-settings-toggle"
            :disabled="isLoading"
            @click="showPathSettings = !showPathSettings"
          >
            {{ showPathSettings ? '收起路径设置（可选）' : '展开路径设置（可选）' }}
          </button>
          <p class="path-settings-status">
            {{ pathStatusText }}
          </p>
          <p v-if="!showPathSettings" class="path-settings-hint">
            默认会在项目根目录下为当前用户自动创建被 gitignore 忽略的存储目录。
          </p>
          <template v-if="showPathSettings">
            <div class="input-box path-input-box">
              <input type="text" v-model="modelBasePath" :disabled="isLoading">
              <span>模型存储路径（留空使用默认）</span>
              <i></i>
            </div>

            <div class="input-box path-input-box">
              <input type="text" v-model="outputBasePath" :disabled="isLoading">
              <span>任务存储路径（留空使用默认）</span>
              <i></i>
            </div>
          </template>
        </div>

        <div class="links">
          <a href="#" @click.prevent="goToLogin">返回登录</a>
        </div>

        <div class="input-box">
          <input type="submit" :value="isLoading ? '注册中...' : '注册'" :disabled="isLoading">
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(45deg, var(--login-bg-gradient-start), var(--login-bg-gradient-end));
  position: relative;
  padding: 20px;
}

/* 主题切换按钮 */
.theme-toggle {
  position: absolute;
  top: 2rem;
  right: 2rem;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.theme-toggle:hover {
  background: var(--bg-hover);
  border-color: var(--border-hover);
  transform: scale(1.05);
}

.theme-toggle:active {
  transform: scale(0.95);
}

.theme-icon {
  width: 24px;
  height: 24px;
  transition: all 0.3s ease;
}

/* 注册卡片 */
.register-card {
  position: relative;
  padding: 50px;
  background: var(--login-card-bg);
  box-shadow: var(--login-card-shadow);
  max-width: 500px;
  width: 100%;
}

.register-card::before {
  content: "";
  position: absolute;
  left: -20px;
  top: 0;
  width: 20px;
  height: 100%;
  background: var(--login-border-before);
  transform: skewY(45deg);
  transform-origin: bottom right;
}

.register-card::after {
  content: "";
  position: absolute;
  top: -20px;
  left: 0;
  height: 20px;
  width: 100%;
  background: var(--login-border-after);
  transform: skewX(45deg);
  transform-origin: bottom right;
}

/* 表单样式 */
.register-card form {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}

.register-card h2 {
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.15em;
  margin-bottom: 20px;
  font-size: 1.5rem;
}

/* 错误消息 */
.error-message {
  width: 100%;
  padding: 12px;
  margin-bottom: 20px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  color: #ef4444;
  font-size: 0.9em;
  text-align: center;
  animation: shake 0.5s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

/* 输入框 */
.register-card .input-box {
  position: relative;
  width: 100%;
  margin-top: 30px;
}

.register-card .input-box input {
  position: relative;
  padding: 8px 10px;
  border: none;
  outline: none;
  width: 100%;
  background: transparent;
  color: var(--text-primary);
  font-size: 1.1em;
  letter-spacing: 0.1em;
  z-index: 2;
}

.register-card .input-box span {
  position: absolute;
  left: 0;
  padding: 10px 0;
  pointer-events: none;
  font-size: 1em;
  transition: 0.5s;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  text-transform: uppercase;
}

.register-card .input-box input:valid ~ span,
.register-card .input-box input:focus ~ span {
  color: var(--text-primary);
  font-size: 0.85em;
  transform: translateY(-32px);
}

.register-card .input-box i {
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 3px;
  background: var(--login-input-line-gradient);
  transform-origin: 0.5s;
  pointer-events: none;
  z-index: 1;
}

.register-card .input-box input:valid ~ i,
.register-card .input-box input:focus ~ i {
  height: 100%;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.25);
}

.register-card .input-box input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.path-settings {
  width: 100%;
  margin-top: 24px;
}

.path-settings-toggle {
  width: 100%;
  height: 42px;
  border: 1px solid var(--border-color);
  background: var(--bg-input);
  color: var(--text-primary);
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.path-settings-toggle:hover {
  background: var(--bg-hover);
  border-color: var(--border-hover);
}

.path-settings-toggle:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.path-settings-hint {
  margin: 10px 4px 0;
  color: var(--text-muted);
  font-size: 0.82rem;
  line-height: 1.5;
}

.path-settings-status {
  margin: 10px 4px 0;
  color: var(--text-secondary);
  font-size: 0.82rem;
  line-height: 1.4;
}

.path-input-box {
  margin-top: 18px;
}

/* 链接 */
.register-card .links {
  position: relative;
  width: 100%;
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.register-card .links a {
  text-decoration: none;
  color: var(--login-link-primary);
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.1em;
  font-size: 0.75em;
  transition: color 0.2s;
}

.register-card .links a:hover {
  color: var(--login-link-secondary);
}

/* 注册按钮 */
.register-card .input-box input[type="submit"] {
  background: var(--accent-blue);
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s;
}

.register-card .input-box input[type="submit"]:hover {
  background: var(--accent-blue-hover);
}

.register-card .input-box input[type="submit"]:active {
  background: var(--accent-blue);
}

.register-card .input-box input[type="submit"]:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 响应式设计 */
@media (max-width: 600px) {
  .register-card {
    padding: 30px;
  }

  .register-card .input-box {
    width: 100%;
  }
}
</style>