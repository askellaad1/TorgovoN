import ccxt
import logging
from django.conf import settings
from core.utils import decrypt_data

logger = logging.getLogger('TorgovoN.CCXTBase')


class CCXTBase:
    def __init__(self, api_key_encrypted, api_secret_encrypted, exchange_name, config=None):
        self.api_key_encrypted = api_key_encrypted
        self.api_secret_encrypted = api_secret_encrypted
        self.exchange_name = exchange_name
        self.config = config or {}

    def create_client(self):
        """Create and return CCXT exchange instance with proper decryption"""
        try:
            exchange_class = getattr(ccxt, self.exchange_name)
        except AttributeError:
            raise ValueError(f"Exchange '{self.exchange_name}' not supported by CCXT")

        # Decrypt API keys using the new encryption method
        try:
            # Try to get ExchangeAccount instance to use its decrypt method
            from exchanges.models import ExchangeAccount
            temp_account = ExchangeAccount()
            api_key = temp_account.decrypt_api_key(self.api_key_encrypted)
            api_secret = temp_account.decrypt_api_key(self.api_secret_encrypted)
        except Exception:
            # Fallback to legacy decryption
            try:
                api_key = decrypt_data(self.api_key_encrypted)
                api_secret = decrypt_data(self.api_secret_encrypted)
            except Exception:
                # If decryption fails, assume they're already decrypted
                api_key = self.api_key_encrypted
                api_secret = self.api_secret_encrypted

        client_config = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': self.config.get('options', {}),
        }

        # Add sandbox/demo mode if specified
        if self.config.get('sandbox', False):
            client_config['sandbox'] = True

        client = exchange_class(client_config)

        # Configure for futures if needed
        if self.config.get('futures', False):
            if self.exchange_name.lower() == 'binance':
                client.options['defaultType'] = 'future'
            elif self.exchange_name.lower() == 'bybit':
                client.options['defaultType'] = 'swap'
            elif self.exchange_name.lower() == 'okx':
                client.options['defaultType'] = 'swap'

        logger.info(f"Created {self.exchange_name} client with rate limiting enabled")
        return client

    def execute_market_order(self, symbol, side, amount, params=None):
        """Execute a market order using CCXT"""
        client = self.create_client()
        params = params or {}

        try:
            logger.info(f"Executing market order: {side} {amount} {symbol}")

            # Handle cost-based orders vs amount-based orders
            if 'cost' in params:
                result = client.create_market_order_with_cost(symbol, side, params['cost'], params)
            else:
                result = client.create_market_order(symbol, side, amount, None, params)

            logger.info(f"Market order executed successfully: {result['id']}")
            return {
                'success': True,
                'order_id': result['id'],
                'status': result.get('status', 'open'),
                'filled': result.get('filled', 0),
                'remaining': result.get('remaining', amount),
                'price': result.get('price', 0),
                'cost': result.get('cost', 0),
                'raw': result
            }

        except ccxt.InsufficientFunds as e:
            logger.error(f"Insufficient funds for market order: {e}")
            return {'success': False, 'error': 'Insufficient funds', 'code': 'INSUFFICIENT_FUNDS'}
        except ccxt.InvalidOrder as e:
            logger.error(f"Invalid order parameters: {e}")
            return {'success': False, 'error': 'Invalid order parameters', 'code': 'INVALID_ORDER'}
        except ccxt.NetworkError as e:
            logger.error(f"Network error during market order: {e}")
            return {'success': False, 'error': 'Network error', 'code': 'NETWORK_ERROR'}
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error during market order: {e}")
            return {'success': False, 'error': str(e), 'code': 'EXCHANGE_ERROR'}
        except Exception as e:
            logger.error(f"Unexpected error during market order: {e}")
            return {'success': False, 'error': 'Unexpected error', 'code': 'UNKNOWN_ERROR'}

    def execute_limit_order(self, symbol, side, amount, price, params=None):
        """Execute a limit order using CCXT"""
        client = self.create_client()
        params = params or {}

        try:
            logger.info(f"Executing limit order: {side} {amount} {symbol} @ {price}")

            result = client.create_limit_order(symbol, side, amount, price, params)

            logger.info(f"Limit order placed successfully: {result['id']}")
            return {
                'success': True,
                'order_id': result['id'],
                'status': result.get('status', 'open'),
                'filled': result.get('filled', 0),
                'remaining': result.get('remaining', amount),
                'price': result.get('price', price),
                'cost': result.get('cost', 0),
                'raw': result
            }

        except ccxt.InsufficientFunds as e:
            logger.error(f"Insufficient funds for limit order: {e}")
            return {'success': False, 'error': 'Insufficient funds', 'code': 'INSUFFICIENT_FUNDS'}
        except ccxt.InvalidOrder as e:
            logger.error(f"Invalid order parameters: {e}")
            return {'success': False, 'error': 'Invalid order parameters', 'code': 'INVALID_ORDER'}
        except ccxt.NetworkError as e:
            logger.error(f"Network error during limit order: {e}")
            return {'success': False, 'error': 'Network error', 'code': 'NETWORK_ERROR'}
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error during limit order: {e}")
            return {'success': False, 'error': str(e), 'code': 'EXCHANGE_ERROR'}
        except Exception as e:
            logger.error(f"Unexpected error during limit order: {e}")
            return {'success': False, 'error': 'Unexpected error', 'code': 'UNKNOWN_ERROR'}

    def get_balance(self):
        """Fetch account balance using CCXT"""
        client = self.create_client()

        try:
            logger.info(f"Fetching balance for {self.exchange_name}")

            balance = client.fetch_balance()

            # Return standardized format
            return {
                'success': True,
                'free': balance.get('free', {}),
                'used': balance.get('used', {}),
                'total': balance.get('total', {}),
                'raw': balance
            }

        except ccxt.NetworkError as e:
            logger.error(f"Network error fetching balance: {e}")
            return {'success': False, 'error': 'Network error', 'code': 'NETWORK_ERROR'}
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error fetching balance: {e}")
            return {'success': False, 'error': str(e), 'code': 'EXCHANGE_ERROR'}
        except Exception as e:
            logger.error(f"Unexpected error fetching balance: {e}")
            return {'success': False, 'error': 'Unexpected error', 'code': 'UNKNOWN_ERROR'}

    def get_order_status(self, order_id, symbol):
        """Get order status using CCXT"""
        client = self.create_client()

        try:
            logger.info(f"Fetching order status for {order_id} on {symbol}")

            order = client.fetch_order(order_id, symbol)

            return {
                'success': True,
                'order_id': order['id'],
                'status': order['status'],
                'side': order['side'],
                'amount': order['amount'],
                'filled': order['filled'],
                'remaining': order['remaining'],
                'price': order['price'],
                'cost': order.get('cost', 0),
                'timestamp': order['timestamp'],
                'raw': order
            }

        except ccxt.OrderNotFound as e:
            logger.error(f"Order not found: {e}")
            return {'success': False, 'error': 'Order not found', 'code': 'ORDER_NOT_FOUND'}
        except ccxt.NetworkError as e:
            logger.error(f"Network error fetching order status: {e}")
            return {'success': False, 'error': 'Network error', 'code': 'NETWORK_ERROR'}
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error fetching order status: {e}")
            return {'success': False, 'error': str(e), 'code': 'EXCHANGE_ERROR'}
        except Exception as e:
            logger.error(f"Unexpected error fetching order status: {e}")
            return {'success': False, 'error': 'Unexpected error', 'code': 'UNKNOWN_ERROR'}

    def cancel_order(self, order_id, symbol):
        """Cancel order using CCXT"""
        client = self.create_client()

        try:
            logger.info(f"Cancelling order {order_id} on {symbol}")

            result = client.cancel_order(order_id, symbol)

            return {
                'success': True,
                'order_id': result['id'],
                'status': result.get('status', 'canceled'),
                'raw': result
            }

        except ccxt.OrderNotFound as e:
            logger.error(f"Order not found for cancellation: {e}")
            return {'success': False, 'error': 'Order not found', 'code': 'ORDER_NOT_FOUND'}
        except ccxt.NetworkError as e:
            logger.error(f"Network error cancelling order: {e}")
            return {'success': False, 'error': 'Network error', 'code': 'NETWORK_ERROR'}
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error cancelling order: {e}")
            return {'success': False, 'error': str(e), 'code': 'EXCHANGE_ERROR'}
        except Exception as e:
            logger.error(f"Unexpected error cancelling order: {e}")
            return {'success': False, 'error': 'Unexpected error', 'code': 'UNKNOWN_ERROR'}

    def get_ticker(self, symbol):
        """Get ticker information using CCXT"""
        client = self.create_client()

        try:
            logger.info(f"Fetching ticker for {symbol}")

            ticker = client.fetch_ticker(symbol)

            return {
                'success': True,
                'symbol': ticker['symbol'],
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'high': ticker['high'],
                'low': ticker['low'],
                'volume': ticker['baseVolume'],
                'timestamp': ticker['timestamp'],
                'raw': ticker
            }

        except ccxt.NetworkError as e:
            logger.error(f"Network error fetching ticker: {e}")
            return {'success': False, 'error': 'Network error', 'code': 'NETWORK_ERROR'}
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error fetching ticker: {e}")
            return {'success': False, 'error': str(e), 'code': 'EXCHANGE_ERROR'}
        except Exception as e:
            logger.error(f"Unexpected error fetching ticker: {e}")
            return {'success': False, 'error': 'Unexpected error', 'code': 'UNKNOWN_ERROR'}

    # Legacy method for backward compatibility
    def place_order(self, client, symbol, side, amount, order_type='market', params=None):
        """Legacy method - use execute_market_order or execute_limit_order instead"""
        if order_type == 'market':
            return self.execute_market_order(symbol, side, amount, params)
        elif order_type == 'limit':
            price = params.get('price') if params else None
            if price is None:
                raise ValueError("Price is required for limit orders")
            return self.execute_limit_order(symbol, side, amount, price, params)
        else:
            raise ValueError(f"Unsupported order type: {order_type}")