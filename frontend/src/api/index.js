import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 180000,  // 3 min for LLM generation
})

export const articlesApi = {
  list: () => api.get('/articles').then(r => r.data),
  stats: () => api.get('/articles/stats').then(r => r.data),
}

export const generateApi = {
  generate: (data) => api.post('/generate', data).then(r => r.data),
  save: (data) => api.post('/generate/save', null, { params: data }).then(r => r.data),
}

export const styleApi = {
  learn: () => api.post('/style/learn').then(r => r.data),
  profile: () => api.get('/style/profile').then(r => r.data),
  score: (data) => api.post('/style/score', data).then(r => r.data),
}

export const settingsApi = {
  get: () => api.get('/settings').then(r => r.data),
}

export default api
