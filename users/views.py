from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login
from .serializers import UserRegistrationSerializer, UserDashboardSerializer, ExchangeAccountSerializer
from .models import User, ExchangeAccount
from core.utils import generate_webhook_path, generate_json_template
from referrals.services import ReferralService
import uuid


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate webhook URLs and templates
        webhook_path = generate_webhook_path('custom', user.id)
        json_template = generate_json_template(user.id, user.secret_key)

        response_data = {
            'user_id': user.id,
            'webhook_url': f"https://{request.get_host()}{webhook_path}",
            'json_template': json_template,
            'referral_code': user.referral_code
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class UserLoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, email=email, password=password)

        if user:
            login(request, user)
            return Response({
                'access_token': str(user.auth_token),
                'refresh_token': str(user.refresh_token)
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class UserDashboardView(generics.RetrieveAPIView):
    serializer_class = UserDashboardSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ExchangeAccountCreateView(generics.CreateAPIView):
    serializer_class = ExchangeAccountSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExchangeAccountListView(generics.ListAPIView):
    serializer_class = ExchangeAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ExchangeAccount.objects.filter(user=self.request.user, is_active=True)