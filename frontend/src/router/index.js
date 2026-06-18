import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'dashboard', component: () => import('@/views/DashboardView.vue'), meta: { title: '概览', icon: '📊' } },
  { path: '/generate', name: 'generate', component: () => import('@/views/GenerateView.vue'), meta: { title: '生成内容', icon: '✍️' } },
  { path: '/style', name: 'style', component: () => import('@/views/StyleView.vue'), meta: { title: '风格学习', icon: '🎨' } },
  { path: '/settings', name: 'settings', component: () => import('@/views/SettingsView.vue'), meta: { title: '设置', icon: '⚙️' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
