from django.contrib import admin

from .models import Department, Faculty, FacultyAssignment, Section, Student, Subject


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "academic_year", "semester")
    list_filter = ("department", "academic_year", "semester")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "name", "department", "section")
    list_filter = ("department", "section")
    search_fields = ("student_id", "name", "email")


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "name", "department")
    list_filter = ("department",)
    search_fields = ("employee_id", "name", "email")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "department", "semester")
    list_filter = ("department", "semester")
    search_fields = ("code", "name")


@admin.register(FacultyAssignment)
class FacultyAssignmentAdmin(admin.ModelAdmin):
    list_display = ("faculty", "subject", "section")
    list_filter = ("subject__department", "section")
    search_fields = ("faculty__name", "subject__code", "section__name")
