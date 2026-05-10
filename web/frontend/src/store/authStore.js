import axios from 'axios'
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      isLoggedIn: false,

      login: (token, user, refreshToken = null) => {
        set({ token, user, refreshToken, isLoggedIn: true })
      },

      logout: () => {
        set({ token: null, refreshToken: null, user: null, isLoggedIn: false })
      },

      setToken: (token) => set({ token }),

      refreshToken: async () => {
        const refreshToken = get().refreshToken
        if (!refreshToken) return null
        try {
          const res = await axios.post('/api/v1/auth/refresh', { refreshToken })
          const { token } = res.data
          set({ token })
          return token
        } catch {
          get().logout()
          return null
        }
      },

      setUser: (user) => set({ user }),
    }),
    {
      name: 'aetherhub_token',
      partialize: (state) => ({ token: state.token, user: state.user, isLoggedIn: state.isLoggedIn, refreshToken: state.refreshToken }),
    }
  )
)
