from django.conf import settings
from django.db import models

from apps.core.models import TargetType


class NotificationQuerySet(models.QuerySet):
    def unread(self):
        return self.filter(is_read=False)


class Notification(models.Model):
    class Type(models.TextChoices):
        LIKE = "like", "Like"
        COMMENT = "comment", "Comment"
        REPLY = "reply", "Reply"
        FOLLOW = "follow", "Follow"
        NEW_POST = "new_post", "New post"
        VERIFICATION_APPROVED = "verification_approved", "Verification approved"
        VERIFICATION_REJECTED = "verification_rejected", "Verification rejected"
        REPORT_UPDATE = "report_update", "Report update"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notifications_triggered",
    )
    type = models.CharField(max_length=30, choices=Type.choices)
    target_type = models.CharField(
        max_length=30, choices=TargetType.choices, null=True, blank=True
    )
    target_id = models.PositiveBigIntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = NotificationQuerySet.as_manager()

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "created_at"]),
        ]

    def __str__(self):
        return f"{self.type} for {self.recipient_id}"
