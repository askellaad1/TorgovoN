import logging
import threading
import time
import ccxt
import pytz
from datetime import datetime
import requests
from asgiref.sync import sync_to_async
from .base_bot import BaseBot
from bots.models import Order, Indicator

logger = logging.getLogger('TorgovoN.BybitBot')


class BybitBotHandler(BaseBot):
    """
    Full Bybit bot implementation with all original logic preserved.
    CCXT calls are kept intact as per user request.
    """

    def __init__(self, bot_instance, pair_config):
        self.bot_instance = bot_instance
        self.user = bot_instance.user
        self.pair_config = pair_config

        quote_currency = self.pair_config['pair_symbol'].split('/')[1]
        self.symbol = f"{pair_config['pair_symbol']}:{quote_currency}"

        # Technical indicators
        self.EMA = 0.0
        self.BB = None
        self.TSI = None
        self.ADX = None
        self.RSI = 0.0
        self.PrevRSI = 0.0
        self.RSI_color = None
        self.RSI_prev_color = None

        # Trading state
        self.current_side = "None"
        self.count = 0
        self.current_price = 0.0
        self.exchange = self._initialize_exchange()

        # Threading
        self.bot_running = False
        self.monitoring_threads = []
        self.lock = threading.Lock()
        self.monitoring = False
        self._stop_event = threading.Event()

        # Performance tracking
        self.reason = ""
        self.PrevReason = ""
        self.Percentage = 0.0
        self.Unrealized_Pnl = 0.0
        self.last_trade_pnl = 0.0
        self.favor_lvl = []
        self.against_lvl = []

        # Initialize conditions
        self.update_conditions()

        logger.info(f"BybitBotHandler initialized for {self.symbol}")

    def _initialize_exchange(self):
        """Initialize CCXT Bybit exchange"""
        try:
            exchange = ccxt.bybit({
                "apiKey": self.user.exchange_accounts.first().api_key_encrypted,
                "secret": self.user.exchange_accounts.first().api_secret_encrypted,
                "enableRateLimit": True,
                "options": {
                    "defaultType": "linear",
                    "trade.type": "linear",
                }
            })
            if hasattr(self.user, 'Demo') and self.user.Demo:
                exchange.enable_demo_trading(True)

            logger.info("Bybit exchange initialized")
            return exchange
        except Exception as e:
            logger.error(f'Bybit Exchange initialization failed: {e}')
            raise

    def reset_trading_state(self):
        """Reset bot state"""
        self.monitoring = False
        self._stop_event.set()
        self.EMA = 0.0
        self.BB = None
        self.TSI = None
        self.ADX = None
        self.RSI = 0.0
        self.PrevRSI = 0.0
        self.RSI_color = None
        self.RSI_prev_color = None
        self.BB = ""
        self.current_side = "None"
        self.count = 0
        self.PrevReason = self.reason
        self.reason = ""
        self.bot_running = False
        self.favor_lvl = []
        self.against_lvl = []
        self.update_conditions()
        self._wait_for_threads()

    def _wait_for_threads(self):
        """Wait for all monitoring threads to finish"""
        for thread in self.monitoring_threads:
            if thread.is_alive():
                thread.join(timeout=5.0)
                if thread.is_alive():
                    logger.warning(f"Thread {thread.name} did not stop gracefully")
        self.monitoring_threads.clear()

    def stop_bot(self):
        """Properly stop the bot and clean up all threads"""
        logger.info(f"Stopping bot for {self.symbol}")
        self.monitoring = False
        self._stop_event.set()
        self._wait_for_threads()
        self.bot_running = False
        logger.info(f"Bot stopped for {self.symbol}")

    def update_conditions(self):
        """Update trading conditions - YOUR ORIGINAL LOGIC"""
        with self.lock:
            logger.info("Updating conditions inside Lock")
            try:
                self.current_price = self.exchange.fetch_ticker(self.symbol)['last']
            except Exception as e:
                logger.error(f"Failed to fetch ticker: {e}")
                self.current_price = 0.0

            self.EmaBuyCondition = (self.current_price >= self.EMA != 0)
            self.EmaSellCondition = (self.current_price <= self.EMA != 0)

            rsi_lower = self.pair_config.get('RSI_Lower', 30)
            rsi_upper = self.pair_config.get('RSI_Upper', 70)

            self.RsiBuyCondition = (self.PrevRSI <= rsi_lower and self.RSI_color == 'white')
            self.RsiSellCondition = (self.PrevRSI >= rsi_upper and self.RSI_color == 'white')

            self.BBBuyCondition = (
                    self.BB == "Crossing Down Band" or self.BB == "Closed Below Lower Band" or self.BB == "Up Arrow"
            )
            self.BBSellCondition = (
                    self.BB == "Crossing Up Band" or self.BB == "Closed Above Upper Band" or self.BB == "Down Arrow"
            )

            self.NoTrade = (self.count == 0 and self.current_side == "None")
            self.BuyTrade = (self.count == 1 and self.current_side == "Buy")
            self.SellTrade = (self.count == 1 and self.current_side == "Sell")

    def get_indicator_data(self):
        return f'Symbol: {self.symbol} - CurrentPrice: {self.current_price} - EMA: {self.EMA} - BB: {self.BB} - RSI: {self.RSI} - PrevRSI: {self.PrevRSI} - RSI_Color: {self.RSI_color} - PrevRSI_Color: {self.RSI_prev_color}'

    def startBot(self):
        """Main bot execution loop - YOUR ORIGINAL LOGIC"""
        self.update_conditions()
        try:
            self.current_price = self.exchange.fetch_ticker(self.symbol)["last"]
        except Exception as e:
            logger.error(f"Failed to fetch initial price: {e}")
            self.current_price = 0.0

        self.bot_running = True
        logger.info(f"{self.user.username} BYBIT BOT START")
        logger.info(f"Current side: {self.current_side}")

        current_price = self.current_price
        logger.info(f"Initial price: {current_price}")

        if self.NoTrade:
            # BUY logic
            if (self.EmaBuyCondition and self.RsiBuyCondition and
                    (self.pair_config['EMA_RSI_Entry'] == 'buy' or self.pair_config['EMA_RSI_Entry'] == 'both')):
                data = self.prepare_order_data("Buy", current_price)
                self.count = 1
                self.current_side = "Buy"
                self.reason = 'Bybit EMA + RSI BUY LONG (CASE1)'
                detail = self.calculated_grid_orders(data)
                self.save_order('BUY', 'Bybit EMA + RSI BUY LONG (CASE1)', detail)
                self.print_details("BUY1", detail)

            elif self.BBBuyCondition and self.EmaBuyCondition and (
                    self.pair_config['EMA_BB_Entry'] == 'buy' or self.pair_config['EMA_BB_Entry'] == 'both'):
                data = self.prepare_order_data("Buy", self.current_price)
                self.count = 1
                self.current_side = "Buy"
                self.reason = 'Bybit EMA + BOLLINGER BANDS BUY LONG (CASE2)) '
                detail = self.calculated_grid_orders(data)
                self.save_order('BUY', 'Bybit EMA + BOLLINGER BANDS BUY LONG (CASE2)) ', detail)
                self.print_details("BUY2", detail=detail)

            elif self.RsiBuyCondition and self.BBBuyCondition and (
                    self.pair_config['BB_RSI_Entry'] == 'buy' or self.pair_config['BB_RSI_Entry'] == 'both'):
                data = self.prepare_order_data("Buy", current_price)
                self.current_side = "Buy"
                self.count = 1
                self.reason = 'Bybit BOLLINGER BANDS + RSI BUY LONG (CASE3)'
                detail = self.calculated_grid_orders(data)
                self.save_order('BUY', 'Bybit BOLLINGER BANDS + RSI BUY LONG (CASE3)', detail)
                self.print_details("BUY3", detail)

            elif self.RsiBuyCondition and (
                    self.pair_config['RSI_Entry'] == 'both' or self.pair_config['RSI_Entry'] == 'buy'):
                data = self.prepare_order_data("Buy", current_price)
                self.current_side = "Buy"
                self.count = 1
                self.reason = 'Bybit ONLY RSI BUY LONG (CASE4)'
                detail = self.calculated_grid_orders(data)
                self.save_order('BUY', 'Bybit ONLY RSI BUY LONG (CASE4)', detail)
                self.print_details("BUY4", detail)

            elif self.BBBuyCondition and (
                    self.pair_config['BB_Entry'] == 'buy' or self.pair_config['BB_Entry'] == 'both'):
                data = self.prepare_order_data("Buy", current_price)
                self.current_side = "Buy"
                self.count = 1
                self.reason = 'Bybit ONLY BOLLINGER BANDS BUY LONG (CASE5))'
                detail = self.calculated_grid_orders(data)
                self.save_order('BUY', 'Bybit ONLY BOLLINGER BANDS BUY LONG (CASE5))', detail)
                self.print_details("BUY5", detail)

            elif self.EmaBuyCondition and self.RsiBuyCondition and self.BBBuyCondition and (
                    self.pair_config['EMA_BB_RSI_Entry'] == 'buy' or self.pair_config['EMA_BB_RSI_Entry'] == 'both'):
                data = self.prepare_order_data("Buy", current_price)
                self.current_side = "Buy"
                self.count = 1
                self.reason = 'Bybit EMA RSI BOLLINGER BANDS LONG (CASE6))'
                detail = self.calculated_grid_orders(data)
                self.save_order('BUY', 'Bybit EMA RSI BOLLINGER BANDS BUY LONG (CASE6))', detail)
                self.print_details("BUY6", detail)

            # SELL logic
            elif (self.EmaSellCondition and self.RsiSellCondition and
                  (self.pair_config['EMA_RSI_Entry'] == 'sell' or self.pair_config['EMA_RSI_Entry'] == 'both')):
                data = self.prepare_order_data("Sell", current_price)
                self.count = 1
                self.current_side = "Sell"
                self.reason = 'Bybit EMA + RSI SELL SHORT (SELL CASE1)'
                detail = self.calculated_grid_orders(data)
                self.save_order('SELL', 'Bybit EMA + RSI SELL SHORT (SELL CASE1)', details=detail)
                self.print_details("SELL1", detail)

            elif self.BBSellCondition and self.EmaSellCondition and (
                    self.pair_config['EMA_BB_Entry'] == 'sell' or self.pair_config['EMA_BB_Entry'] == 'both'):
                data = self.prepare_order_data("Sell", current_price)
                self.count = 1
                self.current_side = "Sell"
                self.reason = 'Bybit EMA + BOLLINGER BANDS SELL SHORT (CASE2)'
                detail = self.calculated_grid_orders(data)
                self.save_order('SELL', 'Bybit EMA + BOLLINGER BANDS SELL SHORT (CASE2)', details=detail)
                self.print_details("SELL2", detail)

            elif self.BBSellCondition and self.RsiSellCondition and (
                    self.pair_config['BB_RSI_Entry'] == 'sell' or self.pair_config['BB_RSI_Entry'] == 'both'):
                data = self.prepare_order_data("Sell", current_price)
                self.count = 1
                self.current_side = "Sell"
                self.reason = 'Bybit BOLLINGER BANDS + RSI SELL SHORT (CASE3)'
                detail = self.calculated_grid_orders(data)
                self.save_order('SELL', 'Bybit BOLLINGER BANDS + RSI SELL SHORT (CASE3)', details=detail)
                self.print_details("SELL3", detail)

            elif self.RsiSellCondition and (
                    self.pair_config['RSI_Entry'] == 'sell' or self.pair_config['RSI_Entry'] == 'both'):
                data = self.prepare_order_data("Sell", current_price)
                self.count = 1
                self.current_side = "Sell"
                self.reason = 'Bybit ONLY RSI SELL SHORT (CASE4)'
                detail = self.calculated_grid_orders(data)
                self.save_order('SELL', 'Bybit ONLY RSI SELL SHORT (CASE4)', details=detail)
                self.print_details("SELL4", detail)

            elif self.BBSellCondition and (
                    self.pair_config['BB_Entry'] == 'sell' or self.pair_config['BB_Entry'] == 'both'):
                data = self.prepare_order_data("Sell", current_price)
                self.count = 1
                self.current_side = "Sell"
                self.reason = 'Bybit ONLY BOLLINGER BANDS SELL SHORT (CASE5)'
                detail = self.calculated_grid_orders(data)
                self.save_order('SELL', 'Bybit ONLY BOLLINGER BANDS SELL SHORT (CASE5)', details=detail)
                self.print_details("SELL5", detail)

            elif self.EmaSellCondition and self.RsiSellCondition and self.BBSellCondition and (
                    self.pair_config['EMA_BB_RSI_Entry'] == 'sell' or self.pair_config['EMA_BB_RSI_Entry'] == 'both'):
                data = self.prepare_order_data("Sell", current_price)
                self.count = 1
                self.current_side = "Sell"
                self.reason = 'Bybit EMA RSI BOLLINGER BANDS SELL SHORT (CASE6)'
                detail = self.calculated_grid_orders(data)
                self.save_order('SELL', 'Bybit EMA RSI BOLLINGER BANDS SELL SHORT (CASE6)', details=detail)
                self.print_details("SELL6", detail)

        elif self.BuyTrade:
            logger.info('Checking TP Buy Cases')
            if self.BBSellCondition and (self.pair_config['BB_Exit'] == 'tp' or self.pair_config['BB_Exit'] == 'both'):
                detail = self.close_all_orders('Bybit BOLLINGER BANDS Only (TP CASE 1))')
                self.print_details("TP_BUY1", detail)

            elif self.RsiSellCondition and (self.pair_config['RSI_Exit'] == 'tp' or self.pair_config['RSI_Exit'] == 'both'):
                detail = self.close_all_orders('Bybit RSI Only (TP CASE 2)')
                self.print_details("TP_BUY2", detail)

            elif self.RsiSellCondition and self.BBSellCondition and (
                    self.pair_config['BB_RSI_Exit'] == 'tp' or self.pair_config['BB_RSI_Exit'] == 'both'):
                detail = self.close_all_orders("Bybit TP-BUY BOLLINGER BANDS + RSI -- (TP Buy CASE3)")
                self.print_details("TP_BUY3", detail)

            elif self.BBSellCondition and (self.EmaSellCondition or self.EmaBuyCondition) and (
                    self.pair_config['EMA_BB_Exit'] == 'tp' or self.pair_config['EMA_BB_Exit'] == 'both'):
                detail = self.close_all_orders("Bybit EMA + Bollinger Bands -- (TP-BUY-CASE 4)")
                self.print_details("TP_BUY4", detail)

        elif self.SellTrade:
            if self.RsiBuyCondition and (self.pair_config['RSI_Exit'] == 'tp' or self.pair_config['RSI_Exit'] == 'both'):
                detail = self.close_all_orders('Bybit RSI SELL TP (CASE1)', )
                self.print_details("TP_SELL1", detail)

            elif self.BBBuyCondition and self.RsiBuyCondition and (
                    self.pair_config['BB_RSI_Exit'] == 'tp' or self.pair_config['BB_RSI_Exit'] == 'both'):
                detail = self.close_all_orders('Bybit BOLLINGER BANDS + RSI SELL TP (CASE2)')
                self.print_details("TP_SELL2", detail)

            elif self.BBBuyCondition and (self.pair_config['BB_Exit'] == 'tp' or self.pair_config['BB_Exit'] == 'both'):
                detail = self.close_all_orders('Bybit BB SELl TP (SELL TP CASE 3)')
                self.print_details("TP_SELL3", detail)

            elif self.EmaBuyCondition and self.BBBuyCondition and (
                    self.pair_config['EMA_BB_Exit'] == 'tp' or self.pair_config['EMA_BB_Exit'] == 'both'):
                detail = self.close_all_orders("Bybit EMA BB TP (SELL TP CASE 4)")
                self.print_details("EMA_SELL4", detail)

    async def buy_order(self):
        """Async wrapper for buy order"""
        if self.NoTrade:
            data = self.prepare_order_data("Buy", self.current_price)
            self.count = 1
            self.current_side = "Buy"
            self.PrevReason = self.reason
            self.reason = 'Bybit Custom BUY'
            detail = self.calculated_grid_orders(data)
            await sync_to_async(self.save_order)('BUY', 'Bybit CUSTOM BUY ORDER', details=detail)
            self.print_details("C_BUY", detail)
            self.update_conditions()
        else:
            logger.info("Already Bought")

    async def sell_order(self):
        """Async wrapper for sell order"""
        if self.NoTrade:
            data = self.prepare_order_data("Sell", self.current_price)
            self.count = 1
            self.current_side = "Sell"
            self.PrevReason = self.reason
            self.reason = 'Bybit Custom SELL'
            detail = self.calculated_grid_orders(data)
            await sync_to_async(self.save_order)('SELL', 'Bybit CUSTOM SELL ORDER', details=detail)
            self.print_details("C_SELL", detail)
            self.update_conditions()
        else:
            logger.info("Already Sold")

    async def close_custom_order(self):
        """Async wrapper for closing orders"""
        if self.BuyTrade or self.SellTrade:
            detail = await sync_to_async(self.close_all_orders)(description="Bybit CUSTOM CLOSE BUY ORDER")
            self.print_details("C_CLOSE_BUY", detail)
        else:
            logger.info('No Trade in Record')

    # --- ALL YOUR ORIGINAL HELPER METHODS BELOW ---

    def SendTelegramMessage(self, message):
        try:
            url = f"https://api.telegram.org/bot {self.user.Token}/sendMessage?chat_id={self.user.Bot_ID}&text={message}"
            logger.info('Telegram Message Sent')
            requests.get(url).json()
        except Exception as e:
            logger.info(f"Cannot send Telegram message {e}")

    def SendTelegramChannelMessage(self, message):
        try:
            url = f"https://api.telegram.org/bot {self.user.Channel_Token}/sendMessage?chat_id={self.user.Channel_Bot_ID}&text={message}"
            logger.info('Telegram Channel Message Sent')
            requests.get(url).json()
        except Exception as e:
            logger.info(f"Cannot send Telegram Channel message {e}")

    def prepare_order_data(self, side, current_price):
        config = self.pair_config
        if self.pair_config['Amount_Type'] == "dollar":
            quantity = round(config['quantity'] / current_price, 4)
            favor_level_qty = round(config['favor_level_qty'] / current_price, 4)
            against_level_qty = round(config['against_level_qty'] / current_price, 4)
            logger.info(f'Dollar calculated: {quantity}, {favor_level_qty}, {against_level_qty}')
        else:
            quantity = config['quantity']
            favor_level_qty = config['favor_level_qty']
            against_level_qty = config['against_level_qty']
            logger.info(f'Coin calculated: {quantity}, {favor_level_qty}, {against_level_qty}')

        quantity = float(self.exchange.amount_to_precision(self.symbol, quantity))
        favor_level_qty = float(self.exchange.amount_to_precision(self.symbol, favor_level_qty))
        against_level_qty = float(self.exchange.amount_to_precision(self.symbol, against_level_qty))

        data = {
            "category": 'futures',
            "symbol": self.symbol,
            "Order_Type": config['Order_Type'],
            "side": side,
            "qty": quantity,
            "price": current_price,
            "favor_levels": config['favor_levels'],
            "against_levels": config['against_levels'],
            "favor_level_qty": favor_level_qty,
            "against_level_qty": against_level_qty,
            "favor_level_difference": config['favor_level_difference'],
            "against_level_difference": config['against_level_difference']
        }
        return data

    def fetch_current_price(self):
        """Fetch the current market price"""
        ticker, symbol = self.exchange.fetch_ticker, self.symbol
        self.current_price = ticker(symbol)["last"]
        thread_id = threading.get_ident()
        logger.info(f"Thread ID: {thread_id} | Fetched current price: {self.current_price}")
        return self.current_price

    def save_order(self, side, description, details):
        """Place an order and save it to the database"""
        indicator = Indicator.objects.create(
            Pair=self.symbol,
            user=self.user,
            EMA=self.EMA,
            RSI=self.RSI,
            Prev_RSI=self.PrevRSI,
            Color=self.RSI_color,
            Prev_Color=self.RSI_prev_color,
            BB=self.BB,
            TSI=self.TSI,
            ADX=self.ADX
        )
        order = Order.objects.create(
            Pair=self.symbol,
            user=self.user,
            PairConfig_id=self.pair_config["id"],
            Indicators=indicator,
            Side=side,
            Category="futures",
            Order_type="Market",
            Quantity=self.pair_config["quantity"],
            Price=self.current_price,
            Exchange="Bybit",
            Description=description,
            Details=details
        )
        logger.info(f"Placed order: {order}")
        return order

    def create_order(self, order_type, side, quantity, price):
        """Execute order on exchange - CCXT CALL PRESERVED"""
        try:
            if self.pair_config['Amount_Type'] == "dollar":
                if order_type == 'market':
                    data = self.exchange.create_market_order_with_cost(
                        self.symbol, side, quantity, params={'category': 'linear'}
                    )
                elif order_type == 'limit':
                    data = self.exchange.create_order(
                        self.symbol, order_type, side, quantity, price, params={'category': 'linear'}
                    )
            else:
                data = self.exchange.create_order(
                    self.symbol, order_type, side, quantity, price, params={'category': 'linear'}
                )
            logger.info(f'Order type: {order_type} - Side: {side} - Quantity: {quantity} - Price: {price}')
            return data
        except Exception as e:
            logger.error(f"Cannot create order {e}")
            raise

    def close_open_order(self, description):
        """Close open position - CCXT CALL PRESERVED"""
        try:
            closing_symbol = self.symbol.replace('/', '')
            position = self.exchange.fetch_positions(symbols=closing_symbol, params={'category': 'linear'})
            self.Unrealized_Pnl = float((position[0]['unrealizedPnl']))
            size = float(position[0]['contracts'])
            side = position[0]['side']

            message = f"User: {self.user.username}\nBybit \nPair: {self.symbol} {datetime.now(pytz.timezone('Asia/Karachi'))}\n Closing Position\n {position}"
            channel_message = f"""Timezone: GMT+5 \n Time: {datetime.now(pytz.timezone('Asia/Karachi'))} \nExchange: Bybit \nSymbol: {self.symbol} \nClosing Position: {position} """
            self.SendTelegramMessage(message)
            self.SendTelegramChannelMessage(channel_message)

            if side == 'short':
                detail = self.exchange.create_order(
                    symbol=closing_symbol, type='market', amount=size, side='buy', params={'reduceOnly': True}
                )
                self.save_order(side, description, detail)
                return detail
            elif side == 'long':
                detail = self.exchange.create_order(
                    symbol=closing_symbol, type='market', amount=size, side='sell', params={'reduceOnly': True}
                )
                self.save_order(side, description, detail)
                return detail
        except Exception as e:
            logger.info(f"No position found: {e}")
            return None

    def close_all_orders(self, description):
        """Cancel all orders and close position - CCXT CALLS PRESERVED"""
        logger.info(f"Cancelling all limit orders for {self.symbol}")
        closing_symbol = self.symbol.replace('/', '')
        self.reset_trading_state()
        self.exchange.cancel_all_orders(symbol=closing_symbol)
        position = self.close_open_order(description)
        self.reason = description
        logger.info(f'All BYBIT Orders Closed: {description}')
        return position

    def calculate_grids(self, side):
        """Calculate grid price levels"""
        favor_levels = []
        against_levels = []
        if side.lower() == 'buy':
            for levels in range(self.pair_config["favor_levels"]):
                favor_levels.append(
                    round(self.current_price * (1 + (levels + 1) * self.pair_config['favor_level_difference'] / 100), 6)
                )
            for levels in range(self.pair_config['against_levels']):
                against_levels.append(
                    round(self.current_price * (1 - (levels + 1) * self.pair_config['against_level_difference'] / 100), 6)
                )
        if side.lower() == 'sell':
            for levels in range(self.pair_config['favor_levels']):
                favor_levels.append(
                    round(self.current_price * (1 - (levels + 1) * self.pair_config['favor_level_difference'] / 100), 6)
                )
            for levels in range(self.pair_config['against_levels']):
                against_levels.append(
                    round(self.current_price * (1 + (levels + 1) * self.pair_config['against_level_difference'] / 100), 6)
                )
        return favor_levels, against_levels

    def monitor_grid_orders(self, side, entry_price, favor_levels, against_levels,
                            favor_level_qty, against_level_qty):
        """Grid monitoring logic - YOUR FULL IMPLEMENTATION"""
        last_favor_level = None
        last_against_level = None
        logger.info('Monitoring Bybit Grid Orders.')
        self.current_price = self.fetch_current_price()

        favor_order_map = {}
        against_order_map = {}

        def place_and_register(price, ord_side, qty, register_map):
            try:
                resp = self.create_order('limit', ord_side, qty, float(price))
                order_id = resp.get('id') if isinstance(resp, dict) else getattr(resp, 'id', None)
                if order_id is None:
                    if isinstance(resp, dict):
                        order_id = resp.get('orderId') or resp.get('clientOrderId')
                    else:
                        order_id = getattr(resp, 'orderId', None) or getattr(resp, 'clientOrderId', None)
                if order_id is None:
                    open_orders = self.exchange.fetch_open_orders(symbol=self.symbol, params={'category': 'linear'})
                    for o in open_orders:
                        if float(o.get('price', 0)) == float(price) and o.get('side', '').lower() == ord_side.lower():
                            order_id = o.get('id') or o.get('orderId') or o.get('clientOrderId')
                            break
                if order_id:
                    register_map[float(price)] = order_id
                else:
                    logger.warning(f'Placed order but no id found for price {price} side {ord_side}.')
                return order_id
            except Exception as e:
                logger.error(f"Error placing order at {price} side {ord_side}: {e}")
                return None

        # Initialize maps
        try:
            open_orders = self.exchange.fetch_open_orders(symbol=self.symbol, params={'category': 'linear'})
            for o in open_orders:
                try:
                    p = round(float(o.get('price')), 8)
                except:
                    continue
                s = o.get('side', '').lower()
                oid = o.get('id') or o.get('orderId') or o.get('clientOrderId')
                if s == 'sell':
                    if side.lower() == 'buy':
                        favor_order_map[p] = oid
                    else:
                        against_order_map[p] = oid
                elif s == 'buy':
                    if side.lower() == 'buy':
                        against_order_map[p] = oid
                    else:
                        favor_order_map[p] = oid
        except Exception as e:
            logger.warning(f"Could not seed open orders into maps: {e}")

        # Sort levels
        reverse_for_favor = (side.lower() == 'sell')
        reverse_for_against = (side.lower() == 'buy')
        favor_levels.sort(reverse=reverse_for_favor)
        against_levels.sort(reverse=reverse_for_against)

        while self.monitoring:
            try:
                open_orders = self.exchange.fetch_open_orders(symbol=self.symbol, params={'category': 'linear'})
                current_buy_prices = set(float(order['price']) for order in open_orders if order['side'].lower() == 'buy')
                current_sell_prices = set(float(order['price']) for order in open_orders if order['side'].lower() == 'sell')

                def is_filled(order_id):
                    if not order_id:
                        return False
                    try:
                        o = self.exchange.fetch_order(order_id, symbol=self.symbol, params={'category': 'linear'})
                        status = o.get('status') or o.get('state')
                        if isinstance(status, str) and status.lower() in ('closed', 'filled', 'filled_partially'):
                            return True
                        return False
                    except Exception:
                        try:
                            for o2 in open_orders:
                                if (o2.get('id') == order_id) or (o2.get('orderId') == order_id) or (o2.get('clientOrderId') == order_id):
                                    return False
                            return True
                        except:
                            return False

                # Process favor orders
                favor_keys = sorted(list(favor_order_map.keys()), reverse=reverse_for_favor)
                for price in favor_keys:
                    order_id = favor_order_map.get(price)
                    if is_filled(order_id):
                        executed_level = float(price)
                        logger.info(f"Favor order filled at {executed_level}")
                        favor_order_map.pop(price, None)
                        try:
                            if price in [float(x) for x in favor_levels]:
                                for i, v in enumerate(favor_levels):
                                    if float(v) == price:
                                        favor_levels.pop(i)
                                        break
                        except Exception:
                            pass

                        if last_favor_level is not None and executed_level >= float(last_favor_level):
                            if entry_price not in favor_levels and entry_price not in against_levels:
                                place_price = float(entry_price)
                                ord_side = 'sell' if side.lower() == 'buy' else 'buy'
                                if ord_side == 'buy':
                                    if float(place_price) in current_buy_prices:
                                        continue
                                else:
                                    if float(place_price) in current_sell_prices:
                                        continue
                                new_oid = place_and_register(place_price, ord_side, against_level_qty, against_order_map)
                                if new_oid:
                                    against_levels.append(place_price)
                                    against_levels.sort(reverse=reverse_for_against)
                                    self.against_lvl = against_levels[:]
                                    open_orders = self.exchange.fetch_open_orders(symbol=self.symbol, params={'category': 'linear'})
                                    current_buy_prices = set(float(order['price']) for order in open_orders if order['side'].lower() == 'buy')
                                    current_sell_prices = set(float(order['price']) for order in open_orders if order['side'].lower() == 'sell')
                            last_favor_level = executed_level
                            entry_price = executed_level
                        else:
                            if entry_price not in favor_levels and entry_price not in against_levels:
                                place_price = float(entry_price)
                                ord_side = 'sell' if side.lower() == 'buy' else 'buy'
                                if ord_side == 'buy':
                                    if float(place_price) in current_buy_prices:
                                        continue
                                else:
                                    if float(place_price) in current_sell_prices:
                                        continue
                                new_oid = place_and_register(place_price, ord_side, against_level_qty, against_order_map)
                                if new_oid:
                                    against_levels.append(place_price)
                                    against_levels.sort(reverse=reverse_for_against)
                                    self.against_lvl = against_levels[:]
                                    open_orders = self.exchange.fetch_open_orders(symbol=self.symbol, params={'category': 'linear'})
                                    current_buy_prices = set(float(order['price']) for order in open_orders if order['side'].lower() == 'buy')
                                    current_sell_prices = set(float(order['price']) for order in open_orders if order['side'].lower() == 'sell')
                            last_favor_level = executed_level
                            entry_price = executed_level
                        favor_levels.sort(reverse=reverse_for_favor)
                        self.favor_lvl = favor_levels[:]

                # Process against orders
                against_keys = sorted(list(against_order_map.keys()), reverse=reverse_for_against)
                for price in against_keys:
                    order_id = against_order_map.get(price)
                    if is_filled(order_id):
                        executed_level = float(price)
                        logger.info(f"Against order filled at {executed_level}")
                        against_order_map.pop(price, None)
                        try:
                            if price in [float(x) for x in against_levels]:
                                for i, v in enumerate(against_levels):
                                    if float(v) == price:
                                        against_levels.pop(i)
                                        break
                        except Exception:
                            pass

                        if last_against_level is not None and executed_level <= float(last_against_level):
                            if entry_price not in favor_levels and entry_price not in against_levels:
                                place_price = float(entry_price)
                                ord_side = 'buy' if side.lower() == 'buy' else 'sell'
                                if ord_side == 'buy':
                                    if float(place_price) in current_buy_prices:
                                        continue
                                else:
                                    if float(place_price) in current_sell_prices:
                                        continue
                                new_oid = place_and_register(place_price, ord_side, favor_level_qty, favor_order_map)
                                if new_oid:
                                    favor_levels.append(place_price)
                                    favor_levels.sort(reverse=reverse_for_favor)
                                    self.favor_lvl = favor_levels[:]
                                    open_orders = self.exchange.fetch_open_orders(symbol=self.symbol, params={'category': 'linear'})
                                    current_buy_prices = set(float(order['price']) for order in open_orders if order['side'].lower() == 'buy')
                                    current_sell_prices = set(float(order['price']) for order in open_orders if order['side'].lower() == 'sell')
                            last_against_level = executed_level
                            entry_price = executed_level
                        else:
                            if entry_price not in favor_levels and entry_price not in against_levels:
                                place_price = float(entry_price)
                                ord_side = 'buy' if side.lower() == 'buy' else 'sell'
                                if ord_side == 'buy':
                                    if float(place_price) in current_buy_prices:
                                        continue
                                else:
                                    if float(place_price) in current_sell_prices:
                                        continue
                                new_oid = place_and_register(place_price, ord_side, favor_level_qty, favor_order_map)
                                if new_oid:
                                    favor_levels.append(place_price)
                                    favor_levels.sort(reverse=reverse_for_favor)
                                    self.favor_lvl = favor_levels[:]
                                    open_orders = self.exchange.fetch_open_orders(symbol=self.symbol, params={'category': 'linear'})
                                    current_buy_prices = set(float(order['price']) for order in open_orders if order['side'].lower() == 'buy')
                                    current_sell_prices = set(float(order['price']) for order in open_orders if order['side'].lower() == 'sell')
                            last_against_level = executed_level
                            entry_price = executed_level
                        against_levels.sort(reverse=reverse_for_against)
                        self.against_lvl = against_levels[:]

                time.sleep(1)

            except Exception as e:
                logger.error(f'Error in monitor_grid_orders: {e}')
                time.sleep(2)

    def monitor_lossProfit(self, side):
        """Monitor P&L for stop loss/take profit"""
        loss_profit_percentage = 0.0
        time.sleep(4)
        message = f"User: {self.user.username}\nPair: {self.symbol}\n{datetime.now(pytz.timezone('Asia/Karachi'))}\nCurrent Price: {self.current_price}\nEMA: {self.EMA}\nRSI: {self.RSI}\nPrevRSI: {self.PrevRSI}\nRSI_Color: {self.RSI_color}\nBB: {self.BB}\nCurrent Side: {self.current_side}\nCount: {self.count}"

        while self.monitoring and not self._stop_event.is_set():
            try:
                loss_profit_percentage = self.check_lossProfit_percent()
                if loss_profit_percentage is None:
                    loss_profit_percentage = 0.0

                elif self.pair_config['SL_Exit'] == 'sl' or self.pair_config['SL_Exit'] == 'both':
                    if loss_profit_percentage <= self.pair_config['Stop_Loss']:
                        reason = "SL"
                        message = message + reason
                        self.SendTelegramMessage(message)
                        channel_message = f"Timezone: GMT+ \nTime: {datetime.now(pytz.timezone('Asia/Karachi'))} \nExchange: Bybit \nSymbol: {self.symbol} \nClosing Position \nStop Loss Price: ({self.current_price})"
                        self.SendTelegramChannelMessage(channel_message)
                        self.close_all_orders('SL hit Position and closed')
                        self.print_details("SL", loss_profit_percentage)

                if self.pair_config['SL_Exit'] == 'tp' or self.pair_config['SL_Exit'] == 'both':
                    if loss_profit_percentage >= self.pair_config['Take_Profit']:
                        reason = "TP"
                        message = message + reason
                        self.SendTelegramMessage(message)
                        channel_message = f"""Timezone: GMT+ \nTime: {datetime.now(pytz.timezone('Asia/Karachi'))} \nExchange: Bybit \nSymbol: {self.symbol} \nClosing Position\nStop Loss Price:({self.current_price})"""
                        self.SendTelegramChannelMessage(channel_message)
                        self.close_all_orders('TP hit Position and closed')
                        self.print_details("TP", loss_profit_percentage)
                        logger.info("TP HIT!!! - Position closed\n")

            except Exception as e:
                logger.error(f"Loss Profit Exception: {str(e)}")

            if self._stop_event.wait(timeout=5.0):
                break

    def check_lossProfit_percent(self):
        """Check current P&L percentage"""
        try:
            position = self.exchange.fetch_position(symbol=self.symbol, params={'category': 'linear'})
            if position:
                size = float(position['notional'])
                pnl = float((position['unrealizedPnl']))
                self.Unrealized_Pnl = pnl
                self.Percentage = pnl / size * 1000
                logger.info(f'User: {self.user.username} Pair: {self.symbol} Percentage: {self.Percentage} PNL: {self.Unrealized_Pnl} Price: {self.current_price}')
                if self.pair_config['SLTP_Type'] == 'percentage':
                    return self.Percentage
                elif self.pair_config['SLTP_Type'] == 'dollars':
                    return self.Unrealized_Pnl
        except Exception as e:
            logger.error(f"Check Loss Profit Exception: {str(e)}")
            self.Unrealized_Pnl = 0.0
            self.Percentage = 0.0
        return 0.0

    def calculated_grid_orders(self, data):
        """Calculate and place grid orders - YOUR FULL LOGIC"""
        self.bot_running = True
        self.monitoring = True
        logger.info(f'Bybit Calculating Grids for {data["symbol"]}')

        symbol = data['symbol']
        side = data['side']
        qty = data['qty']
        price = data['price']
        favor_level_qty = data['favor_level_qty']
        against_level_qty = data['against_level_qty']

        logger.info(f"Grid data: {data['symbol']} - {data['Order_Type']} - {side} - {qty} - {price}")

        # Open initial order
        initial_order = None
        try:
            if self.pair_config['Amount_Type'] == "dollar":
                if side == 'Buy':
                    initial_order = self.exchange.create_market_buy_order_with_cost(
                        self.symbol, cost=qty, params={'category': 'linear'}
                    )
                elif side == 'Sell':
                    initial_order = self.exchange.create_market_sell_order_with_cost(
                        self.symbol, cost=qty, params={'category': 'linear'}
                    )
            elif self.pair_config['Amount_Type'] == "coin":
                initial_order = self.create_order(
                    order_type=self.pair_config['Order_Type'], side=side, quantity=qty, price=price
                )
        except Exception as e:
            logger.error('Creating Order Failed at calculated_grid_orders', exc_info=True)
            raise

        favor_levels, against_levels = self.calculate_grids(side)
        self.favor_lvl, self.against_lvl = favor_levels, against_levels

        if side.lower() == 'buy':
            for level in favor_levels:
                level_price = float(level)
                try:
                    self.create_order('limit', 'sell', favor_level_qty, level_price)
                except Exception as e:
                    logger.error('Creating favor level order failed', exc_info=True)

            for level in against_levels:
                level_price = float(level)
                try:
                    self.create_order('limit', 'buy', against_level_qty, level_price)
                except Exception as e:
                    logger.error('Creating against level order failed', exc_info=True)

        if side.lower() == 'sell':
            for level in favor_levels:
                level_price = float(level)
                try:
                    self.create_order('limit', 'buy', favor_level_qty, level_price)
                except Exception as e:
                    logger.error('Creating favor level order failed', exc_info=True)

            for level in against_levels:
                level_price = float(level)
                try:
                    self.create_order('limit', 'sell', against_level_qty, level_price)
                except Exception as e:
                    logger.error('Creating against level order failed', exc_info=True)

        time.sleep(3)
        monitoring_thread = threading.Thread(
            target=self.monitor_grid_orders,
            args=(side, price, favor_levels, against_levels, favor_level_qty, against_level_qty),
            name=f"GridMonitor-{self.symbol}-{side}"
        )
        monitoring_thread.daemon = True
        monitoring_thread.start()
        self.monitoring_threads.append(monitoring_thread)

        return initial_order

    def print_details(self, case, detail=None):
        """Print trade details"""
        print(f"\n{'=' * 50}")
        print(f"CASE: {case}")
        print(f"User: {self.user.username}")
        print(f"Symbol: {self.symbol}")
        print(f"Current Price: {self.current_price}")
        print(f"Side: {self.current_side}")
        print(f"Reason: {self.reason}")
        print(f"Details: {detail}")
        print(f"{'=' * 50}\n")

        logger.info(f"CASE: {case} | User: {self.user.username} | Symbol: {self.symbol} | Price: {self.current_price} | Side: {self.current_side} | Reason: {self.reason}")