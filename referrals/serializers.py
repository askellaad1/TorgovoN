from rest_framework import serializers
from .models import Referral, ReferralBonusConfig


class ReferralSerializer(serializers.ModelSerializer):
    referrer_email = serializers.ReadOnlyField(source='referrer.email')
    referred_email = serializers.ReadOnlyField(source='referred.email')

    class Meta:
        model = Referral
        fields = '__all__'


class ReferralBonusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralBonusConfig
        fields = '__all__'