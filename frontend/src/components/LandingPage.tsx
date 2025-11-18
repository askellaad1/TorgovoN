import React from 'react'
import { Link } from 'react-router-dom'
import {
  BoltIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  ArrowRightOnRectangleIcon,
  PlayIcon,
  StarIcon,
} from '@heroicons/react/24/outline'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="relative bg-gray-900">
        <div className="absolute inset-0">
          <div className="absolute inset-y-0 left-0 w-1/2 bg-blue-600"></div>
          <div className="absolute inset-y-0 right-0 w-1/2 bg-gray-900"></div>
        </div>
        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="relative py-24 sm:py-32">
            <div className="text-center">
              <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl lg:text-6xl">
                Advanced Crypto
                <span className="block text-blue-600">Trading Bots</span>
              </h1>
              <p className="mt-6 max-w-lg mx-auto text-xl text-gray-300 sm:max-w-3xl">
                Automate your cryptocurrency trading with our sophisticated AI-powered bots.
                Grid, Martingale, Custom, and Quantum AI strategies for all skill levels.
              </p>
              <div className="mt-10 flex justify-center space-x-4">
                <Link
                  to="/auth"
                  className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Get Started Free
                </Link>
                <Link
                  to="/auth"
                  className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  View Demo
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-12 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="lg:text-center">
            <h2 className="text-base font-semibold text-blue-600 tracking-wide uppercase">Features</h2>
            <p className="mt-2 text-3xl font-extrabold text-gray-900 sm:text-4xl">
              Everything you need for automated trading
            </p>
            <p className="mt-4 max-w-2xl mx-auto text-xl text-gray-500">
              From beginners to advanced traders, our platform has the tools and features to help you succeed.
            </p>
          </div>

          <div className="mt-16 grid grid-cols-1 gap-8 lg:grid-cols-3">
            <div className="text-center">
              <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white mb-4 mx-auto">
                <BoltIcon className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-medium text-gray-900">Custom Trading Bots</h3>
              <p className="mt-4 text-base text-gray-500">
                Create your own trading strategies with our webhook-driven custom bots.
                Perfect for implementing your unique trading algorithms.
              </p>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center h-12 w-12 rounded-md bg-green-500 text-white mb-4 mx-auto">
                <ChartBarIcon className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-medium text-gray-900">Grid Trading</h3>
              <p className="mt-4 text-base text-gray-500">
                Implement proven grid trading strategies with customizable levels and
                percentage differences for systematic profit generation.
              </p>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center h-12 w-12 rounded-md bg-purple-500 text-white mb-4 mx-auto">
                <ShieldCheckIcon className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-medium text-gray-900">Quantum AI</h3>
              <p className="mt-4 text-base text-gray-500">
                Invest in our advanced AI trading system with proven returns and
                fortnightly profit distributions.
              </p>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center h-12 w-12 rounded-md bg-yellow-500 text-white mb-4 mx-auto">
                <CurrencyDollarIcon className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-medium text-gray-900">Martingale Strategy</h3>
              <p className="mt-4 text-base text-gray-500">
                Progressive betting strategy with configurable multipliers and
                maximum loss limits for risk management.
              </p>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center h-12 w-12 rounded-md bg-red-500 text-white mb-4 mx-auto">
                <PlayIcon className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-medium text-gray-900">Multiple Exchanges</h3>
              <p className="mt-4 text-base text-gray-500">
                Connect to all major cryptocurrency exchanges including Binance,
                Bybit, OKX, MEXC, and Coinbase.
              </p>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center h-12 w-12 rounded-md bg-indigo-500 text-white mb-4 mx-auto">
                <StarIcon className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-medium text-gray-900">Referral Program</h3>
              <p className="mt-4 text-base text-gray-500">
                Earn generous bonuses by referring friends. Get rewards in
                alerts, discounts, or USDT.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <div className="mx-auto max-w-4xl text-center">
            <h2 className="text-3xl font-extrabold text-gray-900">
              Trusted by thousands of traders worldwide
            </h2>
            <p className="mt-4 text-gray-600">
              Join our growing community of successful cryptocurrency traders
            </p>
            <dl className="mt-12 grid grid-cols-2 gap-8 sm:grid-cols-4">
              <div className="flex flex-col">
                <dt className="order-2 text-2xl font-bold text-blue-600">50K+</dt>
                <dd className="order-1 mt-2 text-lg text-gray-500">Active Users</dd>
              </div>
              <div className="flex flex-col">
                <dt className="order-2 text-2xl font-bold text-green-600">$2.5M+</dt>
                <dd className="order-1 mt-2 text-lg text-gray-500">Trading Volume</dd>
              </div>
              <div className="flex flex-col">
                <dt className="order-2 text-2xl font-bold text-purple-600">1M+</dt>
                <dd className="order-1 mt-2 text-lg text-gray-500">Trades Executed</dd>
              </div>
              <div className="flex flex-col">
                <dt className="order-2 text-2xl font-bold text-yellow-600">99.9%</dt>
                <dd className="order-1 mt-2 text-lg text-gray-500">Uptime</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-blue-600">
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
              Ready to automate your trading?
            </h2>
            <p className="mt-4 text-xl text-blue-100">
              Get started with our free plan and upgrade as you grow.
            </p>
            <div className="mt-8 flex justify-center">
              <Link
                to="/auth"
                className="inline-flex items-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-blue-700 bg-white hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white"
              >
                Start Free Trial
                <ArrowRightOnRectangleIcon className="ml-2 h-5 w-5" />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white">
        <div className="mx-auto max-w-7xl py-12 px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4 lg:grid-cols-6">
            <div>
              <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">Product</h3>
              <ul className="mt-4 space-y-4">
                <li><Link to="/features" className="text-base text-gray-500 hover:text-gray-900">Features</Link></li>
                <li><Link to="/pricing" className="text-base text-gray-500 hover:text-gray-900">Pricing</Link></li>
                <li><Link to="/api" className="text-base text-gray-500 hover:text-gray-900">API</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">Support</h3>
              <ul className="mt-4 space-y-4">
                <li><Link to="/docs" className="text-base text-gray-500 hover:text-gray-900">Documentation</Link></li>
                <li><Link to="/guides" className="text-base text-gray-500 hover:text-gray-900">Guides</Link></li>
                <li><Link to="/contact" className="text-base text-gray-500 hover:text-gray-900">Contact</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">Company</h3>
              <ul className="mt-4 space-y-4">
                <li><Link to="/about" className="text-base text-gray-500 hover:text-gray-900">About</Link></li>
                <li><Link to="/blog" className="text-base text-gray-500 hover:text-gray-900">Blog</Link></li>
                <li><Link to="/careers" className="text-base text-gray-500 hover:text-gray-900">Careers</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">Legal</h3>
              <ul className="mt-4 space-y-4">
                <li><Link to="/privacy" className="text-base text-gray-500 hover:text-gray-900">Privacy</Link></li>
                <li><Link to="/terms" className="text-base text-gray-500 hover:text-gray-900">Terms</Link></li>
                <li><Link to="/risk" className="text-base text-gray-500 hover:text-gray-900">Risk Disclaimer</Link></li>
              </ul>
            </div>
            <div className="col-span-2 md:col-span-2">
              <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase">Subscribe to our newsletter</h3>
              <p className="mt-4 text-base text-gray-500">
                The latest news, articles, and resources, sent to your inbox weekly.
              </p>
              <form className="mt-4 sm:flex sm:max-w-md">
                <label htmlFor="email-address" className="sr-only">Email address</label>
                <input
                  id="email-address"
                  type="email"
                  autoComplete="email"
                  required
                  className="appearance-none min-w-0 w-full bg-white border border-gray-300 rounded-md py-2 px-4 text-base text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-white focus:border-blue-500 sm:max-w-xs"
                  placeholder="Enter your email"
                />
                <div className="mt-3 rounded-md sm:mt-0 sm:ml-3 sm:flex-shrink-0">
                  <button
                    type="submit"
                    className="flex w-full items-center justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:w-auto sm:px-6"
                  >
                    Subscribe
                  </button>
                </div>
              </form>
            </div>
          </div>
          <div className="mt-12 border-t border-gray-200 pt-8">
            <p className="text-base text-gray-400 xl:text-center">
              &copy; 2024 Torgovo Platform. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}