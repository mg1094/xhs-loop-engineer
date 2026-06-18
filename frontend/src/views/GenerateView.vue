<script setup>
import { ref, computed } from 'vue'
import { generateApi } from '@/api'

const topic = ref('')
const articleType = ref('xiaobai')
const backend = ref('openai')
const model = ref('qwen-max')
const apiBase = ref('https://dashscope.aliyuncs.com/compatible-mode/v1')
const apiKey = ref('')

const loading = ref(false)
const result = ref(null)
const error = ref('')

const showApiKey = ref(false)

async function handleGenerate() {
  if (!topic.value.trim()) {
    error.value = '请输入选题'
    return
  }
  error.value = ''
  loading.value = true
  result.value = null
  try {
    const payload = {
      topic: topic.value,
      article_type: articleType.value,
      backend: backend.value,
      model: model.value || null,
      api_base: apiBase.value || null,
      api_key: apiKey.value || null,
    }
    result.value = await generateApi.generate(payload)
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || '生成失败'
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (!result.value?.content) return
  try {
    await generateApi.save({
      topic: result.value.topic,
      content: result.value.content,
      article_type: result.value.article_type,
    })
    alert('✅ 已保存到 Obsidian 待发布目录')
  } catch (e) {
    alert('❌ 保存失败：' + (e.message || 'unknown'))
  }
}

const ruleCheck = computed(() => result.value?.rule_check || {})
const styleScore = computed(() => result.value?.style_score || {})
</script>

<template>
  <div class="space-y-6 max-w-4xl">
    <!-- Input form -->
    <div class="card space-y-4">
      <div class="grid grid-cols-2 gap-4">
        <div class="col-span-2">
          <label class="label">选题</label>
          <input v-model="topic" class="input" placeholder="例如：AI 写年终总结" />
        </div>

        <div>
          <label class="label">文章类型</label>
          <div class="flex gap-4 mt-2">
            <label class="flex items-center gap-2 text-slate-200">
              <input v-model="articleType" type="radio" value="xiaobai" class="accent-brand" />
              <span>小白文</span>
            </label>
            <label class="flex items-center gap-2 text-slate-200">
              <input v-model="articleType" type="radio" value="deep_tech" class="accent-brand" />
              <span>技术深度稿</span>
            </label>
          </div>
        </div>

        <div>
          <label class="label">LLM Provider</label>
          <select v-model="backend" class="input">
            <option value="openai">OpenAI 兼容 (豆包/Qwen/DeepSeek)</option>
            <option value="anthropic">Anthropic Claude</option>
            <option value="manual">手动模式 (返回 prompt)</option>
          </select>
        </div>

        <div>
          <label class="label">模型名称</label>
          <input v-model="model" class="input" placeholder="qwen-max / gpt-4o / claude-sonnet-4-6" />
        </div>

        <div>
          <label class="label">API Base (可选)</label>
          <input v-model="apiBase" class="input" placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1" />
        </div>

        <div class="col-span-2">
          <label class="label">API Key (可选，留空使用环境变量)</label>
          <div class="flex gap-2">
            <input v-model="apiKey" :type="showApiKey ? 'text' : 'password'" class="input" placeholder="sk-..." />
            <button @click="showApiKey = !showApiKey" type="button" class="btn-ghost">
              {{ showApiKey ? '隐藏' : '显示' }}
            </button>
          </div>
        </div>
      </div>

      <div class="flex gap-3 pt-2">
        <button @click="handleGenerate" :disabled="loading" class="btn-primary">
          {{ loading ? '⏳ 生成中...' : '🚀 生成文章' }}
        </button>
        <button v-if="result" @click="handleGenerate" :disabled="loading" class="btn-ghost">
          🔄 重新生成
        </button>
      </div>

      <p v-if="error" class="text-rose-400 text-sm">❌ {{ error }}</p>
    </div>

    <!-- Result -->
    <div v-if="result" class="card space-y-4">
      <!-- Validation -->
      <div class="grid grid-cols-2 gap-4">
        <div class="p-4 bg-slate-800/50 rounded-lg">
          <p class="text-sm text-slate-400">规则检查</p>
          <p :class="ruleCheck.pass ? 'text-emerald-400' : 'text-rose-400'" class="text-2xl font-bold mt-1">
            {{ ruleCheck.score ?? '-' }}/10
          </p>
          <span v-if="ruleCheck.pass" class="badge badge-green mt-1">通过</span>
          <span v-else class="badge badge-red mt-1">未通过</span>
        </div>
        <div class="p-4 bg-slate-800/50 rounded-lg">
          <p class="text-sm text-slate-400">风格匹配</p>
          <p :class="styleScore.passed ? 'text-emerald-400' : 'text-rose-400'" class="text-2xl font-bold mt-1">
            {{ styleScore.score ?? '-' }}
          </p>
          <span v-if="styleScore.passed" class="badge badge-green mt-1">像你</span>
          <span v-else-if="styleScore.reason === 'no_style_profile_yet'" class="badge badge-yellow mt-1">需先学习风格</span>
          <span v-else class="badge badge-red mt-1">不像你</span>
        </div>
      </div>

      <!-- Issues -->
      <div v-if="ruleCheck.issues?.length" class="text-sm">
        <p class="text-slate-400 mb-2">问题：</p>
        <ul class="list-disc list-inside space-y-1 text-slate-300">
          <li v-for="(issue, i) in ruleCheck.issues" :key="i">{{ issue }}</li>
        </ul>
      </div>

      <!-- Content -->
      <div>
        <p class="text-sm text-slate-400 mb-2">生成内容：</p>
        <pre class="bg-slate-950 border border-slate-800 rounded-lg p-4 text-sm text-slate-200 whitespace-pre-wrap font-sans max-h-96 overflow-y-auto">{{ result.content || '(空 - 手动模式请到 CLI 粘贴)' }}</pre>
      </div>

      <!-- Save button -->
      <div v-if="result.content && (ruleCheck.pass && styleScore.passed)" class="flex gap-3">
        <button @click="handleSave" class="btn-primary">📁 保存到 Obsidian</button>
        <p class="text-sm text-slate-500 self-center">保存到 待发布/ 目录</p>
      </div>
    </div>
  </div>
</template>
