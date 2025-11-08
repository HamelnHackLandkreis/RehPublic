import { createRouter, createWebHistory } from 'vue-router'
import MapPage from '@/pages/MapPage.vue'
import UploadPage from '@/pages/UploadPage.vue'
import GalleryPage from '@/pages/GalleryPage.vue'
import StatisticsPage from '@/pages/StatisticsPage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'map',
      component: MapPage
    },
    {
      path: '/upload',
      name: 'upload',
      component: UploadPage
    },
    {
      path: '/gallery',
      name: 'gallery',
      component: GalleryPage
    },
    {
      path: '/statistics',
      name: 'statistics',
      component: StatisticsPage
    }
  ]
})

export default router
