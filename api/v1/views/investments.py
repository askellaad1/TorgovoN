from django.urls import path
from investments.views import QuantumInvestmentCreateView, QuantumInvestmentListView, UserQuantumBalanceView

urlpatterns = [
    path('quantum/submit/', QuantumInvestmentCreateView.as_view(), name='api-quantum-invest'),
    path('quantum/history/', QuantumInvestmentListView.as_view(), name='api-quantum-history'),
    path('quantum/balance/', UserQuantumBalanceView.as_view(), name='api-quantum-balance'),
]