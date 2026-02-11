<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
    <main class="container mx-auto px-4 py-16">
      <div class="max-w-4xl mx-auto text-center">
        <h1 class="text-5xl font-bold text-gray-900 mb-6">
          Vue 3 + Django 全栈项目
        </h1>
        <p class="text-xl text-gray-600 mb-12">
          现代化前后端分离架构，快速开发企业级应用
        </p>

        <div class="bg-white rounded-2xl shadow-xl p-8 mb-8">
          <h2 class="text-2xl font-semibold text-gray-800 mb-6">
            后端 API 连接测试
          </h2>
          <button
            @click="testBackend"
            class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors mb-4"
          >
            测试后端连接
          </button>
          <div v-if="apiResponse" class="mt-4 p-4 bg-green-50 rounded-lg">
            <p class="text-green-800">{{ apiResponse.message }}</p>
            <p class="text-sm text-green-600 mt-2">状态: {{ apiResponse.status }}</p>
          </div>
          <div v-if="errorMessage" class="mt-4 p-4 bg-red-50 rounded-lg">
            <p class="text-red-800">{{ errorMessage }}</p>
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-xl p-8">
          <h2 class="text-2xl font-semibold text-gray-800 mb-6">
            技术栈
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
            <div>
              <h3 class="text-lg font-semibold text-gray-700 mb-3">前端</h3>
              <ul class="space-y-2 text-gray-600">
                <li>• Vue 3 (Composition API)</li>
                <li>• TypeScript</li>
                <li>• Vite</li>
                <li>• TailwindCSS v4</li>
                <li>• Pinia</li>
                <li>• Vue Router</li>
                <li>• Axios</li>
              </ul>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-gray-700 mb-3">后端</h3>
              <ul class="space-y-2 text-gray-600">
                <li>• Django 5.1+</li>
                <li>• Django REST Framework</li>
                <li>• SQLite (开发)</li>
                <li>• django-cors-headers</li>
                <li>• python-dotenv</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'

const apiResponse = ref<any>(null)
const errorMessage = ref<string>('')

const testBackend = async () => {
  apiResponse.value = null
  errorMessage.value = ''

  try {
    const response = await axios.get('/api/test/')
    apiResponse.value = response.data
  } catch (error) {
    errorMessage.value = '后端连接失败，请确保 Django 服务已启动 (python manage.py runserver)'
  }
}
</script>
