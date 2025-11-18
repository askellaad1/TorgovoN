import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import toast from 'react-hot-toast'

type LoginFormData = {
  email: string
  password: string
  remember: boolean
}

type TabType = 'email' | 'phone' | 'google'

export default function Login() {
  const navigate = useNavigate()
  const { login, loginWithOtp, loginWithGoogle, isLoading, error, clearError } = useAuthStore()
  const [activeTab, setActiveTab] = useState<TabType>('email')
  const [showOtpInput, setShowOtpInput] = useState(false)
  const [phoneNumber, setPhoneNumber] = useState('')

  const {
    register: registerEmail,
    handleSubmit: handleEmailSubmit,
    formState: { errors: emailErrors },
  } = useForm<LoginFormData>()

  const {
    register: registerPhone,
    handleSubmit: handlePhoneSubmit,
    setValue: setPhoneValue,
    formState: { errors: phoneErrors },
  } = useForm<{ phone: string; otp: string }>()

  const onEmailLogin = async (data: LoginFormData) => {
    try {
      clearError()
      await login(data.email, data.password)
      toast.success('Login successful!')
      navigate('/dashboard')
    } catch (error: any) {
      console.error('Login error:', error)
    }
  }

  const onPhoneLogin = async (data: { phone: string; otp: string }) => {
    try {
      clearError()

      if (!showOtpInput) {
        // Send OTP request
        await useAuthStore.getState().sendOtp(data.phone)
        setPhoneNumber(data.phone)
        setShowOtpInput(true)
        toast.success('OTP sent to your phone')
      } else {
        // Verify OTP
        await loginWithOtp(phoneNumber, data.otp)
        toast.success('Login successful!')
        navigate('/dashboard')
      }
    } catch (error: any) {
      console.error('Phone login error:', error)
    }
  }

  const onGoogleLogin = async () => {
    try {
      clearError()
      // This would integrate with Google OAuth
      const googleToken = 'google_oauth_token' // Replace with actual Google OAuth
      await loginWithGoogle(googleToken)
      toast.success('Login successful!')
      navigate('/dashboard')
    } catch (error: any) {
      console.error('Google login error:', error)
    }
  }

  const handleResendOtp = async () => {
    try {
      await useAuthStore.getState().sendOtp(phoneNumber)
      toast.success('OTP resent to your phone')
    } catch (error: any) {
      console.error('Resend OTP error:', error)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to Torgovo
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Access your cryptocurrency trading dashboard
          </p>
        </div>

        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {/* Tab Navigation */}
          <div className="flex space-x-1 mb-6">
            <button
              onClick={() => setActiveTab('email')}
              className={`flex-1 py-2 px-4 text-center rounded-lg font-medium transition-colors ${
                activeTab === 'email'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Email
            </button>
            <button
              onClick={() => setActiveTab('phone')}
              className={`flex-1 py-2 px-4 text-center rounded-lg font-medium transition-colors ${
                activeTab === 'phone'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Phone
            </button>
            <button
              onClick={() => setActiveTab('google')}
              className={`flex-1 py-2 px-4 text-center rounded-lg font-medium transition-colors ${
                activeTab === 'google'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Google
            </button>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Email Login Form */}
          {activeTab === 'email' && (
            <form onSubmit={handleEmailSubmit(onEmailLogin)} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Email address
                </label>
                <div className="mt-1">
                  <input
                    {...registerEmail('email', {
                      required: 'Email is required',
                      pattern: {
                        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                        message: 'Invalid email address',
                      },
                    })}
                    type="email"
                    autoComplete="email"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Enter your email"
                  />
                  {emailErrors.email && (
                    <p className="mt-1 text-sm text-red-600">{emailErrors.email.message}</p>
                  )}
                </div>
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Password
                </label>
                <div className="mt-1">
                  <input
                    {...registerEmail('password', {
                      required: 'Password is required',
                      minLength: {
                        value: 8,
                        message: 'Password must be at least 8 characters',
                      },
                    })}
                    type="password"
                    autoComplete="current-password"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Enter your password"
                  />
                  {emailErrors.password && (
                    <p className="mt-1 text-sm text-red-600">{emailErrors.password.message}</p>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <input
                    {...registerEmail('remember')}
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="remember" className="ml-2 block text-sm text-gray-900">
                    Remember me
                  </label>
                </div>

                <div className="text-sm">
                  <Link to="/auth/forgot-password" className="font-medium text-blue-600 hover:text-blue-500">
                    Forgot password?
                  </Link>
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Signing in...' : 'Sign in'}
                </button>
              </div>
            </form>
          )}

          {/* Phone Login Form */}
          {activeTab === 'phone' && (
            <form onSubmit={handlePhoneSubmit(onPhoneLogin)} className="space-y-6">
              <div>
                <label htmlFor="phone" className="block text-sm font-medium text-gray-700">
                  Phone number
                </label>
                <div className="mt-1">
                  <input
                    {...registerPhone('phone', {
                      required: 'Phone number is required',
                      pattern: {
                        value: /^\+?[1-9]\d{1,14}$/,
                        message: 'Invalid phone number',
                      },
                    })}
                    type="tel"
                    autoComplete="tel"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="+1234567890"
                    disabled={showOtpInput}
                  />
                  {phoneErrors.phone && (
                    <p className="mt-1 text-sm text-red-600">{phoneErrors.phone.message}</p>
                  )}
                </div>
              </div>

              {showOtpInput && (
                <div>
                  <label htmlFor="otp" className="block text-sm font-medium text-gray-700">
                    One-Time Password
                  </label>
                  <div className="mt-1">
                    <input
                      {...registerPhone('otp', {
                        required: 'OTP is required',
                        pattern: {
                          value: /^\d{6}$/,
                          message: 'OTP must be 6 digits',
                        },
                      })}
                      type="text"
                      autoComplete="one-time-code"
                      maxLength={6}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="123456"
                    />
                    {phoneErrors.otp && (
                      <p className="mt-1 text-sm text-red-600">{phoneErrors.otp.message}</p>
                    )}
                  </div>
                </div>
              )}

              <div className="flex justify-between items-center">
                {showOtpInput && (
                  <button
                    type="button"
                    onClick={() => setShowOtpInput(false)}
                    className="text-sm text-gray-600 hover:text-gray-500"
                  >
                    Change phone number
                  </button>
                )}

                {showOtpInput && (
                  <button
                    type="button"
                    onClick={handleResendOtp}
                    className="text-sm font-medium text-blue-600 hover:text-blue-500"
                  >
                    Resend OTP
                  </button>
                )}
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading
                    ? (showOtpInput ? 'Verifying...' : 'Sending OTP...')
                    : (showOtpInput ? 'Verify OTP' : 'Send OTP')
                  }
                </button>
              </div>
            </form>
          )}

          {/* Google Login */}
          {activeTab === 'google' && (
            <div className="space-y-6">
              <div className="text-center py-8">
                <button
                  onClick={onGoogleLogin}
                  disabled={isLoading}
                  className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm text-base font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                    <path
                      fill="#4285F4"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                  {isLoading ? 'Signing in with Google...' : 'Sign in with Google'}
                </button>
              </div>
            </div>
          )}

          {/* Registration Link */}
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">New to Torgovo?</span>
              </div>
            </div>

            <div className="mt-6 text-center">
              <Link
                to="/auth/register"
                className="font-medium text-blue-600 hover:text-blue-500"
              >
                Create your free account
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}