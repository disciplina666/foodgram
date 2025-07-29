from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxLengthValidator, RegexValidator
from django.db import models

from .constants import MAX_LENGTH_EMAIL, MAX_LENGTH_NAME, MAX_PASSWORD_LENGTH
from .validators import validate_username


class User(AbstractUser):
    """Модель пользователя."""

    email = models.EmailField(
        unique=True,
        max_length=MAX_LENGTH_EMAIL,
        validators=[MaxLengthValidator(MAX_LENGTH_EMAIL)],
        verbose_name="Электронная почта",
        help_text="Введите свой электронный адрес",
    )

    username = models.CharField(
        max_length=MAX_LENGTH_NAME,
        unique=True,
        help_text=(
            "Обязательное поле. 150 символов или меньше. "
            "Только буквы, цифры и @/./+/-/_ символы."
        ),
        validators=[
            validate_username,
            RegexValidator(
                regex=r"^[\w.@+-]+$",
                message=(
                    "Имя пользователя может содержать только "
                    "буквы, цифры и символы @/./+/-/_"
                ),
            ),
        ],
        error_messages={
            "unique": "Пользователь с таким именем уже существует.",
        },
        verbose_name="Имя пользователя",
    )

    first_name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        validators=[MaxLengthValidator(MAX_LENGTH_NAME)],
        verbose_name="Имя",
    )

    last_name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        validators=[MaxLengthValidator(MAX_LENGTH_NAME)],
        verbose_name="Фамилия",
    )

    avatar = models.ImageField(
        upload_to="avatars",
        blank=True,
        verbose_name="Аватар",
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Модель подписок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "following"], name="unique_follow"
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F("following")),
                name="user_cannot_follow_himself",
            ),
        ]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f"{self.user} подписан на {self.following}"
