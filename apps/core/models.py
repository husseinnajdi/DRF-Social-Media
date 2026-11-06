from django.db import models


class TargetType(models.TextChoices):
    """Shared by reports, audit_logs and notifications (polymorphic targets)."""

    POST = "post", "Post"
    COMMENT = "comment", "Comment"
    USER = "user", "User"
    VERIFICATION_REQUEST = "verification_request", "Verification request"
    REPORT = "report", "Report"