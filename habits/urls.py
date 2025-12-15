from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'habits'

router = DefaultRouter()
router.register(r'habits', views.HabitViewSet, basename='habit')

urlpatterns = [
    path('health/', views.health, name='health'),
    # Put specific public routes BEFORE router include to avoid capture by `habits/{lookup}`
    path('habits/public/', views.PublicHabitListView.as_view(), name='habits-public'),
    path('habits/public/<int:pk>/adopt/', views.AdoptPublicHabitView.as_view(), name='habits-public-adopt'),
    path('', include(router.urls)),
]
