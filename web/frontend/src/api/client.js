import axios from 'axios'
import { useAuthStore } from '../store/authStore'
import { toast } from '../components/Toast'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

// Request interceptor: attach JWT
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle errors and token refresh
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const status = err.response?.status
    const originalRequest = err.config

    // Handle 401 - try token refresh if not already attempted
    if (status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refreshToken = useAuthStore.getState().refreshToken
      if (refreshToken) {
        try {
          const res = await axios.post('/api/v1/auth/refresh', { refreshToken })
          const { token } = res.data
          useAuthStore.getState().setToken(token)
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        } catch (refreshErr) {
          useAuthStore.getState().logout()
          window.location.href = '/login'
          return Promise.reject(refreshErr)
        }
      }
      useAuthStore.getState().logout()
      window.location.href = '/login'
      return Promise.reject(err)
    }

    // Show toast for other errors
    if (status === 401) {
      // Already handled above or logged out
    } else if (status === 403) {
      toast('Access denied', 'error')
    } else if (status >= 500) {
      toast('Server error, please try again', 'error')
    } else if (status === 422) {
      const detail = err.response?.data?.detail
      toast(detail || 'Validation error', 'error')
    }

    // Handle network errors
    if (err.code === 'ECONNABORTED' || !err.response) {
      toast('Network error, please check your connection', 'error')
    }

    return Promise.reject(err)
  }
)

export default api
