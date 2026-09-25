from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class ApplicationUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Attendance role", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Attendance role", {"fields": ("role", "email")}),)
    list_display = (*UserAdmin.list_display, "role")
