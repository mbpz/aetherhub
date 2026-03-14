import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoggedIn: false,

      login: (token, user) => {
        set({ token, user, isLoggedIn: true })
      },

      logout: () => {
        set({ token: null, user: null, isLoggedIn: false })
      },

      setUser: (user) => set({ user }),
    }),
    {
      name: 'aetherhub_token',
      partialize: (state) => ({ token: state.token, user: state.user, isLoggedIn: state.isLoggedIn }),
    }
  )
)
