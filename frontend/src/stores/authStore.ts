import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '../utils/api'

export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  subscription_plan: string
  webhook_alerts_used: number
  quantum_balance: number
  referral_code: string
  secret_key: string
  webhook_url: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

export interface AuthActions {
  login: (email: string, password: string) => Promise<void>
  loginWithOtp: (phone: string, otp: string) => Promise<void>
  loginWithGoogle: (googleToken: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
  clearError: () => void
  setLoading: (loading: boolean) => void
}

export const useAuthStore = create<AuthState & AuthActions>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null })

        try {
          const response = await api.post('/api/v1/users/login/', {
            email,
            password,
          })

          const { access_token, refresh_token, user } = response.data

          // Set auth header
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 'Login failed'
          set({
            error: errorMessage,
            isLoading: false,
            isAuthenticated: false,
            user: null,
            token: null,
          })
          throw error
        }
      },

      loginWithOtp: async (phone: string, otp: string) => {
        set({ isLoading: true, error: null })

        try {
          const response = await api.post('/api/v1/users/login-otp/', {
            phone,
            otp,
          })

          const { access_token, refresh_token, user } = response.data

          // Set auth header
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 'OTP login failed'
          set({
            error: errorMessage,
            isLoading: false,
            isAuthenticated: false,
            user: null,
            token: null,
          })
          throw error
        }
      },

      loginWithGoogle: async (googleToken: string) => {
        set({ isLoading: true, error: null })

        try {
          const response = await api.post('/api/v1/users/google-login/', {
            access_token: googleToken,
          })

          const { access_token, refresh_token, user } = response.data

          // Set auth header
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 'Google login failed'
          set({
            error: errorMessage,
            isLoading: false,
            isAuthenticated: false,
            user: null,
            token: null,
          })
          throw error
        }
      },

      logout: () => {
        // Remove auth header
        delete api.defaults.headers.common['Authorization']

        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
          isLoading: false,
        })
      },

      refreshToken: async () => {
        const { token } = get()
        if (!token) return

        try {
          const response = await api.post('/api/v1/users/refresh/', {
            refresh_token: localStorage.getItem('refresh_token'),
          })

          const { access_token } = response.data

          // Update auth header
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

          set({ token: access_token })
        } catch (error) {
          // If refresh fails, logout user
          get().logout()
          throw error
        }
      },

      clearError: () => {
        set({ error: null })
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        // Set auth header when rehydrating
        if (state?.token) {
          api.defaults.headers.common['Authorization'] = `Bearer ${state.token}`
        }
        return state
      },
    }
  )
)