from django.urls import path, include

urlpatterns = [
    path('users/', include('api.v1.views.users')),
    path('bots/', include('api.v1.views.bots')),
    path('webhooks/', include('api.v1.views.webhooks')),
    path('investments/', include('api.v1.views.investments')),
    path('payments/', include('api.v1.views.payments')),
    path('admin/', include('api.v1.views.admin')),
    path('referrals/', include('api.v1.views.referrals')),
]