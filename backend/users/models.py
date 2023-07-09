from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from api.validators import validate_username


class User(AbstractUser):
    email = models.EmailField(
        verbose_name='Адрес почты',
        max_length=settings.MAX_LEN_EMAIL_PWRD_FIELD,
        unique=True,
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=settings.MAX_LEN_USER_CHARFIELD,
        unique=True,
        validators=[validate_username],
    )

    first_name = models.CharField(
        verbose_name='Имя',
        max_length=settings.MAX_LEN_USER_CHARFIELD,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=settings.MAX_LEN_USER_CHARFIELD,

    )
    password = models.CharField(
        verbose_name='Пароль',
        max_length=settings.MAX_LEN_EMAIL_PWRD_FIELD,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return f'{self.username}: {self.email}'


class Follow(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='Нельзя повторно подписаться',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='Нельзя подписываться на самого себя'
            ),
        ]

    def __str__(self) -> str:
        return f'{self.user} Подписка на -> {self.author}'
