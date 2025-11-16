from django.urls import path
from .views import WebhookHandlerView

urlpatterns = [
    path('custom_bots/<uuid:bot_id>/', WebhookHandlerView.as_view(), name='webhook-custom'),
    path('grid_bots/<uuid:bot_id>/', WebhookHandlerView.as_view(), name='webhook-grid'),
    path('martingale_bots/<uuid:bot_id>/', WebhookHandlerView.as_view(), name='webhook-martingale'),
    path('quantum_bots/<uuid:bot_id>/', WebhookHandlerView.as_view(), name='webhook-quantum'),
]