# Assessment review and interview notes

## Requirement audit

| Requirement | Implemented | Main locations | Verification status |
|---|---|---|---|
| Admin, faculty, and student roles | Yes | `backend/accounts/models.py`, `backend/accounts/permissions.py` | Django system check passed; exercised by API tests |
| JWT login, refresh, logout, profile | Yes; username or email login | `backend/accounts/serializers.py`, `backend/accounts/views.py` | Username/email login and profile API tests passed |
| Academic data management | Yes, through Django admin | `backend/academics/admin.py`, `backend/accounts/admin.py` | Source review |
| Assignment-scoped faculty access | Yes | `backend/academics/views.py`, `backend/attendance/serializers.py` | Faculty access API tests passed |
| Record a complete roster atomically | Yes | `backend/attendance/serializers.py`, `backend/attendance/services.py` | Roster creation and validation API tests passed |
| Prevent duplicate sessions and duplicate marks | Yes, validation plus database constraints | `backend/attendance/models.py`, `backend/attendance/services.py` | Django system and migration drift checks passed; duplicate API test passed |
| Student self-only history and session detail | Yes; responses contain only that student's mark | `backend/attendance/views.py`, `backend/attendance/serializers.py` | Student privacy API test passed |
| Attendance corrections and admin review audit | Yes; a request must be approved before the mark changes | `backend/attendance/views.py`, `backend/attendance/models.py`, `frontend/src/pages/CorrectionQueuePage.jsx` | Correction approval and ownership API tests passed |
| Role-specific dashboards and low attendance | Yes | `backend/attendance/reporting.py`, `backend/attendance/report_views.py`, `frontend/src/pages/DashboardPage.jsx` | Admin dashboard and unconfigured faculty dashboard API tests passed |
| Configurable threshold | Yes, admin-only, integer 1–100 | `backend/attendance/report_views.py`, `frontend/src/pages/DashboardPage.jsx` | Threshold API test passed |
| Responsive entry, history, and correction screens | Implemented | `frontend/src/pages/`, `frontend/src/styles.css` | Vite production build passed; interactive browser review not performed |
| Deployment configuration | Development and PostgreSQL settings documented | `.env.example`, `backend/config/settings.py`, `README.md` | Deployment not performed |

## Validation status and known limits

- `python manage.py check` passed with no issues.
- `python manage.py makemigrations --check --dry-run` passed with no model drift.
- `python manage.py test accounts.tests attendance.tests` passed: 12 tests, including regression coverage for admin dashboard loading and faculty with no profile yet.
- `npm run build` passed with Vite; npm reported zero dependency vulnerabilities.
- Python compilation passed for backend source and tests.
- No seed data is included. Create an admin with `python manage.py createsuperuser`, then add departments, sections, subjects, user accounts, student/faculty profiles, and faculty assignments in Django admin.
- The session rule is one session per subject + section + date. Multiple same-day meetings would require a class slot or start time in the unique constraint.
- There is no timetable entity. The faculty dashboard counts sessions recorded today; it does not infer which unrecorded assignments are pending.
- The prototype stores JWTs in browser local storage. A production deployment should evaluate secure, HttpOnly cookies and their CSRF requirements.
- PostgreSQL compatibility is configured but has not been exercised. The app has not been deployed.

## Architecture and decision notes

The project uses one Django REST Framework service and one React single-page app. This keeps the assessment deployable and explainable. Django owns validation, role checks, database constraints, and reports; React handles navigation, forms, and feedback states.

`AttendanceSession` is separate from `AttendanceRecord`: the session represents the class meeting, while records represent each student's mark. A session-level unique constraint prevents duplicate daily attendance. A transaction writes the session and complete roster together, so a failed save cannot leave half a class marked.

Correction requests are separate rows because historical marks need an approval trail. Requests remain pending until an admin decides. Approval updates the attendance mark and records reviewer, time, and comment together.

Attendance is `present records / all recorded records`. No records produce `null` and the UI says “No attendance recorded.” Threshold comparisons use the unrounded rate; the UI displays one decimal place.

Roles are checked on the backend. List querysets are scoped by faculty assignment or student ownership, and student session serializers filter marks so students cannot see classmates' attendance.

## AI/tool use report

**Tool used:** ChatGPT via Codex.

**What the tool assisted with:** requirements analysis, architecture and data-model planning, implementation drafts, code review, and documentation. Assistant-generated or edited files include Django settings/models/views/serializers/migrations, React pages and shared API/auth code, and project documentation.

