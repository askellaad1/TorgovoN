from django.urls import path
from .views import UserRegistrationView, UserLoginView, UserDashboardView, ExchangeAccountCreateView, ExchangeAccountListView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('dashboard/', UserDashboardView.as_view(), name='user-dashboard'),
    path('exchanges/', ExchangeAccountListView.as_view(), name='exchange-list'),
    path('exchanges/add/', ExchangeAccountCreateView.as_view(), name='exchange-add'),
]