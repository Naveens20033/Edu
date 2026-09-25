from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated

from accounts.models import User
from accounts.permissions import HasRole
from .models import FacultyAssignment, Section, Student
from .serializers import FacultyAssignmentSerializer, RosterStudentSerializer


class FacultyAssignmentListView(generics.ListAPIView):
    serializer_class = FacultyAssignmentSerializer
    permission_classes = (IsAuthenticated, HasRole)
    required_roles = (User.Role.ADMIN, User.Role.FACULTY)

    def get_queryset(self):
        queryset = FacultyAssignment.objects.select_related(
            "subject", "section", "section__department", "faculty", "faculty__user"
        )
        if self.request.user.is_superuser or self.request.user.role == User.Role.ADMIN:
            return queryset
        return queryset.filter(faculty__user=self.request.user)


class SectionRosterView(generics.ListAPIView):
    serializer_class = RosterStudentSerializer
    permission_classes = (IsAuthenticated, HasRole)
    required_roles = (User.Role.ADMIN, User.Role.FACULTY)

    def get_queryset(self):
        section_id = self.kwargs["section_id"]
        if not (self.request.user.is_superuser or self.request.user.role == User.Role.ADMIN):
            assignments = FacultyAssignment.objects.filter(section_id=section_id, faculty__user=self.request.user)
            if not assignments.exists():
                raise NotFound("No assigned section is available to this account.")
        elif not Section.objects.filter(pk=section_id).exists():
            raise NotFound("Section not found.")
        return Student.objects.filter(section_id=section_id).select_related("section").order_by("student_id")
