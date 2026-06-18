<script setup>
import { ref, onMounted } from 'vue'
import { settingsApi } from '@/api'

const settings = ref(null)
const loading = ref(true)

onMounted(async () => {
  try {
    settings.value = await settingsApi.get()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-if="loading" class="text-slate-500">加载中...</div>

  <div v-else class="space-y-6 max-w-4xl">
    <!-- Obsidian -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-3">📂 Obsidian 路径</h3>
      <code class="block bg-slate-950 px-3 py-2 rounded text-slate-300 text-sm">
        {{ settings?.obsidian_vault }}
      </code>
    </div>

    <!-- LLM Providers -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-4">🤖 LLM Providers</h3>

      <div class="space-y-2">
        <div
          v-for="p in settings?.providers"
          :key="p.name"
          class="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg"
        >
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="font-medium text-white capitalize">{{ p.name }}</span>
              <span v-if="p.configured" class="badge badge-green">已配置</span>
              <span v-else class="badge badge-yellow">未配置</span>
            </div>
            <p class="text-xs text-slate-500 mt-1">
              {{ p.backend }} · {{ p.model }}
              <span v-if="p.api_base"> · {{ p.api_base }}</span>
            </p>
            <p v-if="p.note" class="text-xs text-slate-400 mt-1">{{ p.note }}</p>
          </div>
          <code class="text-xs text-slate-500 font-mono">{{ p.api_key_env }}</code>
        </div>
      </div>
    </div>

    <!-- How to configure -->
    <div class="card">
      <h3 class="text-lg font-semibold text-white mb-3">⚙️ 配置方法</h3>
      <p class="text-sm text-slate-400 mb-2">在终端运行（替换为你的真实 key）：</p>
      <pre class="bg-slate-950 px-3 py-2 rounded text-emerald-400 text-sm font-mono whitespace-pre-wrap"># 豆包
export OPENAI_API_BASE="https://ark.cn-beijing.volces.com/api/v3"
export OPENAI_API_KEY="你的豆包 API Key"
export OPENAI_MODEL="doubao-pro-32k"

# 通义千问
export OPENAI_API_BASE="https://dashscope.aliyuncs.com/compatible-mode/v1"
export OPENAI_API_KEY="你的阿里云 API Key"
export OPENAI_MODEL="qwen-max"

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."</pre>
    </div>
  </div>
</template>
