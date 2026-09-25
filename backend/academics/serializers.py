from rest_framework import serializers

from .models import FacultyAssignment, Student


class FacultyAssignmentSerializer(serializers.ModelSerializer):
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    section_name = serializers.CharField(source="section.name", read_only=True)
    department_code = serializers.CharField(source="section.department.code", read_only=True)
    academic_year = serializers.CharField(source="section.academic_year", read_only=True)
    semester = serializers.IntegerField(source="section.semester", read_only=True)

    class Meta:
        model = FacultyAssignment
        fields = ("id", "subject", "section", "subject_code", "subject_name", "section_name", "department_code", "academic_year", "semester")


class RosterStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ("id", "student_id", "name")
