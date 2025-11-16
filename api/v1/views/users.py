from django.urls import path
from users.views import UserRegistrationView, UserLoginView, UserDashboardView, ExchangeAccountCreateView, ExchangeAccountListView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='api-user-register'),
    path('login/', UserLoginView.as_view(), name='api-user-login'),
    path('dashboard/', UserDashboardView.as_view(), name='api-user-dashboard'),
    path('exchanges/', ExchangeAccountListView.as_view(), name='api-exchange-list'),
    path('exchanges/add/', ExchangeAccountCreateView.as_view(), name='api-exchange-add'),
]