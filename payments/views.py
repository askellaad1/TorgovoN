from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import PaymentMethod, SubscriptionPlan
from .serializers import PaymentCreateSerializer, PaymentSerializer, SubscriptionPlanSerializer
from django.utils import timezone
from rest_framework.permissions import IsAdminUser

class PaymentCreateView(generics.CreateAPIView):
    serializer_class = PaymentCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)


class SubscriptionPlanListView(generics.ListAPIView):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated]


class AdminPaymentApproveView(generics.UpdateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        payment = self.get_object()
        payment.status = 'approved'
        payment.approved_at = timezone.now()
        payment.save()

        # Apply subscription benefits
        if payment.purpose == "Bot Subscription":
            payment.user.subscription_plan = SubscriptionPlan.objects.get(plan_type='pro')
            payment.user.subscription_end_date = timezone.now() + timedelta(days=30)
            payment.user.save()

        return Response({"status": "approved"})


class AdminPlanUpdateView(generics.UpdateAPIView):
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'
    queryset = SubscriptionPlan.objects.all()