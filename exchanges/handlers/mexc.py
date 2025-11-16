from .base import CCXTBase

class MEXCHandler(CCXTBase):
    def __init__(self, api_key, api_secret, config=None):
        super().__init__(api_key, api_secret, 'mexc', config)