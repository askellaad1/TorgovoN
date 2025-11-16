from .base import CCXTBase


class BinanceHandler(CCXTBase):
    def __init__(self, api_key, api_secret, config=None):
        super().__init__(api_key, api_secret, 'binance', config)

    def get_futures_config(self):
        return {
            'options': {
                'defaultType': 'future',
                'adjustForTimeDifference': True,
            }
        }