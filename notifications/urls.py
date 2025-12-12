from django.urls import path

from .views import GenerateTelegramLinkView


app_name = 'notifications'

urlpatterns = [
    path('telegram/link/', GenerateTelegramLinkView.as_view(), name='telegram-link'),
]
