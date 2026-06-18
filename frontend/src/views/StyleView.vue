<script setup>
import { ref, onMounted } from 'vue'
import { styleApi } from '@/api'

const profile = ref(null)
const loading = ref(true)
const learning = ref(false)
const message = ref('')

const testText = ref('')
const testType = ref('xiaobai')
const testResult = ref(null)

onMounted(async () => {
  await refresh()
})

async function refresh() {
  loading.value = true
  try {
    profile.value = await styleApi.profile()
  } finally {
    loading.value = false
  }
}

async function handleLearn() {
  learning.value = true
  message.value = ''
  try {
    const r = await styleApi.learn()
    message.value = `✅ 已学习 ${r.profile.xiaobai?.sample_size || 0} 篇小白文 + ${r.profile.deep_tech?.sample_size || 0} 篇深度稿`
    await refresh()
  } catch (e) {
    message.value = '❌ 学习失败: ' + e.message
  } finally {
    learning.value = false
  }
}

async function handleTest() {
  if (!testText.value.trim()) return
  testResult.value = await styleApi.score({
    content: testText.value,
    article_type: testType.value,
  })
}

function fmtFloat(n) {
  if (n == null) return '-'
  return Number(n).toFixed(2)
}
</script>

<template>
  <div class="space-y-6 max-w-4xl">
    <!-- Status -->
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-white">风格库</h3>
        <button @click="handleLearn" :disabled="learning" class="btn-primary">
          {{ learning ? '学习中...' : '🔄 重新学习' }}
        </button>
      </div>

      <p v-if="message" class="text-sm text-slate-300 mb-4">{{ message }}</p>

      <div v-if="loading" class="text-slate-500">加载中...</div>

      <div v-else class="grid grid-cols-2 gap-4">
        <!-- Xiaobai profile -->
        <div class="p-4 bg-slate-800/50 rounded-lg">
          <div class="flex items-center justify-between mb-3">
            <h4 class="font-semibold text-emerald-400">📚 小白文</h4>
            <span class="badge badge-green">{{ profile?.xiaobai?.sample_size || 0 }} 篇</span>
          </div>
          <dl v-if="profile?.xiaobai?.sample_size" class="text-sm space-y-1 text-slate-300">
            <div class="flex justify-between"><dt>平均句长</dt><dd>{{ fmtFloat(profile.xiaobai.sent_length_mean) }} 字</dd></div>
            <div class="flex justify-between"><dt>Emoji 密度</dt><dd>{{ fmtFloat(profile.xiaobai.emoji_density) }}%</dd></div>
            <div class="flex justify-between"><dt>段落行数</dt><dd>{{ fmtFloat(profile.xiaobai.para_lines_mean) }}</dd></div>
            <div class="flex justify-between"><dt>Emoji 段落</dt><dd>{{ fmtFloat(profile.xiaobai.emoji_section_count) }} 个</dd></div>
            <div class="flex justify-between"><dt>句号占比</dt><dd>{{ fmtFloat(profile.xiaobai.punct_ratio?.['。'] * 100) }}%</dd></div>
            <div class="flex justify-between"><dt>问号占比</dt><dd>{{ fmtFloat(profile.xiaobai.punct_ratio?.['？'] * 100) }}%</dd></div>
          </dl>
          <p v-else class="text-slate-500 text-sm">暂无数据，点击"重新学习"提取你的风格</p>
        </div>

        <!-- Deep tech profile -->
        <div class="p-4 bg-slate-800/50 rounded-lg">
          <div class="flex items-center justify-between mb-3">
            <h4 class="font-semibold text-sky-400">📖 技术深度稿</h4>
            <span class="badge badge-blue">{{ profile?.deep_tech?.sample_size || 0 }} 篇</span>
          </div>
          <dl v-if="profile?.deep_tech?.sample_size" class="text-sm space-y-1 text-slate-300">
            <div class="flex justify-between"><dt>平均句长</dt><dd>{{ fmtFloat(profile.deep_tech.sent_length_mean) }} 字</dd></div>
            <div class="flex justify-between"><dt>Emoji 密度</dt><dd>{{ fmtFloat(profile.deep_tech.emoji_density) }}%</dd></div>
            <div class="flex justify-between"><dt>段落行数</dt><dd>{{ fmtFloat(profile.deep_tech.para_lines_mean) }}</dd></div>
            <div class="flex justify-between"><dt>Emoji 段落</dt><dd>{{ fmtFloat(profile.deep_tech.emoji_section_count) }} 个</dd></div>
            <div class="flex justify-between"><dt>句号占比</dt><dd>{{ fmtFloat(profile.deep_tech.punct_ratio?.['。'] * 100) }}%</dd></div>
            <div class="flex justify-between"><dt>问号占比</dt><dd>{{ fmtFloat(profile.deep_tech.punct_ratio?.['？'] * 100) }}%</dd></div>
          </dl>
          <p v-else class="text-slate-500 text-sm">暂无数据</p>
        </div>
      </div>
    </div>

    <!-- Test scorer -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">测试风格匹配</h3>

      <div class="space-y-3">
        <div>
          <label class="label">类型</label>
          <div class="flex gap-4">
            <label class="flex items-center gap-2 text-slate-200">
              <input v-model="testType" type="radio" value="xiaobai" class="accent-brand" /> 小白文
            </label>
            <label class="flex items-center gap-2 text-slate-200">
              <input v-model="testType" type="radio" value="deep_tech" class="accent-brand" /> 深度稿
            </label>
          </div>
        </div>

        <div>
          <label class="label">待测试文本</label>
          <textarea v-model="testText" rows="6" class="input font-mono text-sm" placeholder="把草稿贴进来测试..." />
        </div>

        <button @click="handleTest" class="btn-primary">🎯 评分</button>

        <div v-if="testResult" class="mt-4 p-4 bg-slate-800/50 rounded-lg">
          <p class="text-sm text-slate-400">总分</p>
          <p :class="testResult.passed ? 'text-emerald-400' : 'text-rose-400'" class="text-3xl font-bold">
            {{ testResult.score }}
            <span class="text-sm text-slate-500">/ 1.0 (阈值 {{ testResult.threshold }})</span>
          </p>

          <div v-if="testResult.dimension_scores" class="mt-4 space-y-2">
            <p class="text-sm text-slate-400">各维度：</p>
            <div v-for="(score, dim) in testResult.dimension_scores" :key="dim" class="flex items-center gap-3">
              <span class="text-sm text-slate-400 w-32">{{ dim }}</span>
              <div class="flex-1 bg-slate-700 rounded-full h-2 overflow-hidden">
                <div
                  :class="score > 0.7 ? 'bg-emerald-500' : score > 0.4 ? 'bg-amber-500' : 'bg-rose-500'"
                  class="h-full"
                  :style="{ width: (score * 100) + '%' }"
                />
              </div>
              <span class="text-sm text-slate-300 w-12 text-right">{{ fmtFloat(score) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
