"""Shared attendance aggregation helpers used by dashboards and reports."""
from django.db.models import Count, F, Q
from django.utils import timezone

from academics.models import Department, Faculty, FacultyAssignment, Student, Subject
from .models import AttendanceRecord, AttendanceSession, AttendanceSettings


def attendance_threshold():
    setting = AttendanceSettings.objects.first()
    return setting.attendance_threshold if setting else 75


def percentage(present, total):
    return round((present * 100.0 / total), 1) if total else None


def student_subject_summary(student):
    groups = AttendanceRecord.objects.filter(student=student).values(
        "session__subject_id", "session__subject__code", "session__subject__name"
    ).annotate(
        total=Count("id"),
        present=Count("id", filter=Q(status=AttendanceRecord.Status.PRESENT)),
    ).order_by("session__subject__code")
    threshold = attendance_threshold()
    return [
        {
            "subject_id": row["session__subject_id"],
            "subject_code": row["session__subject__code"],
            "subject_name": row["session__subject__name"],
            "total_classes": row["total"],
            "present_count": row["present"],
            "absent_count": row["total"] - row["present"],
            "percentage": percentage(row["present"], row["total"]),
            "below_threshold": (row["present"] * 100.0 / row["total"]) < threshold,
        }
        for row in groups
    ]


def student_overall_summary(student):
    result = AttendanceRecord.objects.filter(student=student).aggregate(
        total=Count("id"),
        present=Count("id", filter=Q(status=AttendanceRecord.Status.PRESENT)),
    )
    return {
        "total_classes": result["total"],
        "present_count": result["present"],
        "absent_count": result["total"] - result["present"],
        "percentage": percentage(result["present"], result["total"]),
    }


def low_attendance_by_assignment(pairs, limit=100):
    """Return low students separately for each assigned subject and section."""
    condition = Q(pk__in=[])
    for subject_id, section_id in pairs:
        condition |= Q(session__subject_id=subject_id, session__section_id=section_id)
    groups = AttendanceRecord.objects.filter(condition).values(
        "student__student_id", "student__name", "student__section__name",
        "session__subject__code", "session__subject__name", "session__section_id",
    ).annotate(
        total=Count("id"),
        present=Count("id", filter=Q(status=AttendanceRecord.Status.PRESENT)),
    ).order_by("session__subject__code", "student__student_id")
    threshold = attendance_threshold()
    rows = []
    for row in groups:
        if row["present"] * 100.0 / row["total"] < threshold:
            rows.append({
                "student_id": row["student__student_id"],
                "student_name": row["student__name"],
                "section_name": row["student__section__name"],
                "subject_code": row["session__subject__code"],
                "subject_name": row["session__subject__name"],
                "total_classes": row["total"],
                "present_count": row["present"],
                "percentage": percentage(row["present"], row["total"]),
            })
            if len(rows) >= limit:
                break
    return rows


def admin_dashboard():
    today = timezone.localdate()
    today_records = AttendanceRecord.objects.filter(session__date=today).aggregate(
        total=Count("id"),
        present=Count("id", filter=Q(status=AttendanceRecord.Status.PRESENT)),
    )
    recent_dates = list(
        AttendanceRecord.objects.values(date=F("session__date")).annotate(
            total=Count("id"), present=Count("id", filter=Q(status=AttendanceRecord.Status.PRESENT))
        ).order_by("-date")[:7]
    )
    return {
        "role": "ADMIN",
        "threshold": attendance_threshold(),
        "total_students": Student.objects.count(),
        "total_faculty": Faculty.objects.count(),
        "total_departments": Department.objects.count(),
        "total_subjects": Subject.objects.count(),
        "today": {
            "sessions": AttendanceSession.objects.filter(date=today).count(),
            "total_records": today_records["total"],
            "present_records": today_records["present"],
            "percentage": percentage(today_records["present"], today_records["total"]),
        },
        "low_attendance_count": len({
            row["student_id"] for row in low_attendance_by_assignment(
                FacultyAssignment.objects.values_list("subject_id", "section_id"), limit=10000
            )
        }),
        "attendance_trend": [
            {"date": row["date"].isoformat(), "percentage": percentage(row["present"], row["total"])}
            for row in reversed(recent_dates)
        ],
        "recent_sessions": list(AttendanceSession.objects.select_related("subject", "section", "faculty").order_by("-date", "-created_at").values(
            "id", "date", "subject__code", "subject__name", "section__name", "faculty__name"
        )[:8]),
    }


def faculty_dashboard(user):
    today = timezone.localdate()
    try:
        faculty = user.faculty_profile
    except Faculty.DoesNotExist:
        return {
            "role": "FACULTY", "assignments": 0, "sections": 0, "today_sessions": 0,
            "low_attendance_count": 0, "low_attendance": [], "assigned_classes": [],
        }
    assignments = FacultyAssignment.objects.filter(faculty=faculty).select_related("subject", "section")
    pairs = list(assignments.values_list("subject_id", "section_id"))
    today_sessions = AttendanceSession.objects.filter(faculty=faculty, date=today).count()
    low_rows = low_attendance_by_assignment(pairs, limit=100)
    return {
        "role": "FACULTY",
        "assignments": assignments.count(),
        "sections": assignments.values("section_id").distinct().count(),
        "today_sessions": today_sessions,
        "low_attendance_count": len({row["student_id"] for row in low_rows}),
        "low_attendance": low_rows[:10],
        "assigned_classes": [
            {"assignment_id": item.pk, "subject_code": item.subject.code, "subject_name": item.subject.name,
             "section_id": item.section_id, "section_name": item.section.name}
            for item in assignments
        ],
    }


def student_dashboard(user):
    try:
        student = user.student_profile
    except Student.DoesNotExist:
        return {"role": "STUDENT", "summary": student_overall_summary(None), "subjects": [], "recent_attendance": []}
    recent = AttendanceSession.objects.filter(records__student=student).select_related("subject", "section").order_by("-date")[:8]
    recent_rows = []
    for session in recent:
        record = session.records.filter(student=student).first()
        if record:
            recent_rows.append({"date": session.date.isoformat(), "subject_code": session.subject.code,
                                "subject_name": session.subject.name, "status": record.status})
    subjects = student_subject_summary(student)
    return {
        "role": "STUDENT",
        "threshold": attendance_threshold(),
        "summary": student_overall_summary(student),
        "subjects": subjects,
        "low_attendance_subjects": [row for row in subjects if row["below_threshold"]],
        "recent_attendance": recent_rows,
    }
