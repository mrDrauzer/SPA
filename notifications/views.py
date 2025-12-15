from datetime import timedelta
import secrets

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TelegramLinkToken


class GenerateTelegramLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Invalidate previous active tokens (optional: keep history)
        now = timezone.now()
        TelegramLinkToken.objects.filter(user=user, used_at__isnull=True, expires_at__gt=now).delete()

        # Generate new code
        code = secrets.token_urlsafe(8)
        expires_at = now + timedelta(minutes=10)

        token = TelegramLinkToken.objects.create(user=user, code=code, expires_at=expires_at)

        bot_username = request.query_params.get('bot', None)  # allow overriding via ?bot=
        # Default username is optional; client usually knows it from UI/env
        tme_link = None
        if bot_username:
            tme_link = f"https://t.me/{bot_username}?start={token.code}"

        return Response({
            'code': token.code,
            'expires_at': token.expires_at,
            'tme_link': tme_link,
        })
