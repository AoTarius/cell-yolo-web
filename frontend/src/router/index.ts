import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import CellTrackingView from '../views/home/CellTrackingView.vue'
import UploadView from '../views/analysis/UploadView.vue'
import ProgressView from '../views/analysis/ProgressView.vue'
import ResourceView from '../views/resource/ResourceView.vue'
import CompareView from '../views/compare/CompareView.vue'
import CompareResult from '../components/compare/CompareResult.vue'
import LoginView from '../views/auth/LoginView.vue'
import RegisterView from '../views/auth/RegisterView.vue'
import ImportView from '../views/import/ImportView.vue'
import DrawingCanvas from '@/components/analysis/chart-drawing/DrawingCanvas.vue'
import FreePlotView from '../views/analysis/FreePlotView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
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
      path: '/upload',
      name: 'upload',
      component: UploadView,
    },
    {
      path: '/progress/:taskId',
      name: 'progress',
      component: ProgressView,
    },
    {
      path: '/resource-manage',
      name: 'resourceManage',
      component: ResourceView,
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
    {
      path: '/import',
      name: 'import',
      component: ImportView,
    },

    {
      path: '/drawing-canvas',
      name: 'drawingCanvas',
      component: DrawingCanvas
    },
    {
      path: '/free-plot',
      name: 'freePlot',
      component: FreePlotView,
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

  // 允许未登录用户访问登录页和注册页
  const publicRoutes = ['/login', '/register']

  // 如果用户未登录且不是公开页面，重定向到登录页
  if (!userStore.currentUser && !publicRoutes.includes(to.path)) {
    next('/login')
    return
  }

  // 如果用户已登录且访问登录页或注册页，重定向到主页
  if (userStore.currentUser && publicRoutes.includes(to.path)) {
    next('/cellTracking')
    return
  }

  next()
})

export default router