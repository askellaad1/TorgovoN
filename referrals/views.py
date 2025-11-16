from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Referral, ReferralBonusConfig
from .serializers import ReferralSerializer, ReferralBonusSerializer
from .services import ReferralService
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

class ReferralListView(generics.ListAPIView):
    serializer_class = ReferralSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReferralService.get_referrals_made(self.request.user)


class AdminReferralBonusConfigView(generics.ListCreateAPIView):
    queryset = ReferralBonusConfig.objects.filter(is_active=True)
    serializer_class = ReferralBonusSerializer
    permission_classes = [IsAdminUser]


class UserReferralStatsView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        earnings = ReferralService.get_referral_earnings(request.user)
        referrals = ReferralService.get_referrals_made(request.user)

        return Response({
            'referral_code': request.user.referral_code,
            'total_earnings': earnings,
            'referrals_count': referrals.count(),
            'referrals': ReferralSerializer(referrals, many=True).data
        })