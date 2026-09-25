"""Faculty attendance creation and scoped session history/detail APIs."""
from django.db import IntegrityError, transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import HasRole
from .models import AttendanceRecord, AttendanceSession, CorrectionRequest
from .serializers import (
    AttendanceSessionCreateSerializer,
    AttendanceSessionSerializer,
    CorrectionRequestCreateSerializer,
    CorrectionRequestSerializer,
    CorrectionReviewSerializer,
    StudentAttendanceSessionSerializer,
)
from .services import AttendanceSessionConflict, create_attendance_session


def accessible_sessions(user):
    queryset = AttendanceSession.objects.select_related(
        "subject", "section", "section__department", "faculty", "faculty__user"
    ).prefetch_related(
        Prefetch("records", queryset=AttendanceRecord.objects.select_related("student"))
    )
    if user.is_superuser or user.role == User.Role.ADMIN:
        return queryset
    if user.role == User.Role.FACULTY:
        return queryset.filter(faculty__user=user)
    if user.role == User.Role.STUDENT:
        return queryset.filter(records__student__user=user).distinct()
    return queryset.none()


class AttendanceSessionListCreateView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        sessions = accessible_sessions(request.user)
        section_id = request.query_params.get("section")
        subject_id = request.query_params.get("subject")
        from_date = request.query_params.get("from")
        to_date = request.query_params.get("to")
        if from_date and parse_date(from_date) is None:
            return Response({"from": ["Use an ISO date such as 2026-09-25."]}, status=status.HTTP_400_BAD_REQUEST)
        if to_date and parse_date(to_date) is None:
            return Response({"to": ["Use an ISO date such as 2026-09-25."]}, status=status.HTTP_400_BAD_REQUEST)
        if section_id and not section_id.isdigit():
            return Response({"section": ["Must be a numeric section ID."]}, status=status.HTTP_400_BAD_REQUEST)
        if subject_id and not subject_id.isdigit():
            return Response({"subject": ["Must be a numeric subject ID."]}, status=status.HTTP_400_BAD_REQUEST)
        if section_id:
            sessions = sessions.filter(section_id=section_id)
        if subject_id:
            sessions = sessions.filter(subject_id=subject_id)
        if from_date:
            sessions = sessions.filter(date__gte=from_date)
        if to_date:
            sessions = sessions.filter(date__lte=to_date)
        page = request.query_params.get("page", "1")
        if not page.isdigit() or int(page) < 1:
            return Response({"page": ["Must be a positive integer."]}, status=status.HTTP_400_BAD_REQUEST)
        page_size = 25
        count = sessions.count()
        start = (int(page) - 1) * page_size
        page_sessions = list(sessions[start:start + page_size])
        serializer_class = StudentAttendanceSessionSerializer if request.user.role == User.Role.STUDENT else AttendanceSessionSerializer
        results = serializer_class(page_sessions, many=True, context={"request": request}).data
        return Response({
            "count": count,
            "next": int(page) + 1 if start + page_size < count else None,
            "previous": int(page) - 1 if int(page) > 1 else None,
            "results": results,
        })

    def post(self, request):
        if not (request.user.is_superuser or request.user.role in (User.Role.ADMIN, User.Role.FACULTY)):
            return Response({"detail": "Only faculty and admins can record attendance."}, status=status.HTTP_403_FORBIDDEN)
        serializer = AttendanceSessionCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        try:
            session = create_attendance_session(
                assignment=values["assignment"],
                attendance_date=values["date"],
                start_time=values.get("start_time"),
                end_time=values.get("end_time"),
                records=values["records"],
            )
        except AttendanceSessionConflict:
            return Response({"date": ["Attendance already exists for this subject and section on that date."]}, status=status.HTTP_409_CONFLICT)
        session = accessible_sessions(request.user).get(pk=session.pk)
        return Response(AttendanceSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class AttendanceSessionDetailView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    lookup_url_kwarg = "session_id"

    def get_serializer_class(self):
        if self.request.user.role == User.Role.STUDENT and not self.request.user.is_superuser:
            return StudentAttendanceSessionSerializer
        return AttendanceSessionSerializer

    def get_queryset(self):
        return accessible_sessions(self.request.user)


class StudentAttendanceHistoryView(generics.ListAPIView):
    """Self-only student history; user IDs in URLs are intentionally absent."""
    serializer_class = StudentAttendanceSessionSerializer
    permission_classes = (IsAuthenticated, HasRole)
    required_roles = (User.Role.STUDENT,)

    def get_queryset(self):
        queryset = accessible_sessions(self.request.user).filter(
            records__student__user=self.request.user
        ).distinct()
        return filter_sessions(queryset, self.request)


def filter_sessions(queryset, request):
    """Apply validated common date, section, and subject filters."""
    from_date = request.query_params.get("from")
    to_date = request.query_params.get("to")
    section_id = request.query_params.get("section")
    subject_id = request.query_params.get("subject")
    if from_date:
        parsed = parse_date(from_date)
        if parsed is None:
            raise ValidationError({"from": "Use an ISO date such as 2026-09-25."})
        queryset = queryset.filter(date__gte=parsed)
    if to_date:
        parsed = parse_date(to_date)
        if parsed is None:
            raise ValidationError({"to": "Use an ISO date such as 2026-09-25."})
        queryset = queryset.filter(date__lte=parsed)
    if section_id:
        if not section_id.isdigit():
            raise ValidationError({"section": "Must be a numeric section ID."})
        queryset = queryset.filter(section_id=section_id)
    if subject_id:
        if not subject_id.isdigit():
            raise ValidationError({"subject": "Must be a numeric subject ID."})
        queryset = queryset.filter(subject_id=subject_id)
    if from_date and to_date and parse_date(from_date) > parse_date(to_date):
        raise ValidationError({"to": "End date must not be earlier than start date."})
    return queryset


class FacultyAttendanceHistoryView(generics.ListAPIView):
    serializer_class = AttendanceSessionSerializer
    permission_classes = (IsAuthenticated, HasRole)
    required_roles = (User.Role.ADMIN, User.Role.FACULTY)

    def get_queryset(self):
        return filter_sessions(accessible_sessions(self.request.user), self.request)


class CorrectionRequestListCreateView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self, request):
        queryset = CorrectionRequest.objects.select_related(
            "attendance_record__student", "attendance_record__session__subject",
            "requested_by", "reviewed_by",
        )
        user = request.user
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.STUDENT:
            return queryset.filter(requested_by=user)
        if user.role == User.Role.FACULTY:
            return queryset.filter(attendance_record__session__faculty__user=user)
        return queryset.none()

    def get(self, request):
        queryset = self.get_queryset(request)
        status_filter = request.query_params.get("status")
        if status_filter:
            if status_filter not in CorrectionRequest.Status.values:
                return Response({"status": ["Use PENDING, APPROVED, or REJECTED."]}, status=status.HTTP_400_BAD_REQUEST)
            queryset = queryset.filter(status=status_filter)
        page = request.query_params.get("page", "1")
        if not page.isdigit() or int(page) < 1:
            return Response({"page": ["Must be a positive integer."]}, status=status.HTTP_400_BAD_REQUEST)
        page_size = 25
        count = queryset.count()
        start = (int(page) - 1) * page_size
        results = CorrectionRequestSerializer(queryset[start:start + page_size], many=True).data
        return Response({"count": count, "next": int(page) + 1 if start + page_size < count else None,
                         "previous": int(page) - 1 if int(page) > 1 else None, "results": results})

    def post(self, request):
        serializer = CorrectionRequestCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                request_row = CorrectionRequest.objects.create(
                    attendance_record=serializer.validated_data["attendance_record"],
                    requested_by=request.user,
                    requested_status=serializer.validated_data["requested_status"],
                    reason=serializer.validated_data["reason"],
                )
        except IntegrityError:
            return Response({"attendance_record_id": ["A correction request is already pending for this record."]}, status=status.HTTP_409_CONFLICT)
        return Response(CorrectionRequestSerializer(request_row).data, status=status.HTTP_201_CREATED)


