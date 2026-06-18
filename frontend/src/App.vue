<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const navItems = [
  { path: '/', title: '概览', icon: '📊' },
  { path: '/generate', title: '生成内容', icon: '✍️' },
  { path: '/style', title: '风格学习', icon: '🎨' },
  { path: '/settings', title: '设置', icon: '⚙️' },
]

const currentTitle = computed(() => {
  const item = navItems.find(n => n.path === route.path)
  return item ? item.title : 'XHS Loop Engineer'
})
</script>

<template>
  <div class="min-h-screen flex">
    <!-- Sidebar -->
    <aside class="w-60 bg-slate-900 border-r border-slate-800 flex flex-col fixed h-full">
      <div class="p-6 border-b border-slate-800">
        <h1 class="text-xl font-bold text-brand">🎯 班味克星</h1>
        <p class="text-xs text-slate-500 mt-1">XHS Loop Engineer</p>
      </div>
      <nav class="flex-1 p-3 space-y-1">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
          active-class="bg-brand/10 text-brand border-l-2 border-brand"
        >
          <span class="text-lg">{{ item.icon }}</span>
          <span class="font-medium">{{ item.title }}</span>
        </RouterLink>
      </nav>
      <div class="p-4 border-t border-slate-800 text-xs text-slate-500">
        v0.1.0 · Loop Engineering
      </div>
    </aside>

    <!-- Main -->
    <main class="flex-1 ml-60">
      <header class="sticky top-0 z-10 bg-slate-950/80 backdrop-blur border-b border-slate-800 px-8 py-4">
        <h2 class="text-2xl font-semibold text-white">{{ currentTitle }}</h2>
      </header>
      <div class="p-8">
        <RouterView />
      </div>
    </main>
  </div>
</template>
