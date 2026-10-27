from django.db import models
from django.conf import settings
from django.utils import timezone

class PostQuerySet(models.QuerySet):
    def alive(self):
        """post that have not been soft_deleted"""
        return self.filter(is_deleted=False)

class Post(models.Model):

    class Visibility(models.TextChoices):
        PUBLIC= "public", "Public"
        FOLLOWERS="followers", "Followers"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts"
    )

    content= models.TextField()

    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PUBLIC
    )

    is_deleted=models.BooleanField(default=False)

    deleted_by=models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,blank=True,
        on_delete=models.SET_NULL,
        related_name="deleted_posts"
    )

    deleted_reason=models.TextField(blank=True)

    deleted_at=models.DateTimeField(auto_now_add=True)

    created_at=models.DateTimeField(auto_now_add=True)

    updated_at=models.DateTimeField(auto_now=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        db_table = "posts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["author","created_at"]),
            models.Index(fields=["is_deleted","-created_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.author.role=="page":
            self.visibility=self.visibility.PUBLIC
        super().save(*args, **kwargs)

    def soft_delete(self,by,reason=""):
        self.deleted_by=by
        self.is_deleted=True
        self.deleted_reason=reason
        self.deleted_at=timezone.now()
        self.save(
            update_fields=[
                "is_deleted",
                "deleted_by",
                "deleted_reason",
                "deleted_at",
                "updated_at",
            ]
        )

    def __str__(self):
        return f"Post by {self.author} , with content:  {self.content}"
