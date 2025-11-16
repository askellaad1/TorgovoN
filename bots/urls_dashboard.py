from django.urls import path
from .views import BotCreateView, BotListView, BotToggleView, BotDetailView, TradeLogView

urlpatterns = [
    path('bots/', BotListView.as_view(), name='bot-list'),
    path('bots/create/', BotCreateView.as_view(), name='bot-create'),
    path('bots/<uuid:id>/', BotDetailView.as_view(), name='bot-detail'),
    path('bots/<uuid:id>/toggle/', BotToggleView.as_view(), name='bot-toggle'),
    path('trades/', TradeLogView.as_view(), name='trade-log'),
]