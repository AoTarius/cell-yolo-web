import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import CellTrackingView from '../views/CellTrackingView.vue'
import ProgressView from '../views/ProgressView.vue'
import ModelUploadView from '../views/ModelUploadView.vue'
import CompareView from '../views/CompareView.vue'
import CompareResult from '../components/compare/CompareResult.vue'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/',
      name: 'home',
      redirect: () => {
        const userStore = useUserStore()
        return userStore.currentUser ? '/cellTracking' : '/login'
      },
    },
    {
      path: '/cellTracking',
      name: 'cellTracking',
      component: CellTrackingView,
    },
    {
      path: '/progress/:taskId',
      name: 'progress',
      component: ProgressView,
    },
    {
      path: '/model-upload',
      name: 'modelUpload',
      component: ModelUploadView,
    },
    {
      path: '/compare',
      name: 'compare',
      component: CompareView,
    },
    {
      path: '/compare/result',
      name: 'compareResult',
      component: CompareResult,
    },
  ],
})

// 全局路由守卫
router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()

  // 如果访问的是根路径，根据登录状态重定向
  if (to.path === '/') {
    if (userStore.currentUser) {
      next('/cellTracking')
    } else {
      next('/login')
    }
    return
  }

  // 如果用户未登录且不是登录页，重定向到登录页
  if (!userStore.currentUser && to.path !== '/login') {
    next('/login')
    return
  }

  // 如果用户已登录且访问登录页，重定向到主页
  if (userStore.currentUser && to.path === '/login') {
    next('/cellTracking')
    return
  }

  next()
})

export default router
