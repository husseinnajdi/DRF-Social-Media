from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class FollowQuerySet(models.QuerySet):
    def following_ids(self, user):
        """IDs of everyone this user follows (used to build the feed)."""
        return self.filter(follower=user).values_list("following_id", flat=True)

    def follower_ids(self, user):
        """IDs of everyone who follows this user."""
        return self.filter(following=user).values_list("follower_id", flat=True)


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following",
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = FollowQuerySet.as_manager()

    class Meta:
        db_table = "follows"
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"],
                name="unique_follow",
            ),
            # Can't follow yourself
            models.CheckConstraint(
                condition=~models.Q(follower=models.F("following")),
                name="no_self_follow",
            ),
        ]

    def clean(self):
        if self.follower.role == "page":
            raise ValidationError("Page accounts cannot follow other accounts.")

    def __str__(self):
        return f"{self.follower_id} follows {self.following_id}"


class Block(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocking",  # user.blocking -> Block rows where user is the blocker
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_by",  # user.blocked_by -> Block rows where user is blocked
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "blocks"
        constraints = [
            models.UniqueConstraint(
                fields=["blocker", "blocked"],
                name="unique_block",
            ),
            models.CheckConstraint(
                condition=~models.Q(blocker=models.F("blocked")),
                name="no_self_block",
            ),
        ]

    def __str__(self):
        return f"{self.blocker_id} blocks {self.blocked_id}"
