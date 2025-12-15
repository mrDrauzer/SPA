from django.core.management import call_command
from django.contrib.auth import get_user_model
import pytest

from habits.models import Habit


@pytest.mark.django_db
def test_seed_public_habits_idempotent():
    # Run seeding twice
    call_command('seed_public_habits')
    first_count = Habit.objects.filter(is_public=True).count()
    assert first_count > 0

    call_command('seed_public_habits')
    second_count = Habit.objects.filter(is_public=True).count()

    assert second_count == first_count
