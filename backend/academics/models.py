"""Departments, sections, people, subjects, and teaching assignments."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=12, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Section(models.Model):
    name = models.CharField(max_length=30)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="sections")
    academic_year = models.CharField(max_length=9, help_text="For example, 2026-2027")
    semester = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])

    class Meta:
        ordering = ["department__code", "academic_year", "semester", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "name", "academic_year", "semester"],
                name="unique_section_in_term",
            ),
        ]

    def __str__(self):
        return f"{self.department.code} {self.name} · Sem {self.semester} · {self.academic_year}"


class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="student_profile")
    student_id = models.CharField(max_length=24, unique=True)
    name = models.CharField(max_length=160)
    email = models.EmailField(unique=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="students")
    section = models.ForeignKey(Section, on_delete=models.PROTECT, related_name="students")

    class Meta:
        ordering = ["student_id"]

    def clean(self):
        if self.section_id and self.department_id and self.section.department_id != self.department_id:
            raise ValidationError({"department": "Student department must match the section department."})

    def __str__(self):
        return f"{self.student_id} — {self.name}"


class Faculty(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="faculty_profile")
    employee_id = models.CharField(max_length=24, unique=True)
    name = models.CharField(max_length=160)
    email = models.EmailField(unique=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="faculty")

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "faculty"

    def __str__(self):
        return f"{self.employee_id} — {self.name}"


class Subject(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=160)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="subjects")
    semester = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class FacultyAssignment(models.Model):
    """Authorizes a faculty member to teach a subject for one section."""
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT, related_name="assignments")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="assignments")
    section = models.ForeignKey(Section, on_delete=models.PROTECT, related_name="faculty_assignments")

    class Meta:
        ordering = ["section", "subject", "faculty"]
        constraints = [
            models.UniqueConstraint(fields=["faculty", "subject", "section"], name="unique_faculty_subject_section"),
        ]

    def clean(self):
        errors = {}
        if self.subject_id and self.section_id:
            if self.subject.department_id != self.section.department_id:
                errors["subject"] = "Subject and section must belong to the same department."
            if self.subject.semester != self.section.semester:
                errors["subject"] = "Subject and section must be in the same semester."
        if self.faculty_id and self.faculty.user.role != "FACULTY":
            errors["faculty"] = "The linked account must have the faculty role."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.faculty} · {self.subject} · {self.section}"
