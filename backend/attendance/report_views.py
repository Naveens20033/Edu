"""Role-scoped dashboard and low-attendance reporting endpoints."""
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import HasRole
from academics.models import Faculty, FacultyAssignment, Student
from .models import AttendanceSettings
from .reporting import (
    admin_dashboard,
    attendance_threshold,
    low_attendance_by_assignment,
    faculty_dashboard,
    student_dashboard,
    student_subject_summary,
)


class DashboardView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        if user.is_superuser or user.role == User.Role.ADMIN:
            data = admin_dashboard()
        elif user.role == User.Role.FACULTY:
            data = faculty_dashboard(user)
        elif user.role == User.Role.STUDENT:
            data = student_dashboard(user)
        else:
            return Response({"detail": "Unsupported account role."}, status=status.HTTP_403_FORBIDDEN)
        return Response(data)


class LowAttendanceView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        if user.is_superuser or user.role == User.Role.ADMIN:
            pairs = list(FacultyAssignment.objects.values_list("subject_id", "section_id"))
            rows = low_attendance_by_assignment(pairs, limit=10000)
        elif user.role == User.Role.FACULTY:
            try:
                faculty = user.faculty_profile
            except Faculty.DoesNotExist:
                rows = []
            else:
                pairs = list(faculty.assignments.values_list("subject_id", "section_id"))
                rows = low_attendance_by_assignment(pairs, limit=10000)
        elif user.role == User.Role.STUDENT:
            try:
                student = user.student_profile
            except Student.DoesNotExist:
                rows = []
            else:
                rows = [
                    {"subject_code": item["subject_code"], "subject_name": item["subject_name"],
                     "total_classes": item["total_classes"], "present_count": item["present_count"],
                     "percentage": item["percentage"]}
                    for item in student_subject_summary(student) if item["below_threshold"]
                ]
        else:
            return Response({"detail": "Unsupported account role."}, status=status.HTTP_403_FORBIDDEN)
        page = request.query_params.get("page", "1")
        if not page.isdigit() or int(page) < 1:
            return Response({"page": ["Must be a positive integer."]}, status=status.HTTP_400_BAD_REQUEST)
        page_number = int(page)
        page_size = 50
        start = (page_number - 1) * page_size
        return Response({
            "threshold": attendance_threshold(), "count": len(rows),
            "next": page_number + 1 if start + page_size < len(rows) else None,
            "previous": page_number - 1 if page_number > 1 else None,
            "results": rows[start:start + page_size],
        })


class ThresholdSerializer(serializers.Serializer):
    attendance_threshold = serializers.IntegerField(min_value=1, max_value=100)


class AttendanceThresholdView(APIView):
    permission_classes = (IsAuthenticated, HasRole)
    required_roles = (User.Role.ADMIN,)

    def get(self, request):
        return Response({"attendance_threshold": attendance_threshold()})

    def patch(self, request):
        serializer = ThresholdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        settings_row, _ = AttendanceSettings.objects.get_or_create(pk=1)
        settings_row.attendance_threshold = serializer.validated_data["attendance_threshold"]
        settings_row.save(update_fields=["attendance_threshold", "updated_at"])
        return Response({"attendance_threshold": settings_row.attendance_threshold})
