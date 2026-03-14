import api from './client'

export const authApi = {
  getLoginUrl: () => api.get('/auth/login'),
  getMe: () => api.get('/auth/me'),
  logout: () => api.post('/auth/logout'),
}

export const skillsApi = {
  list: (params) => api.get('/skills', { params }),
  categories: () => api.get('/skills/categories'),
  mine: (params) => api.get('/skills/mine', { params }),
  getById: (id) => api.get(`/skills/${id}`),
  create: (formData) => api.post('/skills', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  delete: (id) => api.delete(`/skills/${id}`),
  star: (id) => api.post(`/skills/${id}/star`),
  unstar: (id) => api.delete(`/skills/${id}/star`),
  getFileContent: (skillId, filename) =>
    api.get(`/skills/${skillId}/files/${encodeURIComponent(filename)}`, {
      responseType: 'text',
    }),
}
