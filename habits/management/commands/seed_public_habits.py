from __future__ import annotations

from datetime import time
from typing import Iterable

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from habits.models import Habit


def t(hhmm: str) -> time:
    hh, mm = hhmm.split(":", 1)
    return time(int(hh), int(mm))


class Command(BaseCommand):
    help = "Seed public habit templates (idempotent)."

    PUBLIC_USERNAME = "public"

    def handle(self, *args, **options):
        User = get_user_model()
        public_user, _ = User.objects.get_or_create(
            username=self.PUBLIC_USERNAME,
            defaults={"is_active": False, "is_staff": False, "is_superuser": False},
        )
        if hasattr(public_user, "set_unusable_password"):
            public_user.set_unusable_password()
            public_user.save(update_fields=["password"])  # ok even if empty before

        created, existed = 0, 0

        # 1) Здоровье и физическая активность
        created += self._ensure_templates(public_user, [
            {
                "action": "Выпить один стакан воды (вода)",
                "time": t("07:00"),
                "place": "Кухня",
                "duration_seconds": 60,
            },
            {
                "action": "Стоять в планке 30–60 секунд",
                "time": t("07:30"),
                "place": "Спальня/Коврик",
                "duration_seconds": 60,
            },
            {
                "action": "Сделать гимнастику для глаз",
                "time": t("14:00"),
                "place": "Рабочий стол",
                "duration_seconds": 120,
            },
            {
                "action": "Выйти на улицу и подышать свежим воздухом",
                "time": t("13:00"),  # из вариантов берём обеденный
                "place": "Улица/Парк",
                "duration_seconds": 120,
            },
        ], existed_counter_ref=lambda n: self._bump(lambda: existed, n))

        # 2) Обучение и саморазвитие
        created += self._ensure_templates(public_user, [
            {
                "action": "Прочитать одну страницу книги",
                "time": t("22:30"),
                "place": "Кровать",
                "duration_seconds": 120,
            },
            {
                "action": "Выучить одно новое английское слово",
                "time": t("08:00"),
                "place": "Кухня",
                "duration_seconds": 60,
            },
            {
                "action": "Просмотреть один PR или кусок кода",
                "time": t("09:00"),
                "place": "Рабочее место",
                "duration_seconds": 120,
            },
        ], existed_counter_ref=lambda n: self._bump(lambda: existed, n))

        # 3) Осознанность и ментальное здоровье
        created += self._ensure_templates(public_user, [
            {
                "action": "Записать одну вещь, за которую я благодарен сегодня",
                "time": t("19:30"),
                "place": "Дневник/Заметки в телефоне",
                "duration_seconds": 60,
            },
            {
                "action": "Сидеть в тишине и следить за дыханием",
                "time": t("18:30"),
                "place": "Кресло",
                "duration_seconds": 120,
            },
            {
                "action": "Отложить телефон экраном вниз",
                "time": t("22:00"),
                "place": "Тумбочка в спальне",
                "duration_seconds": 10,
            },
        ], existed_counter_ref=lambda n: self._bump(lambda: existed, n))

        # 4) Порядок и быт
        created += self._ensure_templates(public_user, [
            {
                "action": "Аккуратно заправить постель",
                "time": t("07:05"),
                "place": "Спальня",
                "duration_seconds": 60,
            },
            {
                "action": "Помыть за собой чашку",
                "time": t("16:00"),
                "place": "Кухня",
                "duration_seconds": 60,
            },
            {
                "action": "Приготовить одежду на завтра",
                "time": t("21:00"),
                "place": "Гардероб",
                "duration_seconds": 120,
            },
        ], existed_counter_ref=lambda n: self._bump(lambda: existed, n))

        # Пример связки полезная ↔ приятная
        pleasant = self._get_or_create_template(
            public_user,
            action="Посмотреть смешное видео (котики/трейлер)",
            time_obj=t("20:00"),
            place="YouTube/Телефон",
            duration_seconds=120,
            is_pleasant=True,
        )
        if pleasant[1]:  # created
            created += 1
        else:
            existed += 1

        linked_useful = self._get_or_create_template(
            public_user,
            action="Выучить 5 горячих клавиш в PyCharm",
            time_obj=t("10:00"),
            place="Рабочий стол",
            duration_seconds=120,
            is_pleasant=False,
            linked_habit=pleasant[0],
        )
        if linked_useful[1]:
            created += 1
        else:
            existed += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seed finished. created={created}, existed={existed}"
        ))

    # Helpers
    def _ensure_templates(self, user, items: Iterable[dict], existed_counter_ref) -> int:
        created_count = 0
        for item in items:
            obj, was_created = Habit.objects.get_or_create(
                user=user,
                action=item["action"],
                time=item["time"],
                place=item["place"],
                defaults=dict(
                    is_pleasant=False,
                    periodicity_days=1,
                    reward="",
                    duration_seconds=item["duration_seconds"],
                    is_public=True,
                ),
            )
            if was_created:
                created_count += 1
            else:
                existed_counter_ref(1)
        return created_count

    def _get_or_create_template(
        self,
        user,
        *,
        action: str,
        time_obj: time,
        place: str,
        duration_seconds: int,
        is_pleasant: bool,
        linked_habit: Habit | None = None,
    ):
        obj, was_created = Habit.objects.get_or_create(
            user=user,
            action=action,
            time=time_obj,
            place=place,
            defaults=dict(
                is_pleasant=is_pleasant,
                linked_habit=linked_habit if not is_pleasant else None,
                periodicity_days=1,
                reward="" if is_pleasant else "",
                duration_seconds=duration_seconds,
                is_public=True,
            ),
        )
        return obj, was_created

    @staticmethod
    def _bump(getter, n: int):
        # no-op placeholder to keep simple counters in place without global state
        return
