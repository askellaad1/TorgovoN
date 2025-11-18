import React, { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ShareIcon, UserPlusIcon, GiftIcon, CurrencyDollarIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline'
import { api, endpoints } from '../../utils/api'
import toast from 'react-hot-toast'

interface ReferralStats {
  referral_code: string
  total_referrals: number
  total_bonus_earned: number
  pending_bonuses: number
  referral_link: string
  recent_referrals: Array<{
    id: string
    referred_user: string
    email: string
    bonus_amount: number
    bonus_type: string
    status: string
    created_at: string
  }>
  bonus_config: {
    bonus_types: Array<{
      type: string
      amount: number
      description: string
    }>
    default_bonus_type: string
  }
}

export default function Referrals() {
  const [activeTab, setActiveTab] = useState<'overview' | 'history'>('overview')
  const [copiedCode, setCopiedCode] = useState(false)
  const [copiedLink, setCopiedLink] = useState(false)

  const queryClient = useQueryClient()

  const { data: stats, isLoading } = useQuery<ReferralStats>({
    queryKey: ['referral-stats'],
    queryFn: async () => {
      const response = await api.get(endpoints.referrals)
      return response.data
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const copyToClipboard = async (text: string, type: 'code' | 'link') => {
    try {
      await navigator.clipboard.writeText(text)

      if (type === 'code') {
        setCopiedCode(true)
        toast.success('Referral code copied!')
        setTimeout(() => setCopiedCode(false), 2000)
      } else {
        setCopiedLink(true)
        toast.success('Referral link copied!')
        setTimeout(() => setCopiedLink(false), 2000)
      }
    } catch (error) {
      toast.error('Failed to copy to clipboard')
    }
  }

  const shareReferral = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Join Torgovo - Advanced Crypto Trading Bots',
          text: `Join Torgovo using my referral code: ${stats?.referral_code}`,
          url: stats?.referral_link,
        })
      } catch (error) {
        console.error('Share failed:', error)
      }
    } else {
      // Fallback: copy referral link
      copyToClipboard(stats?.referral_link || '', 'link')
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  const data = stats!

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Referral Program</h1>
        <p className="mt-2 text-gray-600">
          Invite friends and earn rewards when they join Torgovo
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="mb-8 border-b border-gray-200">
        <nav className="flex -mb-px space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'history'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Referral History
          </button>
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Referral Code */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
            <div className="flex items-center mb-4">
              <ShareIcon className="h-6 w-6 text-blue-600 mr-2" />
              <h3 className="text-lg font-medium text-gray-900">Your Referral Code</h3>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-2xl font-mono font-bold text-gray-900">
                  {data.referral_code}
                </span>
                <button
                  onClick={() => copyToClipboard(data.referral_code, 'code')}
                  className={`ml-4 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    copiedCode
                      ? 'bg-green-100 text-green-700'
                      : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                  }`}
                >
                  {copiedCode ? 'Copied!' : 'Copy'}
                </button>
              </div>
            </div>
            <p className="mt-4 text-sm text-gray-600">
              Share this code with friends to earn referral bonuses when they sign up.
            </p>
          </div>

          {/* Stats Overview */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <UserPlusIcon className="h-6 w-6 text-green-600 mr-2" />
                <h3 className="text-lg font-medium text-gray-900">Total Referrals</h3>
              </div>
              <div className="mt-2 text-3xl font-bold text-gray-900">
                {data.total_referrals}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <CurrencyDollarIcon className="h-6 w-6 text-purple-600 mr-2" />
                <h3 className="text-lg font-medium text-gray-900">Total Bonuses Earned</h3>
              </div>
              <div className="mt-2 text-3xl font-bold text-gray-900">
                ${data.total_bonus_earned.toFixed(2)}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <GiftIcon className="h-6 w-6 text-yellow-600 mr-2" />
                <h3 className="text-lg font-medium text-gray-900">Pending Bonuses</h3>
              </div>
              <div className="mt-2 text-3xl font-bold text-gray-900">
                {data.pending_bonuses}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Referral Link */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Referral Link</h3>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-mono text-gray-700 truncate flex-1">
              {data.referral_link}
            </span>
            <div className="flex space-x-2 ml-4">
              <button
                onClick={() => copyToClipboard(data.referral_link, 'link')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  copiedLink
                    ? 'bg-green-100 text-green-700'
                    : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                }`}
              >
                {copiedLink ? 'Copied!' : 'Copy'}
              </button>
              <button
                onClick={shareReferral}
                className="px-4 py-2 rounded-md text-sm font-medium bg-purple-100 text-purple-700 hover:bg-purple-200 transition-colors"
              >
                Share
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Bonus Configuration */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Bonus Structure</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <span className="text-sm text-gray-500">Default Bonus Type:</span>
            <span className="ml-2 px-3 py-1 text-sm font-semibold rounded-full bg-blue-100 text-blue-800">
              {data.bonus_config.default_bonus_type}
            </span>
          </div>
        </div>
        <div className="mt-4 space-y-2">
          {data.bonus_config.bonus_types.map((bonus, index) => (
            <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-md">
              <span className="text-sm font-medium text-gray-900">{bonus.description}</span>
              <span className="text-sm font-bold text-green-600">
                ${bonus.amount.toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Referral History</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Referred User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Bonus Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.recent_referrals.map((referral) => (
                  <tr key={referral.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(referral.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {referral.referred_user}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {referral.email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        referral.bonus_type === 'alerts' ? 'bg-blue-100 text-blue-800' :
                        referral.bonus_type === 'discount' ? 'bg-green-100 text-green-800' :
                        referral.bonus_type === 'usdt' ? 'bg-purple-100 text-purple-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {referral.bonus_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      ${referral.bonus_amount.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        referral.status === 'paid' ? 'bg-green-100 text-green-800' :
                        referral.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                        referral.status === 'claimed' ? 'bg-blue-100 text-blue-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {referral.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data.recent_referrals.length === 0 && (
              <div className="text-center py-8">
                <ArrowDownTrayIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No referrals yet</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Start sharing your referral code to earn bonuses!
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}