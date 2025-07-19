from django.db import models
from django.contrib.auth import get_user_model

from .constants import MAX_LENGTH_TAGS, MAX_NAME_LENGTH

User = get_user_model()

class Tags(models.Model):
    name = models.CharField(
        unique=True,
        max_length=MAX_LENGTH_TAGS,
    )
    slug = models.SlugField(
        unique=True,
        max_length=MAX_LENGTH_TAGS,
        null=True,
        allow_unicode=False,

   )

class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="follower",
        verbose_name="Пользователь"
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followers",
        verbose_name="Подписчик"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["following", "user"],
                name="unique_follow"
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F("following")),
                name="user_cannot_follow_himself"
            ),
        ]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписчики"

    def __str__(self):
        return f"Подписчики пользователя: {self.user}"
