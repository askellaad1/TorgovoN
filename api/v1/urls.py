from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Import views from their ACTUAL locations - no star imports, no namespace prefix
from users.views import (
    UserRegistrationView,
    UserLoginView,
    UserDashboardView,
    ExchangeAccountCreateView,
    ExchangeAccountListView
)
from bots.views import (
    BotCreateView,
    BotListView,
    BotToggleView,
    BotDetailView,
    BotBulkActionView,
    TradeLogView,
    WebhookHandlerView
)
from investments.views import (
    QuantumAIBotView,
    QuantumWebhookView,
    QuantumInvestmentCreateView,
    QuantumInvestmentListView,
    AdminQuantumInvestmentApproveView,
    AdminQuantumTradeResultCreateView,
    UserQuantumBalanceView,
    BinanceEMAView,
    BinanceRSIView,
    BinanceBBView
)
from payments.views import (
    PaymentCreateView,
    PaymentListView,
    SubscriptionPlanListView,
    AdminPaymentApproveView,
    AdminPlanUpdateView
)
from referrals.views import (
    ReferralListView,
    AdminReferralBonusConfigView,
    UserReferralStatsView
)

urlpatterns = [
    # Authentication
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/login/', UserLoginView.as_view(), name='user-login'),

    # Users
    path('users/', include([
        path('register/', UserRegistrationView.as_view(), name='user-register'),
        path('dashboard/', UserDashboardView.as_view(), name='user-dashboard'),
        path('exchanges/', include([
            path('', ExchangeAccountListView.as_view(), name='exchange-list'),
            path('add/', ExchangeAccountCreateView.as_view(), name='exchange-add'),
        ])),
    ])),

    # Bots
    path('bots/', include([
        path('', BotListView.as_view(), name='bot-list'),
        path('create/', BotCreateView.as_view(), name='bot-create'),
        path('bulk-action/', BotBulkActionView.as_view(), name='bot-bulk-action'),
        path('<uuid:id>/', BotDetailView.as_view(), name='bot-detail'),
        path('<uuid:id>/toggle/', BotToggleView.as_view(), name='bot-toggle'),
        path('<uuid:id>/trades/', TradeLogView.as_view(), name='bot-trades'),
    ])),

    # Webhooks (for TradingView integration)
    path('webhooks/', include([
        path('custom-bots/<uuid:bot_id>/', WebhookHandlerView.as_view(), name='webhook-custom'),
        path('quantum-ai/', QuantumWebhookView.as_view(), name='webhook-quantum'),

        # TradingView indicator updates
        path('indicators/ema/', BinanceEMAView.as_view(), name='indicator-ema'),
        path('indicators/rsi/', BinanceRSIView.as_view(), name='indicator-rsi'),
        path('indicators/bb/', BinanceBBView.as_view(), name='indicator-bb'),
    ])),

    # Quantum AI
    path('quantum-ai/', include([
        path('dashboard/<str:username>/<str:pair>/', QuantumAIBotView.as_view(), name='quantum-dashboard'),
        path('invest/', include([
            path('', QuantumInvestmentCreateView.as_view(), name='quantum-invest'),
            path('my/', QuantumInvestmentListView.as_view(), name='quantum-investments'),
            path('balance/', UserQuantumBalanceView.as_view(), name='quantum-balance'),
        ])),
    ])),

    # Investments (Admin)
    path('admin/investments/', include([
        path('<uuid:id>/approve/', AdminQuantumInvestmentApproveView.as_view(), name='admin-approve-investment'),
        path('trade-result/', AdminQuantumTradeResultCreateView.as_view(), name='admin-add-trade-result'),
    ])),

    # Payments
    path('payments/', include([
        path('', PaymentListView.as_view(), name='payment-history'),
        path('subscribe/', PaymentCreateView.as_view(), name='payment-subscribe'),
        path('plans/', SubscriptionPlanListView.as_view(), name='subscription-plans'),
    ])),

    # Payments (Admin)
    path('admin/payments/', include([
        path('<uuid:id>/approve/', AdminPaymentApproveView.as_view(), name='admin-approve-payment'),
        path('plans/<uuid:id>/', AdminPlanUpdateView.as_view(), name='admin-update-plan'),
    ])),

    # Referrals
    path('referrals/', include([
        path('', ReferralListView.as_view(), name='referral-list'),
        path('stats/', UserReferralStatsView.as_view(), name='referral-stats'),
    ])),

    # Referrals (Admin)
    path('admin/referrals/', include([
        path('bonus-config/', AdminReferralBonusConfigView.as_view(), name='admin-referral-config'),
    ])),
]