import axios, { AxiosError, AxiosResponse } from 'axios'
import toast from 'react-hot-toast'

// Create axios instance
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth-storage')
    if (token) {
      try {
        const authData = JSON.parse(token)
        if (authData.state?.token) {
          config.headers.Authorization = `Bearer ${authData.state.token}`
        }
      } catch (error) {
        console.error('Error parsing auth token:', error)
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error: AxiosError) => {
    const originalRequest = error.config as any

    // Handle 401 Unauthorized
    if (error.response?.status === 401) {
      // Don't retry login requests
      if (!originalRequest.url?.includes('/login') && !originalRequest._retry) {
        originalRequest._retry = true

        try {
          const authData = localStorage.getItem('auth-storage')
          if (authData) {
            const parsed = JSON.parse(authData)
            if (parsed.state?.token) {
              // Try to refresh token
              return api.post('/api/v1/users/refresh/', {
                refresh_token: localStorage.getItem('refresh_token')
              }).then((response) => {
                const { access_token } = response.data

                // Update stored token
                parsed.state.token = access_token
                localStorage.setItem('auth-storage', JSON.stringify(parsed))

                // Update original request
                originalRequest.headers.Authorization = `Bearer ${access_token}`
                return api(originalRequest)
              }).catch(() => {
                // Refresh failed, clear auth and redirect
                localStorage.removeItem('auth-storage')
                localStorage.removeItem('refresh_token')
                window.location.href = '/auth'
                return Promise.reject(error)
              })
            }
          }
        } catch (refreshError) {
          // Clear auth and redirect
          localStorage.removeItem('auth-storage')
          localStorage.removeItem('refresh_token')
          window.location.href = '/auth'
          return Promise.reject(error)
        }
      } else {
        // Login failed or already retried
        localStorage.removeItem('auth-storage')
        localStorage.removeItem('refresh_token')
        window.location.href = '/auth'
      }
    }

    // Handle different error types
    if (error.response) {
      const status = error.response.status
      const data = error.response.data as any

      switch (status) {
        case 400:
          toast.error(data.error || 'Bad request')
          break
        case 401:
          toast.error(data.error || 'Unauthorized')
          break
        case 403:
          toast.error(data.error || 'Forbidden')
          break
        case 404:
          toast.error(data.error || 'Not found')
          break
        case 429:
          toast.error(data.error || 'Rate limit exceeded')
          break
        case 500:
          toast.error(data.error || 'Server error')
          break
        default:
          toast.error(data.error || 'Request failed')
      }
    } else if (error.request) {
      toast.error('Network error. Please check your connection.')
    } else {
      toast.error('Request failed')
    }

    return Promise.reject(error)
  }
)

// API endpoints
export const endpoints = {
  // Auth
  login: '/api/v1/users/login/',
  register: '/api/v1/users/register/',
  refreshToken: '/api/v1/users/refresh/',
  googleLogin: '/api/v1/users/google-login/',
  loginOtp: '/api/v1/users/login-otp/',

  // Dashboard
  dashboard: '/api/v1/users/dashboard/',

  // Bots
  bots: '/api/v1/bots/',
  createBot: '/api/v1/bots/',
  bulkAction: '/api/v1/bots/bulk-action/',
  updateBot: (id: string) => `/api/v1/bots/${id}/`,
  deleteBot: (id: string) => `/api/v1/bots/${id}/`,

  // Exchanges
  exchanges: '/api/v1/exchanges/accounts/',
  createExchange: '/api/v1/exchanges/accounts/',
  updateExchange: (id: string) => `/api/v1/exchanges/accounts/${id}/`,
  deleteExchange: (id: string) => `/api/v1/exchanges/accounts/${id}/`,

  // Investments
  investments: '/api/v1/investments/quantum/',
  createInvestment: '/api/v1/investments/quantum/',

  // Referrals
  referrals: '/api/v1/referrals/stats/',

  // Payments
  subscriptionPlans: '/api/v1/payments/plans/',
  subscribe: '/api/v1/payments/subscribe/',
}

export default api