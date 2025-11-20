from rest_framework import serializers
from .models import User
from exchanges.models import ExchangeAccount
from core.utils import encrypt_data


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    referral_code = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['email', 'phone', 'password', 'first_name', 'last_name', 'referral_code']

    def validate(self, data):
        if not data.get('email') and not data.get('phone'):
            raise serializers.ValidationError("Either email or phone is required")
        return data

    def create(self, validated_data):
        referral_code = validated_data.pop('referral_code', None)
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data, password=password)

        # Handle referral if code provided
        if referral_code:
            from referrals.services import ReferralService
            ReferralService.process_referral(user, referral_code)

        return user


class UserDashboardSerializer(serializers.ModelSerializer):
    bots = serializers.SerializerMethodField()
    exchanges = serializers.SerializerMethodField()
    subscription = serializers.SerializerMethodField()
    referral = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'first_name', 'last_name',
                  'quantum_balance', 'bots', 'exchanges', 'subscription', 'referral']

    def get_bots(self, obj):
        from bots.serializers import BotListSerializer
        return BotListSerializer(obj.bots.all(), many=True).data

    def get_exchanges(self, obj):
        from .serializers import ExchangeAccountSerializer
        return ExchangeAccountSerializer(obj.exchange_accounts.filter(is_active=True), many=True).data

    def get_subscription(self, obj):
        if obj.subscription_plan:
            return {
                'plan': obj.subscription_plan.name,
                'end_date': obj.subscription_end_date,
                'webhook_limit': obj.subscription_plan.webhook_limit,
                'webhooks_used': obj.webhook_alerts_used
            }
        return None

    def get_referral(self, obj):
        from referrals.services import ReferralService
        earnings = ReferralService.get_referral_earnings(obj)
        return {
            'code': obj.referral_code,
            'earnings': earnings,
            'referred_count': obj.referrals_made.count()
        }


class ExchangeAccountSerializer(serializers.ModelSerializer):
    masked_api_key = serializers.ReadOnlyField()

    class Meta:
        model = ExchangeAccount
        fields = ['id', 'exchange_name', 'masked_api_key', 'is_active', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        # Encrypt secrets before saving
        validated_data['api_key_encrypted'] = encrypt_data(validated_data['api_key_encrypted'])
        validated_data['api_secret_encrypted'] = encrypt_data(validated_data['api_secret_encrypted'])
        return super().create(validated_data)