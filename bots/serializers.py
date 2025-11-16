from rest_framework import serializers
from .models import Bot, TradeLog, WebhookTrigger
from exchanges.models import ExchangeAccount


class BotCreateSerializer(serializers.ModelSerializer):
    exchange_account_id = serializers.UUIDField()

    class Meta:
        model = Bot
        fields = ['name', 'bot_type', 'exchange_account_id', 'trading_pair', 'config']

    def validate(self, data):
        bot_type = data['bot_type']
        config = data['config']

        # Validate config based on bot type
        if bot_type == 'grid':
            required_fields = ['percentage_difference', 'amount_per_level', 'starting_amount']
        elif bot_type == 'martingale':
            required_fields = ['multiplier', 'max_levels', 'base_amount']
        elif bot_type == 'custom':
            required_fields = []
        else:
            raise serializers.ValidationError("Invalid bot type")

        for field in required_fields:
            if field not in config:
                raise serializers.ValidationError(f"Missing required config field: {field}")

        return data


class BotListSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Bot
        fields = ['id', 'name', 'bot_type', 'trading_pair', 'is_active', 'status', 'created_at']

    def get_status(self, obj):
        return 'active' if obj.is_active else 'inactive'


class TradeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeLog
        fields = '__all__'


class WebhookTriggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookTrigger
        fields = ['secret_key', 'webhook_path']