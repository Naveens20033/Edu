"""User accounts with an explicit application role."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        FACULTY = "FACULTY", "Faculty"
        STUDENT = "STUDENT", "Student"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
        # App admins need the Django admin site to manage academic records.
        self.is_staff = self.is_superuser or self.role == self.Role.ADMIN
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"is_staff", "role"}
        super().save(*args, **kwargs)

    def has_perm(self, perm, obj=None):
        if self.is_active and (self.is_superuser or self.role == self.Role.ADMIN):
            return True
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        if self.is_active and (self.is_superuser or self.role == self.Role.ADMIN):
            return True
        return super().has_module_perms(app_label)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
