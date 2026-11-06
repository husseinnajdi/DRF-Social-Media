from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class PageProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="page_profile",
    )
    page_name = models.CharField(max_length=150)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    website = models.URLField(max_length=300, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=300, blank=True)

    # Verified badge
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="verified_pages",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "page_profiles"

    def clean(self):
        # Only page accounts have a PageProfile
        if self.user.role != self.user.Role.PAGE:
            raise ValidationError("Only accounts with role 'page' can have a PageProfile.")

    def revoke_badge(self):
        """Remove the verified badge. Log the action (with a reason) in AuditLog."""
        self.is_verified = False
        self.verified_by = None
        self.verified_at = None
        self.save(update_fields=["is_verified", "verified_by", "verified_at"])

    def __str__(self):
        return self.page_name


class VerificationRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    page = models.ForeignKey(
        PageProfile,
        on_delete=models.CASCADE,
        related_name="verification_requests",
    )
    message = models.TextField(blank=True)
    document = models.FileField(
        upload_to="verification_docs/", max_length=500, blank=True
    )  # optional proof file
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_verifications",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "verification_requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["page", "status"]),
        ]
        constraints = [
            # A page can have only one pending request at a time
            models.UniqueConstraint(
                fields=["page"],
                condition=models.Q(status="pending"),
                name="one_pending_request_per_page",
            ),
        ]

    def _close(self, status, reviewer, note):
        if self.status != self.Status.PENDING:
            raise ValidationError("Only pending requests can be reviewed.")
        now = timezone.now()
        self.status = status
        self.reviewed_by = reviewer
        self.reviewed_at = now
        self.review_note = note
        self.save()
        return now

    @transaction.atomic
    def approve(self, reviewer, note=""):
        """Approve the request and give the page its badge."""
        now = self._close(self.Status.APPROVED, reviewer, note)
        page = self.page
        page.is_verified = True
        page.verified_by = reviewer
        page.verified_at = now
        page.save(update_fields=["is_verified", "verified_by", "verified_at"])

    @transaction.atomic
    def reject(self, reviewer, note=""):
        """Reject the request (the note is shown to the page)."""
        self._close(self.Status.REJECTED, reviewer, note)

    def __str__(self):
        return f"Verification request {self.pk} ({self.status})"


class ProductService(models.Model):
    class Type(models.TextChoices):
        PRODUCT = "product", "Product"
        SERVICE = "service", "Service"

    page = models.ForeignKey(
        PageProfile,
        on_delete=models.CASCADE,
        related_name="products_services",
    )
    type = models.CharField(max_length=20, choices=Type.choices)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products_services"
        indexes = [
            models.Index(fields=["page", "is_available"]),
        ]

    def __str__(self):
        return self.name


class ProductServiceImage(models.Model):
    product_service = models.ForeignKey(
        ProductService,
        on_delete=models.CASCADE,
        related_name="images",
    )
    file = models.ImageField(upload_to="catalog/", max_length=500)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "product_service_images"
        ordering = ["order"]

    def __str__(self):
        return f"Image {self.pk} of {self.product_service_id}"