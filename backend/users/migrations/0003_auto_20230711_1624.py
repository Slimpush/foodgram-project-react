# Generated by Django 3.2.3 on 2023-07-11 09:24

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import api.validators


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20230628_1426'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='follow',
            name='created_at',
        ),
        migrations.AlterField(
            model_name='follow',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='follower', to=settings.AUTH_USER_MODEL, verbose_name='Подписчик'),
        ),
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=models.CharField(max_length=150, verbose_name='Имя'),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_name',
            field=models.CharField(max_length=150, verbose_name='Фамилия'),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=150, unique=True, validators=[api.validators.validate_username], verbose_name='Имя пользователя'),
        ),
    ]
