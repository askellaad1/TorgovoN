from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Import views one by one to handle missing imports gracefully
try:
    from users.views import (
        UserRegistrationView,
        UserLoginView,
        UserDashboardView,
        ExchangeAccountCreateView,
        ExchangeAccountListView
    )
except ImportError:
    UserRegistrationView = None
    UserLoginView = None
    UserDashboardView = None
    ExchangeAccountCreateView = None
    ExchangeAccountListView = None

try:
    from bots.views import (
        BotCreateView,
        BotListView,
        BotToggleView,
        BotDetailView,
        BotBulkActionView,
        TradeLogView,
        WebhookHandlerView
    )
except ImportError:
    BotCreateView = None
    BotListView = None
    BotToggleView = None
    BotDetailView = None
    BotBulkActionView = None
    TradeLogView = None
    WebhookHandlerView = None

urlpatterns = [
    # Authentication
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Only add user paths if views are available
if UserLoginView:
    urlpatterns.append(path('auth/login/', UserLoginView.as_view(), name='user-login'))

if UserRegistrationView or UserDashboardView:
    user_patterns = []
    if UserRegistrationView:
        user_patterns.append(path('register/', UserRegistrationView.as_view(), name='user-register'))
    if UserDashboardView:
        user_patterns.append(path('dashboard/', UserDashboardView.as_view(), name='user-dashboard'))
    if user_patterns:
        urlpatterns.append(path('users/', include(user_patterns)))

# Only add bot paths if views are available
if BotListView or BotCreateView:
    bot_patterns = []
    if BotListView:
        bot_patterns.append(path('', BotListView.as_view(), name='bot-list'))
    if BotCreateView:
        bot_patterns.append(path('create/', BotCreateView.as_view(), name='bot-create'))
    if BotBulkActionView:
        bot_patterns.append(path('bulk-action/', BotBulkActionView.as_view(), name='bot-bulk-action'))
    if bot_patterns:
        urlpatterns.append(path('bots/', include(bot_patterns)))