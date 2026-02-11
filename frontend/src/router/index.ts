import { createRouter, createWebHistory } from 'vue-router'
import CellTrackingView from '../views/CellTrackingView.vue'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'cellTracking',
      component: CellTrackingView,
    },
    {
      path: '/test',
      name: 'test',
      component: HomeView ,
    },
  ],
})

export default router
