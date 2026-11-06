from django.conf import settings
from django.db import models

from core.choices import TargetType


class AuditLog(models.Model):
    """Append-only record of every admin / supervisor action."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,  # never lose the record of who did something
        related_name="audit_logs",
    )
    action = models.CharField(max_length=100)  # e.g. delete_post, suspend_user, approve_badge
    target_type = models.CharField(
        max_length=30, choices=TargetType.choices, null=True, blank=True
    )
    target_id = models.PositiveBigIntegerField(null=True, blank=True)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor", "created_at"]),
            models.Index(fields=["target_type", "target_id"]),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError("Audit log entries cannot be modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Audit log entries cannot be deleted.")

    def __str__(self):
        return f"{self.actor_id}: {self.action}"


class DailyStat(models.Model):
    """One row per day, filled by a Celery Beat job so dashboards read fast."""

    date = models.DateField(unique=True)
    new_users = models.PositiveIntegerField(default=0)
    new_pages = models.PositiveIntegerField(default=0)
    new_posts = models.PositiveIntegerField(default=0)
    reports_filed = models.PositiveIntegerField(default=0)
    reports_resolved = models.PositiveIntegerField(default=0)
    pending_verifications = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "daily_stats"
        ordering = ["-date"]

    def __str__(self):
        return f"Stats for {self.date}"