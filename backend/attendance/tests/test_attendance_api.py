from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from academics.models import Department, Faculty, FacultyAssignment, Section, Student, Subject
from attendance.models import AttendanceRecord, AttendanceSession, AttendanceSettings, CorrectionRequest


class AttendanceWorkflowApiTests(APITestCase):
    def setUp(self):
        self.department = Department.objects.create(name="Engineering", code="ENG")
        self.section = Section.objects.create(
            name="A", department=self.department, academic_year="2026-2027", semester=1,
        )
        self.subject = Subject.objects.create(
            code="CS101", name="Programming", department=self.department, semester=1,
        )
        self.faculty_user = User.objects.create_user(
            username="faculty.one", email="faculty@college.edu", password="faculty-password",
            role=User.Role.FACULTY,
        )
        self.faculty = Faculty.objects.create(
            user=self.faculty_user, employee_id="F001", name="Asha Rao",
            email="asha@college.edu", department=self.department,
        )
        self.assignment = FacultyAssignment.objects.create(
            faculty=self.faculty, subject=self.subject, section=self.section,
        )
        self.student_users = []
        self.students = []
        for number in range(1, 4):
            user = User.objects.create_user(
                username=f"student{number}", email=f"student{number}@college.edu",
                password="student-password", role=User.Role.STUDENT,
            )
            student = Student.objects.create(
                user=user, student_id=f"ST{number:03}", name=f"Student {number}",
                email=f"student-profile{number}@college.edu", department=self.department,
                section=self.section,
            )
            self.student_users.append(user)
            self.students.append(student)
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@college.edu", password="admin-password",
        )

    def authenticate(self, user, password):
        response = self.client.post("/api/auth/token/", {"username": user.username, "password": password})
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def attendance_payload(self, students=None):
        students = students if students is not None else self.students
        return {
            "assignment_id": self.assignment.pk,
            "date": timezone.localdate().isoformat(),
            "records": [
                {"student_id": student.pk, "status": "PRESENT" if index < 2 else "ABSENT"}
                for index, student in enumerate(students)
            ],
        }

    def test_faculty_can_load_roster_and_record_complete_session(self):
        self.authenticate(self.faculty_user, "faculty-password")
        roster = self.client.get(f"/api/sections/{self.section.pk}/students/")
        self.assertEqual(roster.status_code, 200)
        self.assertEqual(len(roster.data["results"]), 3)
        response = self.client.post("/api/attendance/sessions/", self.attendance_payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["record_count"], 3)
        self.assertEqual(AttendanceRecord.objects.filter(session_id=response.data["id"]).count(), 3)

    def test_other_faculty_cannot_use_assignment(self):
        other_user = User.objects.create_user(
            username="faculty.two", email="faculty.two@college.edu", password="other-password",
            role=User.Role.FACULTY,
        )
        Faculty.objects.create(
            user=other_user, employee_id="F002", name="Other Faculty",
            email="other.faculty@college.edu", department=self.department,
        )
        self.authenticate(other_user, "other-password")
        response = self.client.post("/api/attendance/sessions/", self.attendance_payload(), format="json")
        self.assertEqual(response.status_code, 400)

    def test_faculty_dashboard_without_profile_returns_empty_setup_state(self):
        unconfigured_user = User.objects.create_user(
            username="faculty.unconfigured", email="unconfigured@college.edu",
            password="faculty-password", role=User.Role.FACULTY,
        )
        self.authenticate(unconfigured_user, "faculty-password")
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role"], "FACULTY")
        self.assertEqual(response.data["assigned_classes"], [])
        self.assertEqual(response.data["low_attendance"], [])

    def test_incomplete_roster_and_duplicate_session_are_rejected(self):
        self.authenticate(self.faculty_user, "faculty-password")
        incomplete = self.client.post(
            "/api/attendance/sessions/", self.attendance_payload(self.students[:2]), format="json",
        )
        self.assertEqual(incomplete.status_code, 400)
        self.assertEqual(AttendanceSession.objects.count(), 0)
        first = self.client.post("/api/attendance/sessions/", self.attendance_payload(), format="json")
        self.assertEqual(first.status_code, 201)
        duplicate = self.client.post("/api/attendance/sessions/", self.attendance_payload(), format="json")
        self.assertIn(duplicate.status_code, (400, 409))
        self.assertEqual(AttendanceSession.objects.count(), 1)

    def test_student_session_detail_only_returns_own_mark(self):
        session = AttendanceSession.objects.create(
            subject=self.subject, section=self.section, faculty=self.faculty, date=timezone.localdate(),
        )
        AttendanceRecord.objects.bulk_create([
            AttendanceRecord(session=session, student=student, status="PRESENT") for student in self.students
        ])
        self.authenticate(self.student_users[0], "student-password")
        response = self.client.get(f"/api/attendance/sessions/{session.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["records"]), 1)
        self.assertEqual(response.data["records"][0]["student"], self.students[0].pk)

    def test_correction_remains_pending_until_admin_approves(self):
        session = AttendanceSession.objects.create(
            subject=self.subject, section=self.section, faculty=self.faculty, date=timezone.localdate(),
        )
        record = AttendanceRecord.objects.create(session=session, student=self.students[0], status="ABSENT")
        self.authenticate(self.student_users[0], "student-password")
        response = self.client.post("/api/corrections/", {
            "attendance_record_id": record.pk, "requested_status": "PRESENT",
            "reason": "I was present in this class.",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        record.refresh_from_db()
        self.assertEqual(record.status, AttendanceRecord.Status.ABSENT)
        self.authenticate(self.admin_user, "admin-password")
        review = self.client.post(f"/api/corrections/{response.data['id']}/review/", {
            "decision": "APPROVE", "review_comment": "Verified with the instructor.",
        }, format="json")
        self.assertEqual(review.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.status, AttendanceRecord.Status.PRESENT)
        correction = CorrectionRequest.objects.get(pk=response.data["id"])
        self.assertEqual(correction.status, CorrectionRequest.Status.APPROVED)
        self.assertEqual(correction.reviewed_by, self.admin_user)

    def test_student_cannot_request_correction_for_classmate(self):
        session = AttendanceSession.objects.create(
            subject=self.subject, section=self.section, faculty=self.faculty, date=timezone.localdate(),
        )
        record = AttendanceRecord.objects.create(session=session, student=self.students[1], status="ABSENT")
        self.authenticate(self.student_users[0], "student-password")
        response = self.client.post("/api/corrections/", {
            "attendance_record_id": record.pk, "requested_status": "PRESENT",
            "reason": "I believe this record is incorrect.",
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(CorrectionRequest.objects.count(), 0)

    def test_admin_threshold_update_and_self_scoped_low_attendance_report(self):
        self.authenticate(self.admin_user, "admin-password")
        dashboard = self.client.get("/api/dashboard/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.data["role"], "ADMIN")
        self.assertIn("total_students", dashboard.data)
        updated = self.client.patch("/api/settings/attendance-threshold/", {"attendance_threshold": 80}, format="json")
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(AttendanceSettings.objects.get(pk=1).attendance_threshold, 80)
        session = AttendanceSession.objects.create(
            subject=self.subject, section=self.section, faculty=self.faculty, date=timezone.localdate(),
        )
        AttendanceRecord.objects.bulk_create([
            AttendanceRecord(session=session, student=student, status="ABSENT") for student in self.students
        ])
        self.authenticate(self.student_users[0], "student-password")
        report = self.client.get("/api/reports/low-attendance/")
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report.data["count"], 1)
        self.assertEqual(report.data["results"][0]["subject_code"], self.subject.code)
