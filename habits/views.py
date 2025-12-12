from django.http import JsonResponse
from rest_framework import viewsets, permissions, generics, status
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from .models import Habit
from .permissions import IsOwner
from .serializers import HabitSerializer


def health(request):
    return JsonResponse({"status": "ok"})


class HabitViewSet(viewsets.ModelViewSet):
    queryset = Habit.objects.all()
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        # Only own habits
        user = self.request.user
        return Habit.objects.filter(user=user)

    def perform_create(self, serializer):
        # user is set by HiddenField, but ensure ownership
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        # Защита публичных шаблонов (на всякий случай, хотя они не попадают в queryset текущего пользователя)
        if instance.is_public or getattr(getattr(instance, 'user', None), 'username', None) == 'public':
            raise PermissionDenied('Нельзя изменять публичные шаблоны.')
        serializer.save()

    def perform_destroy(self, instance):
        # Защита публичных шаблонов
        if instance.is_public or getattr(getattr(instance, 'user', None), 'username', None) == 'public':
            raise PermissionDenied('Нельзя удалять публичные шаблоны.')
        instance.delete()


class PublicHabitListView(generics.ListAPIView):
    serializer_class = HabitSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Habit.objects.filter(is_public=True)
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(Q(action__icontains=q) | Q(place__icontains=q))
        return qs


class AdoptPublicHabitView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk: int):
        # Find public template
        try:
            template = Habit.objects.select_related('linked_habit').get(id=pk, is_public=True)
        except Habit.DoesNotExist:
            return Response({'detail': 'Публичный шаблон не найден'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        def clone_habit(src: Habit, linked: Habit | None = None) -> Habit:
            return Habit.objects.create(
                user=user,
                place=src.place,
                time=src.time,
                action=src.action,
                is_pleasant=src.is_pleasant,
                linked_habit=linked,
                periodicity_days=src.periodicity_days,
                reward=src.reward if not src.is_pleasant else '',
                duration_seconds=src.duration_seconds,
                is_public=False,
            )

        created_linked = None
        if not template.is_pleasant and template.linked_habit is not None:
            # Ensure pleasant linked habit is cloned first for this user
            src_pleasant = template.linked_habit
            created_linked = clone_habit(src_pleasant, linked=None)

        created = clone_habit(template, linked=created_linked)
        data = HabitSerializer(created, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)
