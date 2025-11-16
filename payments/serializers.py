from rest_framework import serializers
from .models import PaymentMethod, SubscriptionPlan
from django.core.files.uploadedfile import InMemoryUploadedFile


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'


class PaymentCreateSerializer(serializers.ModelSerializer):
    screenshot = serializers.ImageField(required=False)

    class Meta:
        model = PaymentMethod
        fields = ['amount', 'method', 'purpose', 'transaction_hash', 'screenshot']

    def validate(self, data):
        if data['method'] == 'crypto' and not data.get('transaction_hash'):
            raise serializers.ValidationError("Transaction hash required for crypto payments")
        return data


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = '__all__'