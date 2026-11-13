from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TargetType

# A report can only target these three kinds of objects
REPORTABLE_TYPES = [
    (value, label)
    for value, label in TargetType.choices
    if value in ("post", "comment", "user")
]


class Report(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        REVIEWED = "reviewed", "Reviewed"
        DISMISSED = "dismissed", "Dismissed"
        ACTION_TAKEN = "action_taken", "Action taken"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_filed",
    )
    target_type = models.CharField(max_length=30, choices=REPORTABLE_TYPES)
    target_id = models.PositiveBigIntegerField()  # polymorphic, so no foreign key
    reason = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reports_handled",
    )
    handled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),  # moderation queue
            models.Index(fields=["target_type", "target_id"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(target_type__in=["post", "comment", "user"]),
                name="report_target_is_reportable",
            ),
        ]

    def clean(self):
        # Only normal users and pages can file reports
        if self.reporter.role not in (self.reporter.Role.USER, self.reporter.Role.PAGE):
            raise ValidationError("Only users and pages can file reports.")

    def __str__(self):
        return f"Report {self.pk} on {self.target_type} {self.target_id}"
