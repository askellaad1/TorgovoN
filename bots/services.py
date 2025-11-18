import json
import logging
from typing import Dict, Any, Optional
from django.core.cache import cache
from django.utils import timezone
from .models import Bot, TradeLog

logger = logging.getLogger('TorgovoN.BotServices')


class BotManagerService:
    """
    Unified bot manager service that handles both Redis state management
    and database operations. Avoids circular imports by lazy loading.
    """

    # Use string references to avoid importing handlers at module level
    HANDLERS = {
        'binance': None,
        'bybit': 'bots.bot_handlers.bybit_bot.BybitBotHandler',
        'mexc': None,
        'kraken_spot': None,
    }

    BOT_KEY_PREFIX = "bot:active:"
    LOCK_PREFIX = "lock:bot:"

    @staticmethod
    def _get_bot_redis_key(user_id: str, pair_symbol: str, exchange: str) -> str:
        """Generate Redis key for bot state"""
        return f"{BotManagerService.BOT_KEY_PREFIX}{user_id}:{pair_symbol}:{exchange}"

    @staticmethod
    def get_bot(user_id: str, pair_symbol: str, exchange: str) -> Optional[Dict[str, Any]]:
        """Alias for get_bot_state to maintain compatibility"""
        return BotManagerService.get_bot_state(user_id, pair_symbol, exchange)

    @staticmethod
    def _load_handler_class(exchange_name: str):
        """Dynamically load handler class to avoid circular imports"""
        handler_path = BotManagerService.HANDLERS.get(exchange_name.lower())
        if not handler_path:
            return None

        # Lazy import
        module_path, class_name = handler_path.rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)

    @staticmethod
    def get_bot_state(user_id: str, pair_symbol: str, exchange: str) -> Optional[Dict[str, Any]]:
        """Retrieve bot state from Redis"""
        key = BotManagerService._get_bot_redis_key(user_id, pair_symbol, exchange)
        bot_data = cache.get(key)
        return json.loads(bot_data) if bot_data else None

    @staticmethod
    def create_bot(bot_instance: Bot, pair_config: Dict[str, Any]) -> str:
        """
        Create bot in Redis and start Celery task
        Import tasks here to avoid circular dependency
        """
        from bots.tasks import execute_bot_loop  # LOCAL IMPORT

        user_id = str(bot_instance.user.id)
        pair_symbol = pair_config['pair_symbol']
        exchange = bot_instance.exchange_account.exchange_name

        key = BotManagerService._get_bot_redis_key(user_id, pair_symbol, exchange)
        lock_key = f"{BotManagerService.LOCK_PREFIX}{key}"

        with cache.lock(lock_key, timeout=10):
            if cache.get(key):
                logger.warning(f"Bot {key} already exists in Redis")
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

            cache.set(key, json.dumps(bot_state), timeout=86400)  # 24 hours

            # Update database
            bot_instance.is_active = True
            bot_instance.save()

            # Start Celery task
            execute_bot_loop.delay(str(bot_instance.id))

            logger.info(f"Created and started bot {key}")
            return key

    @staticmethod
    def start_bot(user_id: str, pair_symbol: str, exchange: str) -> bool:
        """Start existing bot"""
        from bots.tasks import execute_bot_loop  # LOCAL IMPORT

        key = BotManagerService._get_bot_redis_key(user_id, pair_symbol, exchange)
        lock_key = f"{BotManagerService.LOCK_PREFIX}{key}"

        with cache.lock(lock_key, timeout=10):
            bot_data = cache.get(key)
            if not bot_data:
                logger.warning(f"Bot {key} not found in Redis")
                return False

            bot_state = json.loads(bot_data)
            if bot_state['is_active']:
                logger.info(f"Bot {key} already running")
                return True

            bot_state['is_active'] = True
            cache.set(key, json.dumps(bot_state), timeout=86400)

            execute_bot_loop.delay(bot_state['bot_id'])

            logger.info(f"Restarted bot {key}")
            return True

    @staticmethod
    def stop_bot(user_id: str, pair_symbol: str, exchange: str) -> bool:
        """Stop bot by removing from Redis"""
        key = BotManagerService._get_bot_redis_key(user_id, pair_symbol, exchange)
        lock_key = f"{BotManagerService.LOCK_PREFIX}{key}"

        with cache.lock(lock_key, timeout=10):
            bot_data = cache.get(key)
            if bot_data:
                cache.delete(key)

                # Update database
                try:
                    bot_instance = Bot.objects.get(id=json.loads(bot_data)['bot_id'])
                    bot_instance.is_active = False
                    bot_instance.save()
                except Bot.DoesNotExist:
                    pass

                logger.info(f"Stopped and removed bot {key}")
                return True
            return False

    @staticmethod
    def refresh_bot_config(bot_instance: Bot, pair_config: Dict[str, Any]) -> bool:
        """Refresh bot configuration in Redis and DB"""
        user_id = str(bot_instance.user.id)
        pair_symbol = pair_config['pair_symbol']
        exchange = bot_instance.exchange_account.exchange_name

        key = BotManagerService._get_bot_redis_key(user_id, pair_symbol, exchange)
        lock_key = f"{BotManagerService.LOCK_PREFIX}{key}"

        with cache.lock(lock_key, timeout=10):
            bot_data = cache.get(key)
            if not bot_data:
                return False

            bot_state = json.loads(bot_data)
            bot_state['config'] = pair_config
            bot_state['updated_at'] = timezone.now().isoformat()

            cache.set(key, json.dumps(bot_state), timeout=86400)

            # Update database
            bot_instance.config = pair_config
            bot_instance.save()

            logger.info(f"Refreshed config for bot {key}")
            return True

    @staticmethod
    def refresh_all_bots_for_user(user_id: str) -> int:
        """Refresh all bots for a specific user"""
        pattern = f"{BotManagerService.BOT_KEY_PREFIX}{user_id}:*"
        keys = cache.keys(pattern)

        refreshed_count = 0
        for key in keys:
            bot_data = cache.get(key)
            if bot_data:
                bot_state = json.loads(bot_data)
                try:
                    bot_instance = Bot.objects.get(id=bot_state['bot_id'])
                    BotManagerService.refresh_bot_config(bot_instance, bot_state['config'])
                    refreshed_count += 1
                except Bot.DoesNotExist:
                    cache.delete(key)

        logger.info(f"Refreshed {refreshed_count} bots for user {user_id}")
        return refreshed_count

    @staticmethod
    def activate_bot(bot):
        """Activate a bot and start its execution"""
        bot.last_activity = timezone.now()
        bot.save()

        # Route to appropriate task based on bot type
        if bot.bot_type == 'grid':
            from bots.tasks import execute_grid_bot  # LOCAL IMPORT
            execute_grid_bot.delay(bot.id)
        elif bot.bot_type == 'martingale':
            from bots.tasks import execute_martingale_bot  # LOCAL IMPORT
            execute_martingale_bot.delay(bot.id)
        elif bot.bot_type == 'custom':
            # Custom bots are event-driven via webhooks, no persistent task needed
            logger.info(f"Custom bot {bot.id} activated for webhook triggers")
        else:
            logger.warning(f"Unknown bot type: {bot.bot_type}")

    @staticmethod
    def deactivate_bot(bot):
        """Deactivate a bot and stop its execution"""
        bot.is_active = False
        bot.save()

        # Stop Redis-based bots if applicable
        if hasattr(bot, 'exchange_account') and bot.exchange_account:
            user_id = str(bot.user.id)
            pair_symbol = bot.config.get('pair_symbol', '')
            exchange = bot.exchange_account.exchange_name

            if user_id and pair_symbol and exchange:
                BotManagerService.stop_bot(user_id, pair_symbol, exchange)

        logger.info(f"Deactivated bot {bot.id}")

    @staticmethod
    def log_trade(bot, exchange, symbol, amount, buy_sell, outcome, order_id=None):
        """
        Log trade execution to database
        Import tasks here to avoid circular dependency
        """
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

        # Check webhook alert limits
        if hasattr(bot.user, 'subscription_plan'):
            if bot.user.webhook_alerts_used >= bot.user.subscription_plan.webhook_limit:
                from users.tasks import send_alert_email  # LOCAL IMPORT
                send_alert_email.delay(
                    bot.user.email,
                    "Webhook Alert Limit Reached",
                    "You've reached your webhook alert limit. Upgrade to continue."
                )

        bot.user.webhook_alerts_used += 1
        bot.user.save()


# Global instance for convenience
bot_manager = BotManagerService()