from django.urls import path
from payments.views import AdminPaymentApproveView, AdminPlanUpdateView
from investments.views import AdminQuantumInvestmentApproveView, AdminQuantumTradeResultCreateView

urlpatterns = [
    path('payments/<uuid:id>/approve/', AdminPaymentApproveView.as_view(), name='api-admin-payment-approve'),
    path('plans/<uuid:id>/update/', AdminPlanUpdateView.as_view(), name='api-admin-plan-update'),
    path('investments/quantum/<uuid:id>/approve/', AdminQuantumInvestmentApproveView.as_view(), name='api-admin-quantum-approve'),
    path('investments/quantum/trade-result/', AdminQuantumTradeResultCreateView.as_view(), name='api-admin-quantum-trade'),
]