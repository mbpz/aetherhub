import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Search, Upload, LogOut, User, ChevronDown, Package } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { authApi } from '../api'

export default function Header() {
  const { user, isLoggedIn, logout } = useAuthStore()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [searchQ, setSearchQ] = useState(searchParams.get('q') || '')
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef(null)

  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSearch = (e) => {
    e.preventDefault()
    const params = new URLSearchParams()
    if (searchQ.trim()) params.set('q', searchQ.trim())
    navigate(`/skills?${params.toString()}`)
  }

  const handleLogin = async () => {
    try {
      const res = await authApi.getLoginUrl()
      window.location.href = res.data.data.auth_url
    } catch (err) {
      console.error('Failed to get login URL', err)
    }
  }

  const handleLogout = async () => {
    try {
      await authApi.logout()
    } catch {}
    logout()
    setDropdownOpen(false)
    navigate('/')
  }

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 font-bold text-xl text-blue-600 shrink-0">
            <Package size={24} />
            <span>AetherHub</span>
          </Link>

          {/* Search */}
          <form onSubmit={handleSearch} className="flex-1 max-w-xl">
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                value={searchQ}
                onChange={(e) => setSearchQ(e.target.value)}
                placeholder="搜索技能名称或描述..."
                className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </form>

          {/* Right actions */}
          <div className="flex items-center gap-3 shrink-0">
            {isLoggedIn ? (
              <>
                <Link to="/skills/upload" className="btn-primary text-sm">
                  <Upload size={16} />
                  上传技能
                </Link>
                <div className="relative" ref={dropdownRef}>
                  <button
                    onClick={() => setDropdownOpen(!dropdownOpen)}
                    className="flex items-center gap-1.5 hover:opacity-80 transition-opacity"
                  >
                    <img
                      src={user?.avatar_url || 'https://avatars.githubusercontent.com/u/583231'}
                      alt={user?.login}
                      className="w-8 h-8 rounded-full border border-gray-200"
                    />
                    <ChevronDown size={14} className="text-gray-500" />
                  </button>
                  {dropdownOpen && (
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                      <div className="px-4 py-2 border-b border-gray-100">
                        <p className="font-medium text-sm text-gray-900 truncate">{user?.name || user?.login}</p>
                        <p className="text-xs text-gray-500 truncate">@{user?.login}</p>
                      </div>
                      <Link
                        to="/mine"
                        className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                        onClick={() => setDropdownOpen(false)}
                      >
                        <User size={14} />
                        我的技能
                      </Link>
                      <hr className="my-1 border-gray-100" />
                      <button
                        onClick={handleLogout}
                        className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                      >
                        <LogOut size={14} />
                        退出登录
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <button onClick={handleLogin} className="btn-primary text-sm">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                </svg>
                GitHub 登录
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
