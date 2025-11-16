from .base import CCXTBase

class CoinbaseHandler(CCXTBase):
    def __init__(self, api_key, api_secret, config=None):
        super().__init__(api_key, api_secret, 'coinbase', config)