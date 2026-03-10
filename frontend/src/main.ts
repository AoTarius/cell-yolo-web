import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

// 在应用挂载之前立即初始化主题，避免闪烁
const savedTheme = localStorage.getItem('theme')
if (savedTheme === 'light') {
  document.documentElement.classList.remove('dark')
} else {
  document.documentElement.classList.add('dark')
}

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