class CorrectionReviewView(APIView):
    permission_classes = (IsAuthenticated, HasRole)
    required_roles = (User.Role.ADMIN,)

    @transaction.atomic
    def post(self, request, correction_id):
        serializer = CorrectionReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        correction = get_object_or_404(
            CorrectionRequest.objects.select_for_update().select_related("attendance_record"),
            pk=correction_id,
        )
        if correction.status != CorrectionRequest.Status.PENDING:
            return Response({"detail": "This correction request has already been reviewed."}, status=status.HTTP_409_CONFLICT)
        if correction.requested_by_id == request.user.pk:
            return Response({"detail": "You cannot review your own correction request."}, status=status.HTTP_403_FORBIDDEN)

        values = serializer.validated_data
        if values["decision"] == "APPROVE":
            record = correction.attendance_record
            record.status = correction.requested_status
            record.save(update_fields=["status"])
            correction.status = CorrectionRequest.Status.APPROVED
        else:
            correction.status = CorrectionRequest.Status.REJECTED
        correction.reviewed_by = request.user
        correction.review_comment = values.get("review_comment", "")
        correction.reviewed_at = timezone.now()
        correction.save(update_fields=["status", "reviewed_by", "review_comment", "reviewed_at"])
        correction = CorrectionRequest.objects.select_related(
            "attendance_record__student", "attendance_record__session__subject", "requested_by", "reviewed_by"
        ).get(pk=correction.pk)
        return Response(CorrectionRequestSerializer(correction).data)
