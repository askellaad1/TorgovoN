import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { PlusIcon, EyeIcon, PencilIcon, TrashIcon, KeyIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline'
import { api, endpoints } from '../../utils/api'
import toast from 'react-hot-toast'

interface ExchangeAccount {
  id: string
  exchange_name: string
  masked_api_key: string
  is_active: boolean
  created_at: string
  balance?: {
    free: Record<string, number>
    used: Record<string, number>
    total: Record<string, number>
  }
  status?: {
    is_connected: boolean
    last_checked: string
    error?: string
  }
}

interface CreateExchangeModalProps {
  isOpen: boolean
  onClose: () => void
}

function CreateExchangeModal({ isOpen, onClose }: CreateExchangeModalProps) {
  const [exchangeName, setExchangeName] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [apiSecret, setApiSecret] = useState('')
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [isTesting, setIsTesting] = useState(false)

  const queryClient = useQueryClient()

  const createExchangeMutation = useMutation({
    mutationFn: async (exchangeData: any) => {
      const response = await api.post(endpoints.createExchange, exchangeData)
      return response.data
    },
    onSuccess: () => {
      toast.success('Exchange account added successfully!')
      queryClient.invalidateQueries({ queryKey: ['exchanges'] })
      onClose()
      resetForm()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to add exchange account')
    },
  })

  const testConnection = async () => {
    if (!apiKey || !apiSecret) {
      toast.error('API key and secret are required')
      return
    }

    setIsTesting(true)
    setTestResult(null)

    try {
      // Test connection via API
      const response = await api.post('/api/v1/exchanges/test-connection/', {
        exchange_name: exchangeName,
        api_key: apiKey,
        api_secret: apiSecret,
      })

      setTestResult({
        success: true,
        message: 'Connection successful!',
      })
    } catch (error: any) {
      setTestResult({
        success: false,
        message: error.response?.data?.error || 'Connection failed',
      })
    } finally {
      setIsTesting(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!testResult?.success) {
      toast.error('Please test the connection first')
      return
    }

    createExchangeMutation.mutate({
      exchange_name: exchangeName,
      api_key: apiKey,
      api_secret: apiSecret,
    })
  }

  const resetForm = () => {
    setExchangeName('')
    setApiKey('')
    setApiSecret('')
    setTestResult(null)
  }

  const supportedExchanges = [
    { value: 'binance', label: 'Binance' },
    { value: 'bybit', label: 'Bybit' },
    { value: 'okx', label: 'OKX' },
    { value: 'mexc', label: 'MEXC' },
    { value: 'coinbase', label: 'Coinbase' },
  ]

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-end justify-center px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div className="relative inline-block transform overflow-hidden rounded-lg bg-white text-left align-bottom transition-all sm:my-8 sm:w-full sm:max-w-lg sm:align-middle">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="sm:flex sm:items-start">
              <div className="w-full">
                <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">
                  Add Exchange Account
                </h3>

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Exchange</label>
                    <select
                      value={exchangeName}
                      onChange={(e) => setExchangeName(e.target.value)}
                      required
                      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                    >
                      <option value="">Select an exchange</option>
                      {supportedExchanges.map((exchange) => (
                        <option key={exchange.value} value={exchange.value}>
                          {exchange.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">API Key</label>
                    <input
                      type="text"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      required
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="Enter your API key"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">API Secret</label>
                    <input
                      type="password"
                      value={apiSecret}
                      onChange={(e) => setApiSecret(e.target.value)}
                      required
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="Enter your API secret"
                    />
                  </div>

                  {/* Test Connection Result */}
                  {testResult && (
                    <div className={`p-3 rounded-md ${
                      testResult.success
                        ? 'bg-green-50 border border-green-200'
                        : 'bg-red-50 border border-red-200'
                    }`}>
                      <div className="flex items-center">
                        {testResult.success ? (
                          <CheckCircleIcon className="h-5 w-5 text-green-400 mr-2" />
                        ) : (
                          <XCircleIcon className="h-5 w-5 text-red-400 mr-2" />
                        )}
                        <span className={`text-sm ${
                          testResult.success ? 'text-green-800' : 'text-red-800'
                        }`}>
                          {testResult.message}
                        </span>
                      </div>
                    </div>
                  )}

                  <div className="flex justify-between space-x-3 mt-6">
                    <button
                      type="button"
                      onClick={onClose}
                      className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={testConnection}
                      disabled={isTesting || !apiKey || !apiSecret || !exchangeName}
                      className="bg-yellow-600 text-white py-2 px-4 rounded-md hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isTesting ? 'Testing...' : 'Test Connection'}
                    </button>
                    <button
                      type="submit"
                      disabled={createExchangeMutation.isLoading || !testResult?.success}
                      className="inline-flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {createExchangeMutation.isLoading ? 'Adding...' : 'Add Exchange'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function ExchangeAccounts() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)

  const { data: exchanges, isLoading, error } = useQuery<ExchangeAccount[]>({
    queryKey: ['exchanges'],
    queryFn: async () => {
      const response = await api.get(endpoints.exchanges)
      return response.data
    },
    refetchInterval: 60000, // Refresh every minute
  })

  const deleteExchangeMutation = useMutation({
    mutationFn: async (exchangeId: string) => {
      await api.delete(`${endpoints.deleteExchange(exchangeId)}`)
      return exchangeId
    },
    onSuccess: () => {
      toast.success('Exchange account removed successfully!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to remove exchange account')
    },
  })

  const handleDeleteExchange = (exchangeId: string) => {
    if (window.confirm('Are you sure you want to remove this exchange account?')) {
      deleteExchangeMutation.mutate(exchangeId)
    }
  }

  const handleTestConnection = async (exchangeId: string) => {
    try {
      await api.post(`${endpoints.exchanges}${exchangeId}/test-connection/`)
      toast.success('Connection test successful!')
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Connection test failed')
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Exchange Accounts</h1>
          <p className="mt-2 text-gray-600">
            Manage your cryptocurrency exchange connections
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Add Exchange
          </button>
        </div>
      </div>

      {/* Exchange Accounts Grid */}
      <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {exchanges?.map((exchange) => (
          <div key={exchange.id} className="bg-white rounded-lg shadow overflow-hidden">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <KeyIcon className="h-4 w-4 text-blue-600" />
                  </div>
                  <h3 className="ml-3 text-lg font-medium text-gray-900">
                    {exchange.exchange_name}
                  </h3>
                </div>
                <div className={`inline-flex w-2 h-2 rounded-full ${
                  exchange.status?.is_connected
                    ? 'bg-green-400'
                    : 'bg-red-400'
                }`}></div>
              </div>

              <div className="space-y-3">
                <div>
                  <span className="text-sm text-gray-500">API Key:</span>
                  <p className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                    {exchange.masked_api_key}
                  </p>
                </div>

                <div>
                  <span className="text-sm text-gray-500">Status:</span>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    exchange.is_active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {exchange.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>

                <div>
                  <span className="text-sm text-gray-500">Added:</span>
                  <span className="text-sm font-medium">
                    {new Date(exchange.created_at).toLocaleDateString()}
                  </span>
                </div>

                {exchange.status?.last_checked && (
                  <div>
                    <span className="text-sm text-gray-500">Last Checked:</span>
                    <span className="text-sm font-medium">
                      {new Date(exchange.status.last_checked).toLocaleString()}
                    </span>
                  </div>
                )}

                {exchange.balance && (
                  <div>
                    <span className="text-sm text-gray-500">USDT Balance:</span>
                    <span className="text-sm font-medium">
                      ${exchange.balance.total?.USDT?.toFixed(2) || '0.00'}
                    </span>
                  </div>
                )}
              </div>

              {exchange.status?.error && (
                <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-sm text-red-600">{exchange.status.error}</p>
                </div>
              )}
            </div>

            <div className="bg-gray-50 px-4 py-3 sm:px-6">
              <div className="flex justify-between space-x-2">
                <button
                  onClick={() => handleTestConnection(exchange.id)}
                  className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <KeyIcon className="h-3 w-3 mr-1" />
                  Test
                </button>
                <button className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-gray-700 bg-gray-100 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500">
                  <EyeIcon className="h-3 w-3 mr-1" />
                  Balance
                </button>
                <button className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-gray-700 bg-gray-100 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500">
                  <PencilIcon className="h-3 w-3 mr-1" />
                  Edit
                </button>
                <button
                  onClick={() => handleDeleteExchange(exchange.id)}
                  className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-red-700 hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  <TrashIcon className="h-3 w-3" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {exchanges?.length === 0 && (
        <div className="text-center py-12">
          <KeyIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No exchange accounts</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by adding your first exchange account.
          </p>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="mt-6 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Add Exchange Account
          </button>
        </div>
      )}

      <CreateExchangeModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
    </div>
  )
}