from .handlers.binance import BinanceHandler
from .handlers.bybit import BybitHandler
from .handlers.okx import OKXHandler
from .handlers.mexc import MEXCHandler
from .handlers.coinbase import CoinbaseHandler
from users.models import ExchangeAccount


class ExchangeManager:
    HANDLERS = {
        'binance': BinanceHandler,
        'bybit': BybitHandler,
        'okx': OKXHandler,
        'mexc': MEXCHandler,
        'coinbase': CoinbaseHandler,
    }

    @classmethod
    def get_handler(cls, exchange_name):
        return cls.HANDLERS.get(exchange_name.lower())

    @classmethod
    def get_exchange_client(cls, exchange_account: ExchangeAccount, config=None):
        """Get CCXT client for an exchange account"""
        handler_class = cls.get_handler(exchange_account.exchange_name)
        if not handler_class:
            raise ValueError(f"Unsupported exchange: {exchange_account.exchange_name}")

        handler = handler_class(
            api_key=exchange_account.api_key_encrypted,
            api_secret=exchange_account.api_secret_encrypted,
            config=config or {}
        )

        return handler.create_client()