**Prompt basis:** the user supplied the Edumerge assignment instructions in `Pasted text.txt`, asked for a complete but explainable Smart Attendance Management System, required an analysis phase with approval before implementation, and approved incremental file-by-file work. The most useful instruction was to define architecture/workflows first, wait for approval, and then build phase by phase.

**Code changed during review:** drafts were revised as integration issues were found, including removing an invalid cross-table database check constraint, restricting student responses to the current student's mark, making logout revoke refresh tokens after access expiry, supporting email login, and making Django admin attendance records read-only so corrections use the audited request flow.

**Output requiring validation:** an early model draft attempted a database check constraint comparing a student's department with a related section department. Django/database check constraints cannot validate a joined relation. It was removed and replaced with model/API validation. Static compilation is not a substitute for Django model checks.

**How issues were identified:** source review against Django constraint behavior and the security/workflow requirements, followed by Python compilation, Django checks, migration drift checks, API tests, and a production build. The API test run exposed and helped fix a student attendance response shape issue; the production build exposed and helped fix a JSX fragment error.

**Candidate changes:** no manual edits by the candidate were observed in this workspace during this session. Before submission, replace this sentence with a truthful account of any manual changes made after reviewing the implementation.

## Interview walkthrough

1. **Problem:** replace fragmented attendance sheets with a central system for recording, reviewing, and reporting class attendance.
2. **Roles:** admins configure college data and review corrections; faculty record attendance for assigned subject-section pairs; students view their own marks.
3. **Architecture:** React/Vite talks to a Django REST Framework JSON API. Django enforces security and data rules; SQLite is local and PostgreSQL can be configured.
4. **Data model:** user profiles link to students or faculty. Faculty assignments grant teaching scope. A session groups per-student records. Correction requests preserve review history.
5. **Authentication:** Simple JWT issues short-lived access and refresh tokens. Login accepts username or email. The frontend restores a session with `/api/auth/me/` and refreshes access tokens.
6. **Authorization:** API views scope querysets and check the authenticated database user's role. Protected React routes help navigation but do not replace API checks.
7. **Attendance workflow:** faculty selects an assigned class/date, loads the roster, marks each student, and submits all marks. The server verifies the full roster and saves the session in one transaction.
8. **Duplicate prevention:** an API pre-check gives a clear message; a unique constraint is the final guard if requests race.
9. **Correction workflow:** a student or faculty member submits a reason and requested status. An admin approves or rejects. Approval changes the mark and stores reviewer metadata in one transaction.
10. **Reports:** percentages aggregate present and total recorded marks. Low attendance is grouped by subject and section for faculty/admin and by subject for students. Admins configure the threshold.
11. **Trade-offs:** one session per subject-section per date is simple but disallows multiple same-day periods. Without a timetable, pending classes cannot be inferred accurately.
12. **Testing:** API tests cover login, access scope, complete roster validation, duplicate submissions, correction approval, and low-attendance privacy. They still need to run in an installed environment.
13. **Next improvements:** run checks/build/tests, add realistic demo data, add frontend component tests, consider cookie-based tokens, and deploy against PostgreSQL.

## Likely interview questions and short answers

**Why Django REST Framework?** It exposes validated JSON APIs while using Django's ORM, authentication, migrations, and admin site.

**Why have both a session and attendance records?** The session captures one meeting's subject, section, faculty, and date. Each record captures one student's status, which simplifies history and reporting.

**How do you prevent a student reading another student's records?** The API filters through the authenticated user's profile, and the student serializer returns only that student's mark. Changing an ID does not broaden the queryset.

**How do you prevent duplicate attendance?** A pre-check returns a useful message; a unique database constraint handles concurrent submissions.

**Why can't faculty directly change old marks?** Faculty submit a correction request with a reason. An admin decision and timestamp remain available for audit.

**How is attendance percentage calculated?** `present_count / recorded_count * 100`. With no records, it is undefined and the UI says that no attendance has been recorded.

**How would you scale to 100,000 students?** Keep role filters in SQL, paginate results, index common relation/date filters, measure query plans, and use PostgreSQL. Split services only if measurements justify it.

**How would you move from SQLite to PostgreSQL?** Configure `DATABASE_URL`, install the included psycopg driver, apply the same migrations, and move data with a controlled export/import. Validate constraints and reports before switching traffic.

**What indexes matter?** Django indexes foreign keys; session date and correction status are explicit indexes. Unique constraints index session subject/section/date, student/session records, and assignments. Add more after measuring query plans.

**What remains unverified?** Interactive browser behavior, responsive appearance on real devices, PostgreSQL deployment, and production hosting configuration have not been exercised. Backend checks, migrations, API tests, and the Vite build passed locally.
