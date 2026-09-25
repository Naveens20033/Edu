"""Validated payloads and output serializers for attendance endpoints."""
from django.utils import timezone
from rest_framework import serializers

from academics.models import FacultyAssignment, Student
from .models import AttendanceRecord, AttendanceSession


class AttendanceEntrySerializer(serializers.Serializer):
    student_id = serializers.IntegerField(min_value=1)
    status = serializers.ChoiceField(choices=AttendanceRecord.Status.choices)


class AttendanceSessionCreateSerializer(serializers.Serializer):
    assignment_id = serializers.IntegerField(min_value=1)
    date = serializers.DateField()
    start_time = serializers.TimeField(required=False, allow_null=True)
    end_time = serializers.TimeField(required=False, allow_null=True)
    records = AttendanceEntrySerializer(many=True, allow_empty=False, max_length=500)

    def validate_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("Attendance cannot be recorded for a future date.")
        return value

    def validate(self, attrs):
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({"end_time": "End time must be later than start time."})

        record_ids = [record["student_id"] for record in attrs["records"]]
        if len(record_ids) != len(set(record_ids)):
            raise serializers.ValidationError({"records": "Each student can appear only once."})

        user = self.context["request"].user
        if user.is_superuser or user.role == "ADMIN":
            assignments = FacultyAssignment.objects.filter(pk=attrs["assignment_id"])
        else:
            if user.role != "FACULTY" or not user.is_active:
                raise serializers.ValidationError({"assignment_id": "An active faculty account is required to record attendance."})
            assignments = FacultyAssignment.objects.filter(pk=attrs["assignment_id"], faculty__user=user)
        assignment = assignments.select_related("subject", "section", "faculty").first()
        if assignment is None:
            raise serializers.ValidationError({"assignment_id": "This teaching assignment is not available to your account."})

        if assignment.faculty.user.role != "FACULTY":
            raise serializers.ValidationError({"assignment_id": "The assigned faculty profile is not linked to an active faculty account."})
        if not assignment.faculty.user.is_active:
            raise serializers.ValidationError({"assignment_id": "The assigned faculty account is inactive."})
        if assignment.subject.department_id != assignment.section.department_id:
            raise serializers.ValidationError({"assignment_id": "The subject and section belong to different departments."})
        if assignment.subject.semester != assignment.section.semester:
            raise serializers.ValidationError({"assignment_id": "The subject and section semesters do not match."})

        enrolled = Student.objects.filter(section=assignment.section)
        inconsistent_enrollment = enrolled.exclude(department_id=assignment.section.department_id).exists()
        if inconsistent_enrollment:
            raise serializers.ValidationError({"assignment_id": "This section has students assigned to a different department. Contact an administrator."})
        enrolled_ids = set(enrolled.values_list("id", flat=True))
        if set(record_ids) != enrolled_ids:
            raise serializers.ValidationError({
                "records": "Submit exactly one attendance status for every student currently enrolled in this section."
            })

        if AttendanceSession.objects.filter(
            subject=assignment.subject,
            section=assignment.section,
            date=attrs["date"],
        ).exists():
            raise serializers.ValidationError({"date": "Attendance has already been recorded for this subject and section on that date."})

        attrs["assignment"] = assignment
        return attrs


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source="student.student_id", read_only=True)
    student_name = serializers.CharField(source="student.name", read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = ("id", "student", "student_id", "student_name", "status", "marked_at")


class AttendanceSessionSerializer(serializers.ModelSerializer):
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    section_name = serializers.CharField(source="section.name", read_only=True)
    faculty_name = serializers.CharField(source="faculty.name", read_only=True)
    records = AttendanceRecordSerializer(many=True, read_only=True)
    record_count = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceSession
        fields = (
            "id", "subject", "subject_code", "subject_name", "section", "section_name",
            "faculty", "faculty_name", "date", "start_time", "end_time", "created_at",
            "record_count", "records",
        )

    def get_record_count(self, obj):
        return len(obj.records.all())


class StudentAttendanceSessionSerializer(AttendanceSessionSerializer):
    """Return just the signed-in student's mark, never classmates' marks."""
    records = serializers.SerializerMethodField()

    def get_records(self, obj):
        user = self.context["request"].user
        record = next((record for record in obj.records.all() if record.student.user_id == user.pk), None)
        return [AttendanceRecordSerializer(record).data] if record else []


class AttendanceRecordUpdateSerializer(serializers.Serializer):
    """Admin-only direct correction input; ordinary users use requests later."""
    status = serializers.ChoiceField(choices=AttendanceRecord.Status.choices)


class CorrectionRequestCreateSerializer(serializers.Serializer):
    attendance_record_id = serializers.IntegerField(min_value=1)
    requested_status = serializers.ChoiceField(choices=AttendanceRecord.Status.choices)
    reason = serializers.CharField(min_length=10, max_length=1000, trim_whitespace=True)

    def validate(self, attrs):
        from .models import CorrectionRequest

        user = self.context["request"].user
        records = AttendanceRecord.objects.select_related("student__user", "session__faculty__user")
        if user.is_superuser or user.role == "ADMIN":
            pass
        elif user.role == "STUDENT":
            records = records.filter(student__user=user)
        elif user.role == "FACULTY":
            records = records.filter(session__faculty__user=user)
        else:
            records = records.none()
        try:
            record = records.get(pk=attrs["attendance_record_id"])
        except AttendanceRecord.DoesNotExist as exc:
            raise serializers.ValidationError({"attendance_record_id": "Attendance record not found."}) from exc
        if record.status == attrs["requested_status"]:
            raise serializers.ValidationError({"requested_status": "Requested status must differ from the recorded status."})
        if CorrectionRequest.objects.filter(attendance_record=record, status=CorrectionRequest.Status.PENDING).exists():
            raise serializers.ValidationError({"attendance_record_id": "A correction request is already pending for this record."})
        attrs["attendance_record"] = record
        return attrs


class CorrectionRequestSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source="attendance_record.student.student_id", read_only=True)
    student_name = serializers.CharField(source="attendance_record.student.name", read_only=True)
    subject_code = serializers.CharField(source="attendance_record.session.subject.code", read_only=True)
    session_date = serializers.DateField(source="attendance_record.session.date", read_only=True)
    current_status = serializers.CharField(source="attendance_record.status", read_only=True)
    requester_name = serializers.CharField(source="requested_by.get_username", read_only=True)
    reviewer_name = serializers.CharField(source="reviewed_by.get_username", read_only=True)

    class Meta:
        from .models import CorrectionRequest
        model = CorrectionRequest
        fields = (
            "id", "attendance_record", "student_id", "student_name", "subject_code", "session_date",
            "current_status", "requested_status", "reason", "status", "requested_by", "requester_name",
            "reviewed_by", "reviewer_name", "review_comment", "created_at", "reviewed_at",
        )
        read_only_fields = fields


class CorrectionReviewSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=(("APPROVE", "Approve"), ("REJECT", "Reject")))
    review_comment = serializers.CharField(max_length=1000, allow_blank=True, required=False, trim_whitespace=True)

    def validate(self, attrs):
        if attrs["decision"] == "REJECT" and not attrs.get("review_comment", "").strip():
            raise serializers.ValidationError({"review_comment": "Add a brief reason when rejecting a request."})
        return attrs
