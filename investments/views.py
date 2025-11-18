from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from .models import QuantumInvestment, QuantumPool, QuantumTradeResult
from .serializers import QuantumInvestmentSerializer, QuantumInvestmentStatusSerializer, QuantumTradeResultSerializer
from .services import QuantumDistributionService
from django.utils import timezone
import json
import logging
from asgiref.sync import sync_to_async
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone
from django.core.cache import cache

from users.models import User
from bots.models import Bot
from bots.services import bot_manager
from bots.serializers import BotListSerializer

logger = logging.getLogger('Torgovo.QuantumAI')


# Your original indicator views adapted
@method_decorator(csrf_exempt, name='dispatch')
class BinanceEMAView(APIView):
    """Update EMA for Quantum AI bot"""
    permission_classes = []

    async def post(self, request):
        try:
            data = json.loads(request.body)
            if "EMA200" not in data:
                return JsonResponse({"error": "EMA200 not provided"}, status=400)

            user_name = data["username"]
            pair_symbol = data["pair"]
            exchange = data.get("exchange", "binance")
            ema_value = data["EMA200"]

            user = await sync_to_async(User.objects.get)(username=user_name)

            # Update bot state in Redis
            key = bot_manager._get_bot_redis_key(str(user.id), pair_symbol, exchange)
            bot_data = cache.get(key)

            if bot_data:
                bot_state = json.loads(bot_data)
                bot_state['config']['EMA'] = ema_value
                bot_state['updated_at'] = timezone.now().isoformat()
                cache.set(key, json.dumps(bot_state), timeout=86400)

                logger.info(f"Updated EMA for {pair_symbol}: {ema_value}")

            return JsonResponse({"status": "success", "EMA": ema_value})

        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except Exception as e:
            logger.error(f"EMA update error: {str(e)}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class BinanceRSIView(APIView):
    """Update RSI for Quantum AI bot"""
    permission_classes = []

    async def post(self, request):
        try:
            data = json.loads(request.body)
            required_fields = ['RSI', 'PrevRSI', 'color', 'prev_color']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({"error": f"Missing {field}"}, status=400)

            user_name = data["username"]
            pair_symbol = data["pair"]
            exchange = data["exchange"]

            user = await sync_to_async(User.objects.get)(username=user_name)

            # Update bot state
            key = bot_manager._get_bot_redis_key(str(user.id), pair_symbol, exchange)
            bot_data = cache.get(key)

            if bot_data:
                bot_state = json.loads(bot_data)
                bot_state['config'].update({
                    'RSI': data['RSI'],
                    'PrevRSI': data['PrevRSI'],
                    'RSI_color': data['color'],
                    'RSI_prev_color': data['prev_color'],
                })
                cache.set(key, json.dumps(bot_state), timeout=86400)

            return JsonResponse({"status": "success", "RSI": data['RSI']})

        except Exception as e:
            logger.error(f"RSI update error: {str(e)}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class BinanceBBView(APIView):
    """Update Bollinger Bands for Quantum AI bot"""
    permission_classes = []

    async def post(self, request):
        try:
            data = json.loads(request.body)
            if "BB" not in data:
                return JsonResponse({"error": "BB not provided"}, status=400)

            user_name = data["username"]
            pair_symbol = data["pair"]
            exchange = data["exchange"]
            bb_value = data["BB"]

            user = await sync_to_async(User.objects.get)(username=user_name)

            # Update bot state
            key = bot_manager._get_bot_redis_key(str(user.id), pair_symbol, exchange)
            bot_data = cache.get(key)

            if bot_data:
                bot_state = json.loads(bot_data)
                bot_state['config']['BB'] = bb_value
                cache.set(key, json.dumps(bot_state), timeout=86400)

            return JsonResponse({"status": "success", "BB": bb_value})

        except Exception as e:
            logger.error(f"BB update error: {str(e)}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)


# Quantum AI Bot Control View
@method_decorator(csrf_exempt, name='dispatch')
class QuantumAIBotView(APIView):
    """Quantum AI bot dashboard and control"""
    permission_classes = [IsAuthenticated]

    async def get(self, request, username, pair):
        """Display Quantum AI bot dashboard"""
        try:
            user = await sync_to_async(User.objects.get)(username=username)

            if user.id != request.user.id and not request.user.is_superuser:
                return JsonResponse({"error": "Not authorized"}, status=403)

            exchange = await sync_to_async(lambda: user.exchange_accounts.filter(is_active=True).first())()
            if not exchange:
                return JsonResponse({"error": "No exchange configured"}, status=400)

            bot_data = await sync_to_async(bot_manager.get_bot)(
                str(user.id), pair, exchange.exchange_name
            )

            bot_instance = await sync_to_async(lambda: Bot.objects.filter(
                user=user, bot_type='quantum', trading_pair=pair
            ).first())()

            context = {
                'pair': pair,
                'username': username,
                'exchange': exchange.exchange_name,
                'bot_running': bool(bot_data and bot_data['is_active']),
                'quantum_balance': user.quantum_balance,
                'subscription_tier': user.subscription_plan.name if user.subscription_plan else 'None',
                'bot_instance': BotListSerializer(bot_instance).data if bot_instance else None,
                'current_price': bot_data.get('current_price', 0) if bot_data else 0,
                'EMA': bot_data.get('EMA', 0) if bot_data else 0,
                'RSI': bot_data.get('RSI', 0) if bot_data else 0,
            }

            return render(request, 'quantum_ai_dashboard.html', context)

        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except Exception as e:
            logger.error(f"Quantum AI dashboard error: {str(e)}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)

    async def post(self, request, username, pair):
        """Control Quantum AI bot (start/stop)"""
        try:
            data = json.loads(request.body)
            action = data.get('action')

            user = await sync_to_async(User.objects.get)(username=username)

            if user.id != request.user.id and not request.user.is_superuser:
                return JsonResponse({"error": "Not authorized"}, status=403)

            exchange = await sync_to_async(lambda: user.exchange_accounts.filter(is_active=True).first())()
            if not exchange:
                return JsonResponse({"error": "No exchange configured"}, status=400)

            quantum_config = {
                'pair_symbol': pair,
                'futures': True,
                'Amount_Type': 'dollar',
                'quantity': 10,  # Default $10 per trade
                'favor_levels': 5,
                'against_levels': 5,
                'favor_level_qty': 5,
                'against_level_qty': 5,
                'favor_level_difference': 2,
                'against_level_difference': 2,
                'Order_Type': 'market',
                'RSI_Lower': 30,
                'RSI_Upper': 70,
                'EMA_RSI_Entry': 'both',
                'EMA_BB_Entry': 'both',
                'BB_RSI_Entry': 'both',
                'RSI_Entry': 'both',
                'BB_Entry': 'both',
                'EMA_BB_RSI_Entry': 'both',
                'SL_Exit': 'both',
                'Stop_Loss': -50,
                'Take_Profit': 100,
                'TP_BUY1': True,
            }

            if action == 'start':
                if user.quantum_balance <= 0:
                    return JsonResponse({"error": "Insufficient Quantum AI balance"}, status=400)

                bot_instance, created = await sync_to_async(Bot.objects.get_or_create)(
                    user=user,
                    bot_type='quantum',
                    trading_pair=pair,
                    defaults={
                        'name': f'Quantum AI {pair}',
                        'exchange_account': exchange,
                        'config': quantum_config,
                    }
                )

                if created:
                    bot_instance.config = quantum_config
                    await sync_to_async(bot_instance.save)()

                bot_key = await sync_to_async(bot_manager.create_bot)(bot_instance, quantum_config)

                return JsonResponse({
                    "success": True,
                    "message": f"Quantum AI bot started for {pair}",
                    "bot_key": bot_key
                })

            elif action == 'stop':
                stopped = await sync_to_async(bot_manager.stop_bot)(
                    str(user.id), pair, exchange.exchange_name
                )
                return JsonResponse({
                    "success": stopped,
                    "message": f"Bot stopped for {pair}" if stopped else "Bot not found"
                })

            return JsonResponse({"error": "Invalid action"}, status=400)

        except Exception as e:
            logger.error(f"Quantum AI control error: {str(e)}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)


# Webhook for Quantum AI signals
@method_decorator(csrf_exempt, name='dispatch')
class QuantumWebhookView(APIView):
    """Webhook for Quantum AI signals from TradingView"""
    permission_classes = []

    async def post(self, request):
        try:
            data = json.loads(request.body)

            secret_key = data.get('secret_key')
            bot_id = data.get('bot_id')

            if not secret_key or not bot_id:
                return JsonResponse({"error": "Missing credentials"}, status=400)

            bot = await sync_to_async(Bot.objects.get)(id=bot_id)

            if bot.user.secret_key != secret_key:
                return JsonResponse({"error": "Invalid secret_key"}, status=403)

            if not bot.is_active:
                return JsonResponse({"error": "Bot is inactive"}, status=400)

            # Queue execution
            signal_data = {
                'bot_id': bot_id,
                'buy_sell': data['buy_sell'],
                'symbol': data['symbol'],
                'exchange': data['exchange'],
                'amount': float(data['amount']),
                'timestamp': data.get('timestamp'),
                'strategy': 'quantum_ai',
                'secret_key': secret_key,
            }

            from bots.tasks import execute_custom_trade
            execute_custom_trade.delay(bot_id, signal_data)

            return JsonResponse({"status": "processed"}, status=200)

        except Bot.DoesNotExist:
            return JsonResponse({"error": "Bot not found"}, status=404)
        except Exception as e:
            logger.error(f"Quantum webhook error: {str(e)}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)


class QuantumInvestmentCreateView(generics.CreateAPIView):
    serializer_class = QuantumInvestmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Use platform wallet addresses from settings
        wallet_addresses = {
            'erc20': '0xPlatformERC20WalletAddress',
            'aptos': '0xPlatformAptosWalletAddress',
            'trc20': 'TPlatformTRONWalletAddress',
        }

        serializer.save(
            user=self.request.user,
            wallet_address=wallet_addresses[serializer.validated_data['blockchain']]
        )


class QuantumInvestmentListView(generics.ListAPIView):
    serializer_class = QuantumInvestmentStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return QuantumInvestment.objects.filter(user=self.request.user)


class AdminQuantumInvestmentApproveView(generics.UpdateAPIView):
    serializer_class = QuantumInvestmentStatusSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        investment = self.get_object()
        investment.status = 'approved'
        investment.approved_at = timezone.now()
        investment.save()

        # Update user's quantum balance
        investment.user.quantum_balance += investment.amount
        investment.user.save()

        # Update pool
        pool, created = QuantumPool.objects.get_or_create(id=1)
        pool.total_invested += investment.amount
        pool.save()

        # Activate quantum bot access
        from payments.models import SubscriptionPlan
        investment.user.subscription_plan = SubscriptionPlan.objects.get(plan_type='quantum')
        investment.user.save()

        return Response({"status": "approved"})


class AdminQuantumTradeResultCreateView(generics.CreateAPIView):
    serializer_class = QuantumTradeResultSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        trade_result = serializer.save(applied=False)
        # Trigger distribution
        QuantumDistributionService.distribute_profit_loss(trade_result)


class UserQuantumBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'quantum_balance': request.user.quantum_balance,
            'total_invested': QuantumPool.objects.get(id=1).total_invested
        })