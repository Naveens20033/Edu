from django.contrib import admin

from .models import AttendanceRecord, AttendanceSession, AttendanceSettings, CorrectionRequest


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    fields = ("student", "status", "marked_at")
    readonly_fields = ("student", "status", "marked_at")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ("date", "subject", "section", "faculty")
    list_filter = ("date", "subject__department", "section")
    search_fields = ("subject__code", "section__name", "faculty__name")
    inlines = (AttendanceRecordInline,)
    readonly_fields = ("subject", "section", "faculty", "date", "start_time", "end_time", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "status", "marked_at")
    list_filter = ("status", "session__date", "session__subject")
    search_fields = ("student__student_id", "student__name")
    readonly_fields = ("session", "student", "status", "marked_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CorrectionRequest)
class CorrectionRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "attendance_record", "requested_by", "requested_status", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("attendance_record__student__student_id", "requested_by__username")
    readonly_fields = (
        "attendance_record", "requested_by", "requested_status", "reason", "status",
        "reviewed_by", "review_comment", "created_at", "reviewed_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AttendanceSettings)
class AttendanceSettingsAdmin(admin.ModelAdmin):
    list_display = ("attendance_threshold", "updated_at")
    readonly_fields = ("updated_at",)
