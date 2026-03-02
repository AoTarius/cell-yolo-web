import { createRouter, createWebHistory } from 'vue-router'
import CellTrackingView from '../views/CellTrackingView.vue'
import ProgressView from '../views/ProgressView.vue'
import ModelUploadView from '../views/ModelUploadView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
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
  ],
})

export default router
