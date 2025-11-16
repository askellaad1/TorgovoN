from django.urls import path
from referrals.views import ReferralListView, UserReferralStatsView

urlpatterns = [
    path('', ReferralListView.as_view(), name='api-referral-list'),
    path('stats/', UserReferralStatsView.as_view(), name='api-referral-stats'),
]