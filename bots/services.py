from django.utils import timezone
from celery import current_app
from .models import Bot, TradeLog
from .tasks import execute_custom_trade, execute_grid_bot, execute_martingale_bot
import json

import json
import logging
from typing import Dict, Any, Optional
from django.core.cache import cache
from django.utils import timezone
from bots.models import Bot
from .bot_handlers.bybit_bot import BybitBotHandler

logger = logging.getLogger('TorgovoN.BotManager')


class TradingManagerService:
    """Redis-based bot manager preserving your original logic"""

    HANDLERS = {
        'binance': None,  # Will implement when you add BinanceBotHandler
        'bybit': BybitBotHandler,
        'mexc': None,  # Will implement when you add MexcBotHandler
        'kraken_spot': None,  # Will implement when you add KrakenBotHandler
    }

    BOT_KEY_PREFIX = "bot:active:"
    LOCK_PREFIX = "lock:bot:"

    def _get_bot_redis_key(self, user_id: str, pair_symbol: str, exchange: str) -> str:
        return f"{self.BOT_KEY_PREFIX}{user_id}:{pair_symbol}:{exchange}"

    def get_bot(self, user_id: str, pair_symbol: str, exchange: str) -> Optional[Dict[str, Any]]:
        """Get bot state from Redis"""
        key = self._get_bot_redis_key(user_id, pair_symbol, exchange)
        bot_data = cache.get(key)
        return json.loads(bot_data) if bot_data else None

    def create_bot(self, bot_instance: Bot, pair_config: Dict[str, Any]) -> str:
        """Create bot in Redis and start Celery task"""
        user_id = str(bot_instance.user.id)
        pair_symbol = pair_config['pair_symbol']
        exchange = bot_instance.exchange_account.exchange_name

        key = self._get_bot_redis_key(user_id, pair_symbol, exchange)

        # Use Redis lock for thread safety
        lock_key = f"{self.LOCK_PREFIX}{key}"
        with cache.lock(lock_key, timeout=10):
            if cache.get(key):
                logger.warning(f"Bot {key} already exists")
                return key

            # Store bot state
            bot_state = {
                'bot_id': str(bot_instance.id),
                'user_id': user_id,
                'pair_symbol': pair_symbol,
                'exchange': exchange,
                'is_active': True,
                'created_at': timezone.now().isoformat(),
                'config': pair_config,
            }

            cache.set(key, json.dumps(bot_state), timeout=86400)

            # Update DB
            bot_instance.is_active = True
            bot_instance.save()

            # Start Celery task
            from bots.tasks import execute_bot_loop
            execute_bot_loop.delay(str(bot_instance.id))

            logger.info(f"Created and started bot {key}")
            return key

    def start_bot(self, user_id: str, pair_symbol: str, exchange: str) -> bool:
        """Start existing bot"""
        key = self._get_bot_redis_key(user_id, pair_symbol, exchange)

        lock_key = f"{self.LOCK_PREFIX}{key}"
        with cache.lock(lock_key, timeout=10):
            bot_data = cache.get(key)
            if not bot_data:
                logger.warning(f"Bot {key} not found")
                return False

            bot_state = json.loads(bot_data)
            if bot_state['is_active']:
                logger.info(f"Bot {key} already running")
                return True

            bot_state['is_active'] = True
            cache.set(key, json.dumps(bot_state), timeout=86400)

            from bots.tasks import execute_bot_loop
            execute_bot_loop.delay(bot_state['bot_id'])

            logger.info(f"Restarted bot {key}")
            return True

    def stop_bot(self, user_id: str, pair_symbol: str, exchange: str) -> bool:
        """Stop bot by removing from Redis"""
        key = self._get_bot_redis_key(user_id, pair_symbol, exchange)

        lock_key = f"{self.LOCK_PREFIX}{key}"
        with cache.lock(lock_key, timeout=10):
            bot_data = cache.get(key)
            if bot_data:
                cache.delete(key)

                # Update DB
                try:
                    bot_instance = Bot.objects.get(id=json.loads(bot_data)['bot_id'])
                    bot_instance.is_active = False
                    bot_instance.save()
                except Bot.DoesNotExist:
                    pass

                logger.info(f"Stopped bot {key}")
                return True
            return False

    def refresh_bot_config(self, bot_instance: Bot, pair_config: Dict[str, Any]) -> bool:
        """Refresh config from DB"""
        user_id = str(bot_instance.user.id)
        pair_symbol = pair_config['pair_symbol']
        exchange = bot_instance.exchange_account.exchange_name

        key = self._get_bot_redis_key(user_id, pair_symbol, exchange)

        lock_key = f"{self.LOCK_PREFIX}{key}"
        with cache.lock(lock_key, timeout=10):
            bot_data = cache.get(key)
            if not bot_data:
                return False

            bot_state = json.loads(bot_data)
            bot_state['config'] = pair_config
            bot_state['updated_at'] = timezone.now().isoformat()

            cache.set(key, json.dumps(bot_state), timeout=86400)

            bot_instance.config = pair_config
            bot_instance.save()

            logger.info(f"Refreshed config for bot {key}")
            return True

    def refresh_all_bots_for_user(self, user_id: str) -> int:
        """Refresh all bots for user"""
        pattern = f"{self.BOT_KEY_PREFIX}{user_id}:*"
        keys = cache.keys(pattern)

        refreshed_count = 0
        for key in keys:
            bot_data = cache.get(key)
            if bot_data:
                bot_state = json.loads(bot_data)
                try:
                    bot_instance = Bot.objects.get(id=bot_state['bot_id'])
                    self.refresh_bot_config(bot_instance, bot_state['config'])
                    refreshed_count += 1
                except Bot.DoesNotExist:
                    cache.delete(key)

        logger.info(f"Refreshed {refreshed_count} bots for user {user_id}")
        return refreshed_count


# Global singleton
trading_manager = TradingManagerService()


class BotManagerService:
    @staticmethod
    def activate_bot(bot):
        """Start monitoring/executing a bot"""
        bot.last_activity = timezone.now()
        bot.save()

        if bot.bot_type == 'grid':
            execute_grid_bot.delay(bot.id)
        elif bot.bot_type == 'martingale':
            execute_martingale_bot.delay(bot.id)
        # Custom bots are event-driven via webhooks

    @staticmethod
    def deactivate_bot(bot):
        """Stop a bot and release resources"""
        bot.is_active = False
        bot.save()
        # Revoke any pending Celery tasks for this bot
        # Note: In production, store task IDs in Redis for revocation

    @staticmethod
    def log_trade(bot, exchange, symbol, amount, buy_sell, outcome, order_id=None):
        """Log all trades to database"""
        TradeLog.objects.create(
            user=bot.user,
            bot=bot,
            exchange=exchange,
            symbol=symbol,
            amount=amount,
            buy_sell=buy_sell,
            outcome=json.dumps(outcome),
            order_id=order_id
        )

        # Check alert limits
        if bot.user.webhook_alerts_used >= bot.user.subscription_plan.webhook_limit:
            # Send alert email
            from users.tasks import send_alert_email
            send_alert_email.delay(
                bot.user.email,
                "Webhook Alert Limit Reached",
                "You've reached your webhook alert limit. Upgrade to continue."
            )

        bot.user.webhook_alerts_used += 1
        bot.user.save()