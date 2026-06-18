<script setup>
import { ref, onMounted } from 'vue'
import { articlesApi } from '@/api'

const stats = ref(null)
const articles = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    [stats.value, articles.value] = await Promise.all([
      articlesApi.stats(),
      articlesApi.list(),
    ])
  } finally {
    loading.value = false
  }
})

function typeLabel(t) {
  return t === 'deep_tech' ? '深度稿' : '小白文'
}
</script>

<template>
  <div v-if="loading" class="text-slate-500">加载中...</div>

  <div v-else class="space-y-6">
    <!-- Stat cards -->
    <div class="grid grid-cols-4 gap-4">
      <div class="card">
        <p class="text-sm text-slate-400">已发文章</p>
        <p class="text-3xl font-bold text-white mt-2">{{ stats?.total_articles ?? 0 }}</p>
      </div>
      <div class="card">
        <p class="text-sm text-slate-400">小白文</p>
        <p class="text-3xl font-bold text-emerald-400 mt-2">{{ stats?.xiaobai_count ?? 0 }}</p>
      </div>
      <div class="card">
        <p class="text-sm text-slate-400">技术深度稿</p>
        <p class="text-3xl font-bold text-sky-400 mt-2">{{ stats?.deep_tech_count ?? 0 }}</p>
      </div>
      <div class="card">
        <p class="text-sm text-slate-400">风格库样本</p>
        <p class="text-3xl font-bold text-brand mt-2">
          {{ stats?.style_sample_size ?? 0 }}
          <span class="text-sm text-slate-500 font-normal">篇</span>
        </p>
        <p class="text-xs text-slate-500 mt-1">
          <span v-if="stats?.style_profile_loaded" class="badge badge-green">已加载</span>
          <span v-else class="badge badge-yellow">未学习</span>
        </p>
      </div>
    </div>

    <!-- Quick action -->
    <div class="card flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-white">生成新文章</h3>
        <p class="text-sm text-slate-400 mt-1">选个选题，让 AI 帮你写一篇</p>
      </div>
      <RouterLink to="/generate" class="btn-primary">立即生成 →</RouterLink>
    </div>

    <!-- Recent articles -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">最新文章</h3>
      <div v-if="articles.length === 0" class="text-slate-500 text-sm">
        还没有发布的文章。
      </div>
      <div v-else class="divide-y divide-slate-800">
        <RouterLink
          v-for="a in articles.slice(0, 8)"
          :key="a.filename"
          to="/articles"
          class="flex items-center justify-between py-3 hover:bg-slate-800/50 -mx-2 px-2 rounded transition-colors"
        >
          <div class="flex-1 min-w-0">
            <p class="text-slate-100 truncate font-medium">{{ a.title }}</p>
            <p class="text-xs text-slate-500 mt-1">{{ a.filename }}</p>
          </div>
          <span :class="a.article_type === 'deep_tech' ? 'badge badge-blue' : 'badge badge-green'">
            {{ typeLabel(a.article_type) }}
          </span>
        </RouterLink>
      </div>
    </div>
  </div>
</template>
