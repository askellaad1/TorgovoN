import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { PlusIcon, PlayIcon, StopIcon, PencilIcon, TrashIcon, EyeIcon, FunnelIcon, MagnifyingGlassIcon, DocumentArrowDownIcon, CheckIcon } from '@heroicons/react/24/outline'
import { api, endpoints } from '../../utils/api'
import toast from 'react-hot-toast'

interface Bot {
  id: string
  name: string
  bot_type: 'custom' | 'grid' | 'martingale' | 'quantum'
  trading_pair: string
  is_active: boolean
  created_at: string
  last_activity: string
  config: any
  exchange_account: {
    exchange_name: string
    masked_api_key: string
  }
  performance?: {
    total_trades: number
    success_rate: number
    profit_loss: number
  }
}

interface CreateBotModalProps {
  isOpen: boolean
  onClose: () => void
}

function CreateBotModal({ isOpen, onClose }: CreateBotModalProps) {
  const [botType, setBotType] = useState<'custom' | 'grid' | 'martingale' | 'quantum'>('custom')
  const [botName, setBotName] = useState('')
  const [tradingPair, setTradingPair] = useState('BTC/USDT')
  const [exchangeId, setExchangeId] = useState('')

  const queryClient = useQueryClient()

  const { data: exchanges } = useQuery({
    queryKey: ['exchanges'],
    queryFn: async () => {
      const response = await api.get(endpoints.exchanges)
      return response.data
    },
  })

  const createBotMutation = useMutation({
    mutationFn: async (botData: any) => {
      const response = await api.post(endpoints.createBot, botData)
      return response.data
    },
    onSuccess: () => {
      toast.success('Bot created successfully!')
      queryClient.invalidateQueries({ queryKey: ['bots'] })
      onClose()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to create bot')
    },
  })

  const handleCreateBot = (e: React.FormEvent) => {
    e.preventDefault()

    const config = getDefaultConfig(botType)

    createBotMutation.mutate({
      name: botName,
      bot_type: botType,
      trading_pair: tradingPair,
      exchange_account: exchangeId,
      config,
    })
  }

  const getDefaultConfig = (type: string) => {
    switch (type) {
      case 'custom':
        return {
          webhook_url: '',
          secret_key: '',
          trade_size: 100,
        }
      case 'grid':
        return {
          grid_levels: 10,
          percentage_difference: 1.0,
          investment_amount: 1000,
        }
      case 'martingale':
        return {
          base_amount: 100,
          multiplier: 2.0,
          max_levels: 5,
        }
      case 'quantum':
        return {
          investment_amount: 1000,
          risk_level: 'medium',
        }
      default:
        return {}
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-end justify-center px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div className="relative inline-block transform overflow-hidden rounded-lg bg-white text-left align-bottom transition-all sm:my-8 sm:w-full sm:max-w-lg sm:align-middle">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="sm:flex sm:items-start">
              <div className="w-full">
                <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">
                  Create New Bot
                </h3>

                <form onSubmit={handleCreateBot} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Bot Type</label>
                    <select
                      value={botType}
                      onChange={(e) => setBotType(e.target.value as any)}
                      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                    >
                      <option value="custom">Custom Bot</option>
                      <option value="grid">Grid Bot</option>
                      <option value="martingale">Martingale Bot</option>
                      <option value="quantum">Quantum AI Bot</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Bot Name</label>
                    <input
                      type="text"
                      value={botName}
                      onChange={(e) => setBotName(e.target.value)}
                      required
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="My Trading Bot"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Trading Pair</label>
                    <input
                      type="text"
                      value={tradingPair}
                      onChange={(e) => setTradingPair(e.target.value)}
                      required
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="BTC/USDT"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Exchange Account</label>
                    <select
                      value={exchangeId}
                      onChange={(e) => setExchangeId(e.target.value)}
                      required
                      className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                    >
                      <option value="">Select an exchange</option>
                      {exchanges?.map((exchange: any) => (
                        <option key={exchange.id} value={exchange.id}>
                          {exchange.exchange_name} ({exchange.masked_api_key})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="flex justify-end space-x-3 mt-6">
                    <button
                      type="button"
                      onClick={onClose}
                      className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={createBotMutation.isLoading}
                      className="inline-flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                    >
                      {createBotMutation.isLoading ? 'Creating...' : 'Create Bot'}
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

export default function BotList() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [selectedBots, setSelectedBots] = useState<string[]>([])
  const [advancedFilter, setAdvancedFilter] = useState({ exchange: '', profitability: 'all', dateRange: '' })

  const { data: bots, isLoading, error } = useQuery<Bot[]>({
    queryKey: ['bots'],
    queryFn: async () => {
      const response = await api.get(endpoints.bots)
      return response.data
    },
    refetchInterval: 30000,
  })

  const toggleBotMutation = useMutation({
    mutationFn: async ({ botId, isActive }: { botId: string; isActive: boolean }) => {
      const endpoint = isActive ? `${endpoints.bots}${botId}/stop/` : `${endpoints.bots}${botId}/start/`
      const response = await api.post(endpoint)
      return response.data
    },
    onSuccess: (_, { botId, isActive }) => {
      const action = isActive ? 'stopped' : 'started'
      toast.success(`Bot ${action} successfully!`)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to toggle bot')
    },
  })

  const deleteBotMutation = useMutation({
    mutationFn: async (botId: string) => {
      await api.delete(`${endpoints.bots}${botId}/`)
      return botId
    },
    onSuccess: () => {
      toast.success('Bot deleted successfully!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to delete bot')
    },
  })

  const handleToggleBot = (botId: string, isActive: boolean) => {
    toggleBotMutation.mutate({ botId, isActive })
  }

  const handleDeleteBot = (botId: string) => {
    if (window.confirm('Are you sure you want to delete this bot?')) {
      deleteBotMutation.mutate(botId)
    }
  }

  const bulkActionMutation = useMutation({
    mutationFn: async ({ action, botIds }: { action: string; botIds: string[] }) => {
      const response = await api.post(`${endpoints.bots}bulk-action/`, { action, bot_ids: botIds })
      return response.data
    },
    onSuccess: (_, { action }) => {
      toast.success(`${action} action completed successfully!`)
      setSelectedBots([])
    },
    onError: () => toast.error('Bulk action failed'),
  })

  const exportBots = (format: 'csv' | 'json') => {
    const exportData = filteredBots.map(bot => ({
      name: bot.name,
      type: bot.bot_type,
      pair: bot.trading_pair,
      exchange: bot.exchange_account.exchange_name,
      status: bot.is_active ? 'Active' : 'Inactive',
      profit: bot.performance?.profit_loss || 0,
      success_rate: bot.performance?.success_rate || 0,
      trades: bot.performance?.total_trades || 0,
    }))

    if (format === 'csv') {
      const csv = [
        Object.keys(exportData[0] || {}).join(','),
        ...exportData.map(row => Object.values(row).join(','))
      ].join('\n')

      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'bots-export.csv'
      a.click()
    } else {
      const json = JSON.stringify(exportData, null, 2)
      const blob = new Blob([json], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'bots-export.json'
      a.click()
    }
    toast.success(`Bots exported as ${format.toUpperCase()}`)
  }

  const filteredBots = bots?.filter(bot => {
    // Basic filter
    if (filter === 'all') return true
    if (filter === 'active') return bot.is_active
    if (filter === 'inactive') return !bot.is_active
    if (filter !== 'all' && bot.bot_type !== filter) return false

    // Search filter
    if (search && !bot.name.toLowerCase().includes(search.toLowerCase()) &&
        !bot.trading_pair.toLowerCase().includes(search.toLowerCase())) {
      return false
    }

    // Advanced filters
    if (advancedFilter.exchange && bot.exchange_account.exchange_name !== advancedFilter.exchange) {
      return false
    }

    if (advancedFilter.profitability !== 'all' && bot.performance) {
      if (advancedFilter.profitability === 'profitable' && bot.performance.profit_loss <= 0) return false
      if (advancedFilter.profitability === 'loss' && bot.performance.profit_loss > 0) return false
    }

    return true
  }) || []

  const getBotTypeColor = (type: string) => {
    switch (type) {
      case 'custom': return 'bg-blue-100 text-blue-800'
      case 'grid': return 'bg-green-100 text-green-800'
      case 'martingale': return 'bg-yellow-100 text-yellow-800'
      case 'quantum': return 'bg-purple-100 text-purple-800'
      default: return 'bg-gray-100 text-gray-800'
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
          <h1 className="text-3xl font-bold text-gray-900">Trading Bots</h1>
          <p className="mt-2 text-gray-600">
            Manage your automated trading strategies
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Create Bot
          </button>
        </div>
      </div>

      {/* Search and Actions Bar */}
      <div className="mt-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex-1 max-w-lg">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Search bots..."
            />
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {selectedBots.length > 0 && (
            <div className="flex items-center space-x-2 mr-4">
              <span className="text-sm text-gray-700">{selectedBots.length} selected</span>
              <button
                onClick={() => bulkActionMutation.mutate({ action: 'start', botIds: selectedBots })}
                className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded"
              >
                Start All
              </button>
              <button
                onClick={() => bulkActionMutation.mutate({ action: 'stop', botIds: selectedBots })}
                className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded"
              >
                Stop All
              </button>
            </div>
          )}

          <button
            onClick={() => exportBots('csv')}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="mt-6 border-b border-gray-200">
        <nav className="flex -mb-px space-x-8">
          {['all', 'active', 'inactive', 'custom', 'grid', 'martingale', 'quantum'].map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                filter === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Bots Grid */}
      <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {filteredBots.map((bot) => (
          <div key={bot.id} className="bg-white rounded-lg shadow overflow-hidden">
            <div className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">{bot.name}</h3>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getBotTypeColor(bot.bot_type)}`}>
                    {bot.bot_type}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex w-2 h-2 rounded-full ${
                    bot.is_active ? 'bg-green-400' : 'bg-gray-300'
                  }`}></span>
                </div>
              </div>

              <div className="mt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Pair:</span>
                  <span className="font-medium">{bot.trading_pair}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Exchange:</span>
                  <span className="font-medium">{bot.exchange_account.exchange_name}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Last Activity:</span>
                  <span className="font-medium">
                    {bot.last_activity ? new Date(bot.last_activity).toLocaleDateString() : 'Never'}
                  </span>
                </div>
              </div>

              {bot.performance && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="text-center">
                      <div className="font-medium">{bot.performance.total_trades}</div>
                      <div className="text-gray-500">Trades</div>
                    </div>
                    <div className="text-center">
                      <div className="font-medium">{bot.performance.success_rate}%</div>
                      <div className="text-gray-500">Success</div>
                    </div>
                    <div className="text-center">
                      <div className={`font-medium ${
                        bot.performance.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        ${bot.performance.profit_loss.toFixed(2)}
                      </div>
                      <div className="text-gray-500">P&L</div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="bg-gray-50 px-4 py-3 sm:px-6">
              <div className="flex justify-between">
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleToggleBot(bot.id, bot.is_active)}
                    className={`inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                      bot.is_active
                        ? 'text-red-700 bg-red-100 hover:bg-red-200 focus:ring-red-500'
                        : 'text-green-700 bg-green-100 hover:bg-green-200 focus:ring-green-500'
                    }`}
                  >
                    {bot.is_active ? (
                      <>
                        <StopIcon className="h-3 w-3 mr-1" />
                        Stop
                      </>
                    ) : (
                      <>
                        <PlayIcon className="h-3 w-3 mr-1" />
                        Start
                      </>
                    )}
                  </button>
                  <button className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                    <EyeIcon className="h-3 w-3 mr-1" />
                    View
                  </button>
                  <button className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-gray-700 bg-gray-100 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500">
                    <PencilIcon className="h-3 w-3 mr-1" />
                    Edit
                  </button>
                </div>
                <button
                  onClick={() => handleDeleteBot(bot.id)}
                  className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-red-700 hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  <TrashIcon className="h-3 w-3" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredBots.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-500">
            {filter === 'all' ? 'No bots found' : `No ${filter} bots found`}
          </div>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            Create Your First Bot
          </button>
        </div>
      )}

      <CreateBotModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
    </div>
  )
}