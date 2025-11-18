import uuid

from celery import shared_task
from django.utils import timezone
from .models import Bot, TradeLog
from exchanges.manager import ExchangeManager

import time
import json
import logging

logger = logging.getLogger('TorgovoN.BotTasks')



@shared_task(bind=True, max_retries=3)
def execute_bot_loop(self, bot_id: str):
    """
    Execute bot loop in Celery task.
    This runs your BybitBots.startBot() method with full threading.
    """
    try:
        from .services import BotManagerService
        from bots.services import bot_manager
        bot_instance = Bot.objects.get(id=bot_id)

        if not bot_instance.is_active:
            logger.info(f"Bot {bot_id} is not active, skipping")
            return

        # Get handler class
        exchange_name = bot_instance.exchange_account.exchange_name.lower()
        handler_class = bot_manager.HANDLERS.get(exchange_name)

        if not handler_class:
            logger.error(f"Unsupported exchange: {exchange_name} for bot {bot_id}")
            return

        # Create handler (this is your BybitBots class)
        handler = handler_class(bot_instance, bot_instance.config)

        # This starts YOUR startBot() method with all threading
        handler.startBot()

        # Keep task alive while bot is monitoring
        while handler.monitoring:
            time.sleep(30)

        logger.info(f"Bot loop completed for {bot_id}")

    except Bot.DoesNotExist:
        logger.error(f"Bot {bot_id} not found")
        return
    except Exception as e:
        logger.error(f"Error in bot loop for {bot_id}: {e}", exc_info=True)
        if self.request.retries < 3:
            raise self.retry(countdown=2 ** self.request.retries, exc=e)


@shared_task
def cleanup_inactive_bots():
    """Clean up bots inactive for 24+ hours"""
    from django.utils import timezone
    from datetime import timedelta
    from .services import BotManagerService
    from bots.services import bot_manager

    inactive_bots = Bot.objects.filter(
        is_active=True,
        last_activity__lt=timezone.now() - timedelta(hours=24)
    )

    for bot in inactive_bots:
        bot_manager.stop_bot(str(bot.user.id), bot.trading_pair, bot.exchange_account.exchange_name)


@shared_task
def refresh_all_user_bots(user_id: str):
    from bots.services import bot_manager
    """Refresh all bots for a user"""
    bot_manager.refresh_all_bots_for_user(user_id)


@shared_task(bind=True, max_retries=3)
def execute_custom_trade(self, bot_id, signal_data):

    """Execute a single trade for custom bot"""
    from .services import BotManagerService
    bot = Bot.objects.get(id=bot_id, is_active=True)
    try:
        from exchanges.manager import ExchangeManager

        exchange_manager = ExchangeManager()

        # Validate limits
        if bot.user.webhook_alerts_used >= bot.user.subscription_plan.webhook_limit:
            return {"error": "Webhook limit exceeded"}

        # Prepare order
        order_params = {
            'symbol': signal_data['symbol'],
            'side': signal_data['buy_sell'],
            'amount': signal_data['amount'],
            'type': 'market'
        }

        # Execute trade (PLACEHOLDER - DO NOT IMPLEMENT TRADE LOGIC)
        # TODO: Implement CCXT trade execution here
        # exchange = exchange_manager.get_exchange(bot.exchange_account)
        # result = exchange.create_order(**order_params)

        # Simulated outcome for demonstration
        outcome = {
            'success': True,
            'message': 'Trade executed successfully',
            'order_id': f"simulated_{uuid.uuid4()}",
            'price': 50000.0,
            'fee': 0.1
        }

        # Log trade
        BotManagerService.log_trade(
            bot=bot,
            exchange=signal_data['exchange'],
            symbol=signal_data['symbol'],
            amount=signal_data['amount'],
            buy_sell=signal_data['buy_sell'],
            outcome=outcome,
            order_id=outcome.get('order_id')
        )

        return {"status": "success", "order_id": outcome['order_id']}

    except Exception as e:
        if self.request.retries < 3:
            time.sleep(2 ** self.request.retries)
            raise self.retry(exc=e)

        # Log failure
        BotManagerService.log_trade(
            bot=bot,
            exchange=signal_data['exchange'],
            symbol=signal_data['symbol'],
            amount=signal_data['amount'],
            buy_sell=signal_data['buy_sell'],
            outcome={'success': False, 'error': str(e)}
        )
        return {"status": "failed", "error": str(e)}


@shared_task
def execute_grid_bot(bot_id):
    """Continuously monitor and execute grid bot trades"""
    try:
        from .services import BotManagerService
        bot = Bot.objects.get(id=bot_id, is_active=True, bot_type='grid')
        config = bot.config

        while bot.is_active:
            # Check last activity for timeout
            if bot.last_activity and (timezone.now() - bot.last_activity).days >= 1:
                BotManagerService.deactivate_bot(bot)
                break

            # Grid trading logic (PLACEHOLDER)
            # TODO: Implement actual grid trading strategy
            # This would involve:
            # 1. Fetching current price
            # 2. Checking grid levels
            # 3. Placing orders at each level
            # 4. Monitoring execution

            # Simulate activity
            bot.last_activity = timezone.now()
            bot.save()

            time.sleep(60)  # Check every minute

    except Bot.DoesNotExist:
        pass


@shared_task
def execute_martingale_bot(bot_id):
    """Execute martingale strategy"""
    try:
        from .services import BotManagerService
        bot = Bot.objects.get(id=bot_id, is_active=True, bot_type='martingale')
        config = bot.config

        while bot.is_active:
            if bot.last_activity and (timezone.now() - bot.last_activity).days >= 1:
                BotManagerService.deactivate_bot(bot)
                break

            # Martingale logic (PLACEHOLDER)
            # TODO: Implement actual martingale strategy
            # This would involve:
            # 1. Checking last trade outcome
            # 2. Calculating next position size (base * multiplier^level)
            # 3. Executing trade
            # 4. Updating level based on outcome

            bot.last_activity = timezone.now()
            bot.save()

            time.sleep(60)

    except Bot.DoesNotExist:
        pass


@shared_task
def cleanup_inactive_bots():
    """Clean up bots inactive for 24+ hours"""
    from django.utils import timezone
    from datetime import timedelta
    from .services import BotManagerService

    inactive_bots = Bot.objects.filter(
        is_active=True,
        last_activity__lt=timezone.now() - timedelta(hours=24)
    )

    for bot in inactive_bots:
        BotManagerService.deactivate_bot(bot)