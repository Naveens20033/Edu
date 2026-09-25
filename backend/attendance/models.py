"""Attendance sessions, per-student marks, and reviewable corrections."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from academics.models import Section, Student, Subject


class AttendanceSession(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="attendance_sessions")
    section = models.ForeignKey(Section, on_delete=models.PROTECT, related_name="attendance_sessions")
    faculty = models.ForeignKey("academics.Faculty", on_delete=models.PROTECT, related_name="attendance_sessions")
    date = models.DateField(db_index=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["subject", "section", "date"], name="unique_daily_subject_section_session"),
            models.CheckConstraint(
                condition=models.Q(end_time__isnull=True) | models.Q(start_time__isnull=True) | models.Q(end_time__gt=models.F("start_time")),
                name="session_end_after_start",
            ),
        ]

    def clean(self):
        if self.subject_id and self.section_id:
            if self.subject.department_id != self.section.department_id:
                raise ValidationError({"subject": "Session subject and section must belong to the same department."})
            if self.subject.semester != self.section.semester:
                raise ValidationError({"subject": "Session subject and section must be in the same semester."})
        if self.faculty_id and self.subject_id and self.section_id:
            if not self.faculty.assignments.filter(subject_id=self.subject_id, section_id=self.section_id).exists():
                raise ValidationError({"faculty": "Faculty must have an assignment for this subject and section."})

    def __str__(self):
        return f"{self.subject.code} · {self.section} · {self.date}"


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"

    session = models.ForeignKey(AttendanceSession, on_delete=models.PROTECT, related_name="records")
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="attendance_records")
    status = models.CharField(max_length=7, choices=Status.choices)
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["student__student_id"]
        constraints = [
            models.UniqueConstraint(fields=["session", "student"], name="unique_attendance_record_per_session"),
        ]

    def clean(self):
        if self.session_id and self.student_id and self.session.section_id != self.student.section_id:
            raise ValidationError({"student": "Student must belong to the session section."})

    def __str__(self):
        return f"{self.student.student_id} · {self.session.date} · {self.status}"


class CorrectionRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    attendance_record = models.ForeignKey(AttendanceRecord, on_delete=models.PROTECT, related_name="correction_requests")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="correction_requests")
    requested_status = models.CharField(max_length=7, choices=AttendanceRecord.Status.choices)
    reason = models.TextField(max_length=1000)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING, db_index=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviewed_correction_requests",
        null=True,
        blank=True,
    )
    review_comment = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["attendance_record"],
                condition=models.Q(status="PENDING"),
                name="one_pending_correction_per_record",
            ),
        ]

    def __str__(self):
        return f"Correction #{self.pk} · {self.status}"


class AttendanceSettings(models.Model):
    """Single-row institution setting; application code uses the first row."""
    attendance_threshold = models.PositiveSmallIntegerField(
        default=75,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Minimum attendance percentage before a student is flagged.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Keep the singleton configuration row stable.
        return None

    def __str__(self):
        return f"Attendance threshold: {self.attendance_threshold}%"
