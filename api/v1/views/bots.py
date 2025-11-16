from django.urls import path
from bots.views import BotCreateView, BotListView, BotToggleView, BotDetailView, TradeLogView

urlpatterns = [
    path('', BotListView.as_view(), name='api-bot-list'),
    path('create/', BotCreateView.as_view(), name='api-bot-create'),
    path('<uuid:id>/', BotDetailView.as_view(), name='api-bot-detail'),
    path('<uuid:id>/toggle/', BotToggleView.as_view(), name='api-bot-toggle'),
    path('trades/', TradeLogView.as_view(), name='api-trade-log'),
]