from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q, F


class User(AbstractUser):
    """Модель для пользователей foodgram"""
    username = models.CharField(
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
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

        def __str__(self):
            """Строковое представление модели"""

            return self.username


class Follow(models.Model):
    """ Модель для создания подписок на автора"""
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        related_name='follower',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        related_name='follow',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('author', 'user'),
                name='unique_follow'
            ),
            models.CheckConstraint(
                check=~Q(user=F('author')),
                name='no_self_follow'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.author}'
