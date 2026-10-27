from django.db import models
from django.conf import settings

from apps import comments


class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes',
    )

    post = models.ForeignKey(
        "posts.Post",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='likes',
    )

    comment = models.ForeignKey(
        "comments.Comment",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='likes',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table= "likes"
        constraints = [
            models.UniqueConstraint(
                fields=['user','post'],
                condition=models.Q(post__isnull=False),
                name="unique_user_post_like"
            ),
            models.UniqueConstraint(
                fields=['user','comment'],
                condition=models.Q(comment__isnull=False),
                name="unique_user_comment_like"
            ),

            models.CheckConstraint(
                condition=models.Q(post__isnull=False,comment__isnull=True)
                | models.Q(post__isnull=True,comment__isnull=False),
                name="like_hase_exactly_one_target",
            ),
        ]

    @property
    def target(self):
        """the liked object, whichever kind it is"""
        return self.post if self.post_id else self.comment

    def __str__(self):
        return f" User {self.user_id} likes{self.target}"