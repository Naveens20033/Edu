"""Reusable role checks for API views and viewsets."""
from rest_framework.permissions import BasePermission

from .models import User


class HasRole(BasePermission):
    """Base permission for a view that declares ``required_roles``."""
    message = "Your account role is not allowed to perform this action."

    def has_permission(self, request, view):
        required_roles = getattr(view, "required_roles", ())
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and (user.is_superuser or user.role in required_roles)
        )


class IsAdminRole(HasRole):
    required_roles = (User.Role.ADMIN,)


class IsFacultyRole(HasRole):
    required_roles = (User.Role.FACULTY,)


class IsStudentRole(HasRole):
    required_roles = (User.Role.STUDENT,)


class IsAdminOrFacultyRole(HasRole):
    required_roles = (User.Role.ADMIN, User.Role.FACULTY)
