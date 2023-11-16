from django.contrib.auth.models import AbstractUser
from django.db import models


class MyUser(AbstractUser):
    """Модель для пользователей foodgram"""
    username = models.SlugField(
        verbose_name='Уникальный юзернейм',
        max_length=150,
        unique=True,
    )
    first_name = models.CharField(
        verbose_name='Имя', max_length=150
    )
    last_name = models.CharField(
        verbose_name='Фамилия', max_length=150
    )
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        max_length=254,
        unique=True,
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

        def __str__(self):
            """Строковое представление модели"""

            return self.username
