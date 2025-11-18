from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Bot, TradeLog, WebhookTrigger
from .serializers import BotCreateSerializer, BotListSerializer, TradeLogSerializer
from .services import BotManagerService
from exchanges.models import ExchangeAccount
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from .models import Bot, WebhookTrigger
from .tasks import execute_custom_trade
import json

class BotCreateView(generics.CreateAPIView):
    serializer_class = BotCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        exchange_account = get_object_or_404(
            ExchangeAccount,
            id=serializer.validated_data['exchange_account_id'],
            user=self.request.user
        )

        bot = serializer.save(
            user=self.request.user,
            exchange_account=exchange_account
        )

        # Create webhook trigger for custom bots
        if bot.bot_type == 'custom':
            WebhookTrigger.objects.create(
                bot=bot,
                secret_key=self.request.user.secret_key,
                webhook_path=f"/webhooks/custom_bots/{bot.id}/"
            )


class BotListView(generics.ListAPIView):
    serializer_class = BotListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Bot.objects.filter(user=self.request.user)


class BotToggleView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Bot.objects.filter(user=self.request.user)

    def patch(self, request, *args, **kwargs):
        bot = self.get_object()
        bot.is_active = not bot.is_active
        bot.last_activity = timezone.now()
        bot.save()

        if bot.is_active:
            BotManagerService.activate_bot(bot)
        else:
            BotManagerService.deactivate_bot(bot)

        return Response({'status': 'activated' if bot.is_active else 'deactivated'})


class BotDetailView(generics.RetrieveAPIView):
    serializer_class = BotListSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Bot.objects.filter(user=self.request.user)


class TradeLogView(generics.ListAPIView):
    serializer_class = TradeLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TradeLog.objects.filter(user=self.request.user).order_by('-timestamp')




@method_decorator(csrf_exempt, name='dispatch')
class WebhookHandlerView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, bot_id):
        # Validate secret_key
        secret_key = request.data.get('secret_key')
        if not secret_key:
            return Response({"error": "Missing secret_key"}, status=403)

        try:
            webhook_trigger = WebhookTrigger.objects.get(
                bot_id=bot_id,
                secret_key=secret_key
            )
        except WebhookTrigger.DoesNotExist:
            return Response({"error": "Invalid secret_key"}, status=403)

        bot = webhook_trigger.bot

        # Validate subscription limits
        if bot.user.webhook_alerts_used >= bot.user.subscription_plan.webhook_limit:
            return Response({"error": "Webhook limit exceeded"}, status=403)

        # Parse and validate signal data
        signal_data = {
            'bot_id': bot_id,
            'buy_sell': request.data.get('buy_sell'),
            'symbol': request.data.get('symbol'),
            'exchange': request.data.get('exchange'),
            'amount': float(request.data.get('amount', 0)),
            'timestamp': request.data.get('timestamp'),
            'code': request.data.get('code', ''),
            'secret_key': secret_key
        }

        # Validate required fields
        required_fields = ['buy_sell', 'symbol', 'exchange', 'amount']
        for field in required_fields:
            if not signal_data.get(field):
                return Response({"error": f"Missing field: {field}"}, status=400)

        # Route to appropriate handler
        if bot.bot_type == 'custom':
            execute_custom_trade.delay(bot_id, signal_data)

        return Response({"status": "processed"}, status=200)