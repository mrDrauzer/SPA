from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from notifications.models import TelegramProfile

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    ChangePasswordSerializer,
)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        return Response({'detail': 'Пароль изменён.'}, status=status.HTTP_200_OK)


class TelegramStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = getattr(user, 'telegram', None)
        if profile and isinstance(profile, TelegramProfile):
            return Response({
                'linked': True,
                'chat_id': profile.chat_id,
                'username': profile.username,
                'linked_at': profile.linked_at,
            })
        return Response({'linked': False})
