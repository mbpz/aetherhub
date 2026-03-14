import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { authApi } from '../api'

export default function AuthCallbackPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { login } = useAuthStore()

  useEffect(() => {
    const token = searchParams.get('token')
    const error = searchParams.get('error')

    if (error) {
      let msg = '授权失败，请重试'
      if (error === 'access_denied') msg = '授权已取消'
      if (error === 'invalid_state') msg = '授权失败：无效的请求，请重试'
      navigate(`/login?error=${encodeURIComponent(msg)}`, { replace: true })
      return
    }

    if (token) {
      // Fetch user info with token
      const fetchUser = async () => {
        try {
          // Temporarily set token in store to make authenticated request
          login(token, null)
          const res = await authApi.getMe()
          login(token, res.data.data)
          navigate('/skills', { replace: true })
        } catch (e) {
          navigate('/login?error=登录失败，请重试', { replace: true })
        }
      }
      fetchUser()
    } else {
      navigate('/login?error=未收到授权凭证', { replace: true })
    }
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
        <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-800">正在登录...</h2>
        <p className="text-gray-500 mt-2 text-sm">请稍候，正在验证您的身份</p>
      </div>
    </div>
  )
}
