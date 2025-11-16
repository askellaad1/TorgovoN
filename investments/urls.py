from django.urls import path
from .views import (
    QuantumInvestmentCreateView,
    QuantumInvestmentListView,
    UserQuantumBalanceView,
    QuantumAIBotView,
    QuantumWebhookView,
    BinanceEMAView,
    BinanceRSIView,
    BinanceBBView,
)

urlpatterns = [
    # Existing investment endpoints
    path('quantum/submit/', QuantumInvestmentCreateView.as_view(), name='quantum-invest'),
    path('quantum/history/', QuantumInvestmentListView.as_view(), name='quantum-history'),
    path('quantum/balance/', UserQuantumBalanceView.as_view(), name='quantum-balance'),

    # Quantum AI bot endpoints
    path('quantum/bot/<str:username>/<str:pair>/', QuantumAIBotView.as_view(), name='quantum-bot-control'),
    path('quantum/webhook/', QuantumWebhookView.as_view(), name='quantum-webhook'),

    # Indicator update endpoints (your original pattern)
    path('quantum/indicators/ema/', BinanceEMAView.as_view(), name='quantum-ema'),
    path('quantum/indicators/rsi/', BinanceRSIView.as_view(), name='quantum-rsi'),
    path('quantum/indicators/bb/', BinanceBBView.as_view(), name='quantum-bb'),
]