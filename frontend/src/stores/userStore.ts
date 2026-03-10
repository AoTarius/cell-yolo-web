import { ref } from 'vue'
import { defineStore } from 'pinia'

export interface User {
  username: string
  email?: string
}

export const useUserStore = defineStore('user', () => {
  // 当前登录用户
  const currentUser = ref<User | null>(null)

  // 登录
  function login(username: string) {
    currentUser.value = {
      username,
    }
    // 保存到 localStorage
    localStorage.setItem('currentUser', JSON.stringify({ username }))
  }

  // 登出
  function logout() {
    currentUser.value = null
    localStorage.removeItem('currentUser')
  }

  // 从 localStorage 恢复用户信息
  function restoreUser() {
    const savedUser = localStorage.getItem('currentUser')
    if (savedUser) {
      try {
        currentUser.value = JSON.parse(savedUser)
      } catch (e) {
        console.error('恢复用户信息失败:', e)
      }
    }
  }

  // 初始化时恢复用户信息
  restoreUser()

  return {
    currentUser,
    login,
    logout,
  }
})