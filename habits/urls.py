from django.urls import path
from . import views

app_name = 'habits'

urlpatterns = [
    path('health/', views.health, name='health'),
]
