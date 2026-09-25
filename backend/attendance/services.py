"""Atomic business operations for recording attendance."""
from django.db import IntegrityError, transaction
from academics.models import Student
from .models import AttendanceRecord, AttendanceSession


@transaction.atomic
def create_attendance_session(*, assignment, attendance_date, start_time, end_time, records):
    """Create a class session and its complete roster in one transaction."""
    try:
        session = AttendanceSession.objects.create(
            subject=assignment.subject,
            section=assignment.section,
            faculty=assignment.faculty,
            date=attendance_date,
            start_time=start_time,
            end_time=end_time,
        )
        students = {
            student.pk: student
            for student in Student.objects.filter(
                section=assignment.section,
                pk__in=[record["student_id"] for record in records],
            )
        }
        AttendanceRecord.objects.bulk_create([
            AttendanceRecord(
                session=session,
                student=students[record["student_id"]],
                status=record["status"],
            )
            for record in records
        ])
    except IntegrityError as exc:
        # A concurrent request can pass the earlier duplicate pre-check.
        raise AttendanceSessionConflict from exc
    return session


class AttendanceSessionConflict(Exception):
    """A concurrent submission created the same daily session first."""
