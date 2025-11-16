from rest_framework import serializers
from .models import QuantumInvestment, QuantumTradeResult


class QuantumInvestmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuantumInvestment
        fields = ['amount', 'blockchain', 'transaction_hash', 'screenshot']

    def validate(self, data):
        if data['amount'] <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return data


class QuantumInvestmentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuantumInvestment
        fields = '__all__'


class QuantumTradeResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuantumTradeResult
        fields = '__all__'