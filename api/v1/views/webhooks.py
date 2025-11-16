from django.urls import path
from bots.views import WebhookHandlerView

urlpatterns = [
    path('custom_bots/<uuid:bot_id>/', WebhookHandlerView.as_view(), name='api-webhook-custom'),
]