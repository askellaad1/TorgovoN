from django.urls import path
from payments.views import PaymentCreateView, PaymentListView, SubscriptionPlanListView

urlpatterns = [
    path('plans/', SubscriptionPlanListView.as_view(), name='api-subscription-plans'),
    path('submit/', PaymentCreateView.as_view(), name='api-payment-submit'),
    path('history/', PaymentListView.as_view(), name='api-payment-history'),
]