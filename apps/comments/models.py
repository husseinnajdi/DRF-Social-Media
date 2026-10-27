from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
class CommentQuerySet(models.QuerySet):
    def alive(self):
        """comments that have not been soft_deleted"""
        return self.filter(is_deleted=False)

    def top_level(self):
        """comments that are not replies"""
        return self.filter(parent__isnull=True)


class Comment(models.Model):
    post=models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        related_name="comments",
    )

    author=models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    parent=models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
        blank=True,
    )

    content=models.TextField()

    is_deleted=models.BooleanField(default=False)

    deleted_by=models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="deleted_comments",
    )

    created_at=models.DateTimeField(auto_now_add=True)

    objects = CommentQuerySet.as_manager()

    class Meta:
        db_table = "comments"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["post", "created_at"]),
        ]

    def clean(self):
        if self.parent_id and self.parent.post_id != self.post_id:
            raise ValidationError(
                "A reply must be on the same post as its parent comment."
            )
    def soft_delete(self,by):
        self.is_deleted = True
        self.deleted_by=by
        self.save(update_fields=["is_deleted","deleted_by"])

    @property
    def is_reply(self):
        return self.parent_id is not None

    def __str__(self):
        return f"Comment {self.content} by {self.author}"