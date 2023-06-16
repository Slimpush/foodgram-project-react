from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(
        _('Адрес почты'),
        max_length=settings.MAX_LEN_EMAIL_PWRD_FIELD,
        unique=True,
    )
    username = models.CharField(
        _('Имя пользователя'),
        max_length=settings.MAX_LEN_USER_CHARFIELD,
        unique=True,
        validators=[MinLengthValidator
                    (4, 'Имя пользователя слишком короткое')
                    ],
    )
    first_name = models.CharField(
        _('Имя'),
        max_length=settings.MAX_LEN_USER_CHARFIELD,
        validators=[RegexValidator(
            regex='^[a-zA-Zа-яА-ЯёЁ -]*$',
            message='Поле должно содержать только буквы и пробелы.',
        )],
    )
    last_name = models.CharField(
        _('Фамилия'),
        max_length=settings.MAX_LEN_USER_CHARFIELD,
        validators=[RegexValidator(
            regex='^[a-zA-Zа-яА-ЯёЁ -]*$',
            message='Поле должно содержать только буквы и пробелы.',
        )],
    )
    password = models.CharField(
        _('Пароль'),
        max_length=settings.MAX_LEN_EMAIL_PWRD_FIELD,
    )

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ('username',)

    def __str__(self):
        return f'{self.username}: {self.email}'

    @classmethod
    def normalize_email(cls, email):
        email = email or ""
        if "@" in email:
            email_name, domain_part = email.strip().rsplit("@", 1)
            return email_name.lower() + "@" + domain_part.lower()
        return email

    @staticmethod
    def __normalize_first_last_names(self, name):
        return name.strip().title()

    def clean(self):
        self.first_name = self.__normalize_first_last_names(self.first_name)
        self.last_name = self.__normalize_first_last_names(self.last_name)
        super().clean()


class Follow(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name=_('Автор'),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="followers",
        verbose_name=_('Подписчики'),
    )
    created_at = models.DateTimeField(
        verbose_name='Дата создания подписки',
        auto_now_add=True,
        editable=False
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
