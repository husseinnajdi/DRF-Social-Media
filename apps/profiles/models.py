from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from posts.models import Post


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    default_post_visibility = models.CharField(
        max_length=20,
        choices=Post.Visibility.choices,
        default=Post.Visibility.PUBLIC,
    )

    class Meta:
        db_table = "profiles"

    def clean(self):
        # Only normal users have a Profile (pages use PageProfile)
        if self.user.role != self.user.Role.USER:
            raise ValidationError("Only accounts with role 'user' can have a Profile.")

    def __str__(self):
        return f"Profile of {self.user_id}"