import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { useAuthStore } from './stores/authStore'

// Layout components
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'

// Page components
import Login from './components/Auth/Login'
import Dashboard from './components/Dashboard'
import BotList from './components/Bots/BotList'
import ExchangeAccounts from './components/Exchanges/ExchangeAccounts'
import Investments from './components/Investments/Investments'
import Referrals from './components/Referrals/Referrals'
import LandingPage from './components/LandingPage'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
    mutations: {
      retry: 1,
    },
  },
})

function App() {
  const { isAuthenticated } = useAuthStore()

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/auth" element={<Login />} />

            {/* Protected routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Dashboard />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/bots"
              element={
                <ProtectedRoute>
                  <Layout>
                    <BotList />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/exchanges"
              element={
                <ProtectedRoute>
                  <Layout>
                    <ExchangeAccounts />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/investments"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Investments />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/referrals"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Referrals />
                  </Layout>
                </ProtectedRoute>
              }
            />

            {/* Catch all route - redirect to dashboard if authenticated, otherwise landing */}
            <Route
              path="*"
              element={
                <Navigate to={isAuthenticated ? "/dashboard" : "/"} replace />
              }
            />
          </Routes>

          {/* Global toast notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                iconTheme: {
                  primary: '#10b981',
                  secondary: '#fff',
                },
              },
              error: {
                duration: 5000,
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </div>
      </Router>
    </QueryClientProvider>
  )
}

export default App