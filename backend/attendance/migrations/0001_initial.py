# Initial attendance workflow migration.
import django.core.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("academics", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="AttendanceSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("attendance_threshold", models.PositiveSmallIntegerField(default=75, help_text="Minimum attendance percentage before a student is flagged.", validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="AttendanceSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(db_index=True)),
                ("start_time", models.TimeField(blank=True, null=True)),
                ("end_time", models.TimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("faculty", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="attendance_sessions", to="academics.faculty")),
                ("section", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="attendance_sessions", to="academics.section")),
                ("subject", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="attendance_sessions", to="academics.subject")),
            ],
            options={"ordering": ["-date", "-created_at"]},
        ),
        migrations.CreateModel(
            name="AttendanceRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("PRESENT", "Present"), ("ABSENT", "Absent")], max_length=7)),
                ("marked_at", models.DateTimeField(auto_now_add=True)),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="records", to="attendance.attendancesession")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="attendance_records", to="academics.student")),
            ],
            options={"ordering": ["student__student_id"]},
        ),
        migrations.CreateModel(
            name="CorrectionRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("requested_status", models.CharField(choices=[("PRESENT", "Present"), ("ABSENT", "Absent")], max_length=7)),
                ("reason", models.TextField(max_length=1000)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("APPROVED", "Approved"), ("REJECTED", "Rejected")], db_index=True, default="PENDING", max_length=8)),
                ("review_comment", models.TextField(blank=True, max_length=1000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("attendance_record", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="correction_requests", to="attendance.attendancerecord")),
                ("requested_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="correction_requests", to=settings.AUTH_USER_MODEL)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="reviewed_correction_requests", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(model_name="attendancesession", constraint=models.UniqueConstraint(fields=("subject", "section", "date"), name="unique_daily_subject_section_session")),
        migrations.AddConstraint(model_name="attendancesession", constraint=models.CheckConstraint(condition=models.Q(("end_time__isnull", True), ("start_time__isnull", True), ("end_time__gt", models.F("start_time")), _connector="OR"), name="session_end_after_start")),
        migrations.AddConstraint(model_name="attendancerecord", constraint=models.UniqueConstraint(fields=("session", "student"), name="unique_attendance_record_per_session")),
        migrations.AddConstraint(model_name="correctionrequest", constraint=models.UniqueConstraint(condition=models.Q(("status", "PENDING")), fields=("attendance_record",), name="one_pending_correction_per_record")),
    ]
