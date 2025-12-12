from rest_framework import serializers

from .models import Habit


class HabitSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Habit
        fields = (
            'id', 'user', 'place', 'time', 'action',
            'is_pleasant', 'linked_habit', 'periodicity_days', 'reward', 'duration_seconds',
            'is_public', 'created_at', 'updated_at',
        )
        # Защищаем публичность от изменения через обычный CRUD
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_public')

    def validate(self, attrs):
        # Cross-field validations replicating model.clean rules plus ownership checks
        is_pleasant = attrs.get('is_pleasant', getattr(self.instance, 'is_pleasant', False))
        reward = attrs.get('reward', getattr(self.instance, 'reward', ''))
        linked_habit = attrs.get('linked_habit', getattr(self.instance, 'linked_habit', None))

        # reward and linked_habit cannot be set together
        if reward and linked_habit is not None:
            raise serializers.ValidationError('Нельзя одновременно указывать вознаграждение и связанную привычку.')

        # pleasant habit cannot have reward or linked habit
        if is_pleasant:
            if reward:
                raise serializers.ValidationError('У приятной привычки не должно быть вознаграждения.')
            if linked_habit is not None:
                raise serializers.ValidationError('У приятной привычки не должно быть связанной привычки.')

        # linked habit must be pleasant and belong to same user
        if linked_habit is not None:
            if not linked_habit.is_pleasant:
                raise serializers.ValidationError('Связанной может быть только приятная привычка.')
            # ownership: linked habit must belong to same user
            request = self.context.get('request')
            user = request.user if request else getattr(self.instance, 'user', None)
            if user and linked_habit.user_id != user.id:
                raise serializers.ValidationError('Связанная привычка должна принадлежать тому же пользователю.')

        return attrs
