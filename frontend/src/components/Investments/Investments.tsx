import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowUpTrayIcon, PhotoIcon, DocumentTextIcon, CheckCircleIcon, ClockIcon } from '@heroicons/react/24/outline'
import { api, endpoints } from '../../utils/api'
import toast from 'react-hot-toast'

interface QuantumInvestment {
  id: string
  amount: number
  wallet_address: string
  blockchain: 'ethereum' | 'aptos'
  screenshot_url?: string
  tx_hash: string
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
  approved_at?: string
  current_balance: number
}

interface PoolStatistics {
  total_pool: number
  total_investors: number
  shown_profit_loss: number
  actual_profit_loss: number
  last_distribution_date?: string
  next_distribution_date: string
  user_share_percentage: number
}

export default function Investments() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<'investments' | 'statistics'>('investments')

  const [formData, setFormData] = useState({
    amount: '',
    wallet_address: '',
    blockchain: 'ethereum' as 'ethereum' | 'aptos',
    screenshot: null as File | null,
    tx_hash: '',
  })

  const queryClient = useQueryClient()

  const { data: investments, isLoading: investmentsLoading } = useQuery<QuantumInvestment[]>({
    queryKey: ['quantum-investments'],
    queryFn: async () => {
      const response = await api.get(endpoints.investments)
      return response.data
    },
    refetchInterval: 30000,
  })

  const { data: statistics } = useQuery<PoolStatistics>({
    queryKey: ['quantum-statistics'],
    queryFn: async () => {
      const response = await api.get(`${endpoints.investments}statistics/`)
      return response.data
    },
    refetchInterval: 60000, // Refresh every minute
  })

  const createInvestmentMutation = useMutation({
    mutationFn: async (data: FormData) => {
      const response = await api.post(endpoints.createInvestment, data, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    },
    onSuccess: () => {
      toast.success('Investment submitted for approval!')
      queryClient.invalidateQueries({ queryKey: ['quantum-investments'] })
      setIsCreateModalOpen(false)
      resetForm()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to submit investment')
    },
  })

  const handleFormChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        toast.error('Screenshot must be less than 5MB')
        return
      }

      // Validate file type
      if (!file.type.startsWith('image/')) {
        toast.error('Screenshot must be an image file')
        return
      }

      setFormData(prev => ({ ...prev, screenshot: file }))
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const submissionData = new FormData()
    submissionData.append('amount', formData.amount)
    submissionData.append('wallet_address', formData.wallet_address)
    submissionData.append('blockchain', formData.blockchain)
    submissionData.append('tx_hash', formData.tx_hash)

    if (formData.screenshot) {
      submissionData.append('screenshot', formData.screenshot)
    }

    createInvestmentMutation.mutate(submissionData)
  }

  const resetForm = () => {
    setFormData({
      amount: '',
      wallet_address: '',
      blockchain: 'ethereum',
      screenshot: null,
      tx_hash: '',
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800'
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      case 'rejected': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getBlockchainLabel = (blockchain: string) => {
    switch (blockchain) {
      case 'ethereum': return 'Ethereum (ERC20)'
      case 'aptos': return 'Aptos'
      default: return blockchain
    }
  }

  if (investmentsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Quantum AI Investments</h1>
        <p className="mt-2 text-gray-600">
          Invest in our advanced AI trading system with proven returns
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="mb-8 border-b border-gray-200">
        <nav className="flex -mb-px space-x-8">
          <button
            onClick={() => setActiveTab('investments')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'investments'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            My Investments
          </button>
          <button
            onClick={() => setActiveTab('statistics')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'statistics'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Pool Statistics
          </button>
        </nav>
      </div>

      {/* Statistics Tab */}
      {activeTab === 'statistics' && statistics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <div className="w-4 h-4 bg-blue-600 rounded-full"></div>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Pool</dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    ${statistics.total_pool.toFixed(2)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <div className="w-4 h-4 bg-green-600 rounded-full"></div>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Investors</dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {statistics.total_investors}
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                  <div className="w-4 h-4 bg-purple-600 rounded-full"></div>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Your Share</dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {statistics.user_share_percentage.toFixed(2)}%
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                  <div className="w-4 h-4 bg-yellow-600 rounded-full"></div>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Next Distribution</dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {new Date(statistics.next_distribution_date).toLocaleDateString()}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Investments Tab */}
      {activeTab === 'investments' && (
        <>
          {/* Create Investment Button */}
          <div className="mb-8">
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
            >
              <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
              New Investment
            </button>
          </div>

          {/* Investments Grid */}
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {investments?.map((investment) => (
              <div key={investment.id} className="bg-white rounded-lg shadow overflow-hidden">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900">
                      ${investment.amount.toFixed(2)}
                    </h3>
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(investment.status)}`}>
                      {investment.status}
                    </span>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Blockchain:</span>
                      <span className="font-medium">{getBlockchainLabel(investment.blockchain)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Current Balance:</span>
                      <span className="font-medium">${investment.current_balance.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Invested:</span>
                      <span className="font-medium">
                        {new Date(investment.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {investment.approved_at && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Approved:</span>
                        <span className="font-medium">
                          {new Date(investment.approved_at).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Investment Details */}
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="space-y-2 text-xs">
                      <div className="flex items-center">
                        <span className="text-gray-500 mr-2">Wallet:</span>
                        <span className="font-mono bg-gray-100 px-2 py-1 rounded truncate">
                          {investment.wallet_address}
                        </span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-gray-500 mr-2">TX Hash:</span>
                        <span className="font-mono bg-gray-100 px-2 py-1 rounded truncate">
                          {investment.tx_hash}
                        </span>
                      </div>
                      {investment.screenshot_url && (
                        <div className="mt-2">
                          <span className="text-gray-500">Proof Screenshot:</span>
                          <a
                            href={investment.screenshot_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="ml-2 text-blue-600 hover:text-blue-500"
                          >
                            <PhotoIcon className="inline h-4 w-4" />
                            View
                          </a>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {investments?.length === 0 && (
            <div className="text-center py-12">
              <div className="mx-auto h-12 w-12 text-gray-400">
                <ArrowUpTrayIcon />
              </div>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No investments yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                Start investing in Quantum AI to see your investments here.
              </p>
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="mt-6 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
              >
                Make Your First Investment
              </button>
            </div>
          )}
        </>
      )}

      {/* Create Investment Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-end justify-center px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            <div className="relative inline-block transform overflow-hidden rounded-lg bg-white text-left align-bottom transition-all sm:my-8 sm:w-full sm:max-w-lg sm:align-middle">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="w-full">
                    <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">
                      Make Quantum AI Investment
                    </h3>

                    <form onSubmit={handleSubmit} className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Amount (USDT)</label>
                        <input
                          type="number"
                          value={formData.amount}
                          onChange={(e) => handleFormChange('amount', e.target.value)}
                          required
                          min="100"
                          step="0.01"
                          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                          placeholder="1000.00"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700">Blockchain</label>
                        <select
                          value={formData.blockchain}
                          onChange={(e) => handleFormChange('blockchain', e.target.value)}
                          className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm rounded-md"
                        >
                          <option value="ethereum">Ethereum (ERC20)</option>
                          <option value="aptos">Aptos</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700">Wallet Address</label>
                        <input
                          type="text"
                          value={formData.wallet_address}
                          onChange={(e) => handleFormChange('wallet_address', e.target.value)}
                          required
                          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-purple-500 focus:border-purple-500 sm:text-sm font-mono"
                          placeholder="0x742d35Cc6634C0532925a3b844Bc9e3694a32bc9dd"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700">Transaction Hash</label>
                        <input
                          type="text"
                          value={formData.tx_hash}
                          onChange={(e) => handleFormChange('tx_hash', e.target.value)}
                          required
                          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-purple-500 focus:border-purple-500 sm:text-sm font-mono"
                          placeholder="0x..."
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700">Payment Screenshot</label>
                        <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-dashed border-gray-300 rounded-lg">
                          <div className="text-center">
                            <PhotoIcon className="mx-auto h-12 w-12 text-gray-400" />
                            <div className="mt-2 text-sm text-gray-600">
                              <label
                                htmlFor="screenshot-upload"
                                className="relative cursor-pointer rounded-md bg-white font-medium text-purple-600 hover:text-purple-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-purple-500"
                              >
                                <span>Upload screenshot</span>
                                <input
                                  id="screenshot-upload"
                                  name="screenshot-upload"
                                  type="file"
                                  className="sr-only"
                                  accept="image/*"
                                  onChange={handleFileChange}
                                />
                              </label>
                            </div>
                            <p className="text-xs text-gray-500">PNG, JPG, GIF up to 5MB</p>
                          </div>
                          {formData.screenshot && (
                            <div className="mt-4">
                              <div className="flex items-center">
                                <CheckCircleIcon className="h-5 w-5 text-green-400 mr-2" />
                                <span className="text-sm text-gray-900">{formData.screenshot.name}</span>
                                <button
                                  type="button"
                                  onClick={() => handleFormChange('screenshot', null)}
                                  className="ml-2 text-red-600 hover:text-red-500"
                                >
                                  Remove
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="mt-6 bg-gray-50 p-4 rounded-md">
                        <h4 className="text-sm font-medium text-gray-900 mb-2">Important Information</h4>
                        <ul className="text-sm text-gray-600 space-y-1">
                          <li>• Minimum investment: 100 USDT</li>
                          <li>• All investments require admin approval</li>
                          <li>• Profit/loss distributions are made fortnightly</li>
                          <li>• Only 20% of actual P&L is shown to users</li>
                        </ul>
                      </div>

                      <div className="flex justify-end space-x-3 mt-6">
                        <button
                          type="button"
                          onClick={() => setIsCreateModalOpen(false)}
                          className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={createInvestmentMutation.isLoading}
                          className="inline-flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {createInvestmentMutation.isLoading ? 'Submitting...' : 'Submit Investment'}
                        </button>
                      </div>
                    </form>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}