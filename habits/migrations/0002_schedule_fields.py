from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('habits', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='habit',
            name='last_notified_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Последнее уведомление'),
        ),
        migrations.AddField(
            model_name='habit',
            name='next_run_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Следующий запуск'),
        ),
    ]
