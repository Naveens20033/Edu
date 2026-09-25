# Initial academic structure migration.
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("accounts", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="Department",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("code", models.CharField(max_length=12, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Section",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=30)),
                ("academic_year", models.CharField(help_text="For example, 2026-2027", max_length=9)),
                ("semester", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)])),
                ("department", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sections", to="academics.department")),
            ],
            options={"ordering": ["department__code", "academic_year", "semester", "name"]},
        ),
        migrations.CreateModel(
            name="Subject",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, unique=True)),
                ("name", models.CharField(max_length=160)),
                ("semester", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)])),
                ("department", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="subjects", to="academics.department")),
            ],
            options={"ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="Faculty",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("employee_id", models.CharField(max_length=24, unique=True)),
                ("name", models.CharField(max_length=160)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("department", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="faculty", to="academics.department")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="faculty_profile", to="accounts.user")),
            ],
            options={"ordering": ["name"], "verbose_name_plural": "faculty"},
        ),
        migrations.CreateModel(
            name="Student",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("student_id", models.CharField(max_length=24, unique=True)),
                ("name", models.CharField(max_length=160)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("department", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="students", to="academics.department")),
                ("section", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="students", to="academics.section")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="student_profile", to="accounts.user")),
            ],
            options={"ordering": ["student_id"]},
        ),
        migrations.CreateModel(
            name="FacultyAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("faculty", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="assignments", to="academics.faculty")),
                ("subject", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="assignments", to="academics.subject")),
                ("section", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="faculty_assignments", to="academics.section")),
            ],
            options={"ordering": ["section", "subject", "faculty"]},
        ),
        migrations.AddConstraint(model_name="section", constraint=models.UniqueConstraint(fields=("department", "name", "academic_year", "semester"), name="unique_section_in_term")),
        migrations.AddConstraint(model_name="facultyassignment", constraint=models.UniqueConstraint(fields=("faculty", "subject", "section"), name="unique_faculty_subject_section")),
    ]
