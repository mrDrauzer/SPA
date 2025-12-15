from django.urls import path

from .views import RegisterView, MeView, ChangePasswordView, TelegramStatusView

app_name = 'users'

urlpatterns = [
    path('users/register/', RegisterView.as_view(), name='register'),
    path('users/me/', MeView.as_view(), name='me'),
    path('users/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('users/telegram/', TelegramStatusView.as_view(), name='telegram-status'),
]
