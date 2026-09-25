"""Root URL configuration for the API and Django admin."""
from django.contrib import admin
from django.urls import path

from accounts.views import LoginView, LogoutView, MeView, RefreshView
from academics.views import FacultyAssignmentListView, SectionRosterView
from attendance.views import (
    AttendanceSessionDetailView,
    AttendanceSessionListCreateView,
    CorrectionRequestListCreateView,
    CorrectionReviewView,
    FacultyAttendanceHistoryView,
    StudentAttendanceHistoryView,
)
from attendance.report_views import AttendanceThresholdView, DashboardView, LowAttendanceView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/token/", LoginView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", RefreshView.as_view(), name="token_refresh"),
    path("api/auth/logout/", LogoutView.as_view(), name="logout"),
    path("api/auth/me/", MeView.as_view(), name="current_user"),
    path("api/assignments/", FacultyAssignmentListView.as_view(), name="assignments"),
    path("api/sections/<int:section_id>/students/", SectionRosterView.as_view(), name="section_roster"),
    path("api/attendance/sessions/", AttendanceSessionListCreateView.as_view(), name="attendance_sessions"),
    path("api/attendance/sessions/<int:session_id>/", AttendanceSessionDetailView.as_view(), name="attendance_session_detail"),
    path("api/attendance/history/", StudentAttendanceHistoryView.as_view(), name="student_attendance_history"),
    path("api/attendance/faculty-history/", FacultyAttendanceHistoryView.as_view(), name="faculty_attendance_history"),
    path("api/corrections/", CorrectionRequestListCreateView.as_view(), name="correction_requests"),
    path("api/corrections/<int:correction_id>/review/", CorrectionReviewView.as_view(), name="correction_review"),
    path("api/dashboard/", DashboardView.as_view(), name="dashboard"),
    path("api/reports/low-attendance/", LowAttendanceView.as_view(), name="low_attendance_report"),
    path("api/settings/attendance-threshold/", AttendanceThresholdView.as_view(), name="attendance_threshold"),
]
