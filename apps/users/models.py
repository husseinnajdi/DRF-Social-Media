from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, username, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not username:
            raise ValueError("Username is required")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)  # hashes the password
        user.save(using=self._db)
        return user

    def create_user(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.USER)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, username, password, **extra_fields)

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_email_verified", True)
        return self._create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        SUPERVISOR = "supervisor", "Supervisor"
        USER = "user", "User"
        PAGE = "page", "Page"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        BANNED = "banned", "Banned"

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    # `password` comes from AbstractBaseUser (hashed, max_length=128)

    # Set by the server at signup, never accepted from the client
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    status_reason = models.TextField(blank=True)
    status_changed_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="status_changes_made",
    )
    status_changed_at = models.DateTimeField(null=True, blank=True)

    is_email_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)  # access to Django admin

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"  # log in with email
    REQUIRED_FIELDS = ["username"]  # asked by createsuperuser

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["status"]),
        ]

    @property
    def is_active(self):
        # Django checks this at login; derived from status so there is one source of truth
        return self.status == self.Status.ACTIVE

    def __str__(self):
        return self.username