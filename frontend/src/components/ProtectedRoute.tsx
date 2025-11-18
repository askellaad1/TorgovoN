import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated } = useAuthStore()
  const location = useLocation()

  if (!isAuthenticated) {
    // Redirect to auth page with return URL
    return (
      <Navigate
        to={`/auth?redirect=${encodeURIComponent(location.pathname)}`}
        replace
        state={{ from: location }}
      />
    )
  }

  return <>{children}</>
}