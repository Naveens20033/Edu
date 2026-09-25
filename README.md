# Smart Attendance Management System

A college attendance prototype built with Django REST Framework and React. The system is designed around three roles: admin, faculty, and student. Its core workflows cover attendance entry, attendance review, correction requests, history, and low-attendance reporting.

## Current project stage

The repository currently contains the project scaffold, normalized database models, and JWT authentication endpoints. The login form is still visual only; frontend token handling and role-aware routes are a remaining UI task.

## Data model

- `accounts.User` extends Django's user with a unique email and an `ADMIN`, `FACULTY`, or `STUDENT` application role.
- `academics.Department`, `Section`, and `Subject` describe the college's academic structure. `Student` and `Faculty` profiles link a person to a login. `FacultyAssignment` grants a faculty member a subject-section teaching assignment.
- `attendance.AttendanceSession` represents one meeting. `AttendanceRecord` stores each student's present/absent mark. `CorrectionRequest` stores the proposed value and review trail separately from the mark. `AttendanceSettings` stores the attendance threshold (default 75%).

The database prevents duplicate department/section/subject identifiers, duplicate faculty assignments, duplicate daily subject-section sessions, duplicate marks in one session, and multiple pending correction requests for the same mark. Related academic and historical attendance rows use `PROTECT` to avoid accidentally deleting records needed for audit/history. API-level validation will additionally ensure profile roles, department/section consistency, subject/section consistency, enrollment, and faculty authorization.

An active `ADMIN` role can use Django's built-in `/admin/` site to provision departments, sections, subjects, users, students, faculty, and assignments. Superusers are presented as application admins as well. The admin site remains a practical assessment-prototype management interface; role permissions for normal attendance APIs are still explicitly checked by each API view.

## Attendance entry API

- `GET /api/assignments/` returns all assignments for admins and only the signed-in faculty member's assignments for faculty.
- `GET /api/sections/{section_id}/students/` returns a roster only when the signed-in faculty member is assigned to that section (admins may inspect any existing section).
- `POST /api/attendance/sessions/` records a session. Example payload:

```json
{
  "assignment_id": 12,
  "date": "2026-09-25",
  "records": [
    {"student_id": 81, "status": "PRESENT"},
    {"student_id": 82, "status": "ABSENT"}
  ]
}
```

The server derives the session faculty from the assignment. The submitted student IDs must be the full current section roster exactly once. Sessions are limited to one subject-section meeting per date, cannot be future-dated, and save in one transaction. The unique constraint handles concurrent duplicate submissions; conflicts return HTTP 409.

- `GET /api/attendance/sessions/` returns a role-scoped session list (optional `section`, `subject`, `from`, and `to` filters).
- `GET /api/attendance/sessions/{id}/` returns details only when the user may view that session.
- `GET /api/attendance/history/` is the student's own session history; responses include only that student's mark.
- `GET /api/attendance/faculty-history/` returns history for a faculty member's own sessions, or all sessions for admins. Both history endpoints support `from`, `to`, `section`, `subject`, and `page` filters and return a paginated response.

## Attendance corrections

- `GET /api/corrections/?status=PENDING` returns correction requests visible to the current user. Students see requests they submitted; faculty see requests for their own sessions; admins see all requests.
- `POST /api/corrections/` accepts `attendance_record_id`, `requested_status` (`PRESENT` or `ABSENT`), and a reason of at least ten characters. A student can request a change only for their own mark, and faculty only for marks in their sessions. Only one request per mark can be pending.
- `POST /api/corrections/{id}/review/` is admin-only and accepts `{"decision":"APPROVE","review_comment":"..."}` or `{"decision":"REJECT","review_comment":"..."}`. Rejections require a comment. Approval updates the mark and records reviewer/timestamp/comment in the same transaction; reviewed requests cannot be changed again.

The student history screen supports date filtering and correction submission. Admins can review pending requests at `/corrections`; faculty can inspect filtered session history at `/attendance/history`.

## Dashboards and reports

- `GET /api/dashboard/` returns a role-specific summary: college metrics and daily attendance for admins, assigned classes and low-attendance students for faculty, and overall/subject-wise attendance plus recent records for students.
- `GET /api/reports/low-attendance/` returns threshold warnings scoped to the caller's role. `GET /api/settings/attendance-threshold/` reads the current threshold; admins can `PATCH` `{"attendance_threshold": 75}` with an integer from 1 to 100.
- A percentage is `present records / recorded attendance records * 100`. No records returns `null`, displayed as “No attendance recorded.” Low-attendance reports use the unrounded rate for threshold comparison; the displayed percentage is rounded to one decimal place.
- Admin daily metrics and the recent trend use recorded attendance marks only. Faculty dashboard shows recorded sessions today; this prototype has no timetable, so it does not claim which assigned classes are truly pending.

Dashboard pages are available at `/dashboard`, with admin threshold controls, faculty class/history links, student subject summaries, and a role-scoped low-attendance report at `/reports/low-attendance`.

The React attendance page uses these endpoints to select an assignment, load the roster, mark all or individual statuses, and submit once. API errors and duplicate conflicts are shown inline. Student history returns only that student's mark in each session, never the rest of the class roster.

Generate/update migrations after changing models, then apply them:

```powershell
cd backend
python manage.py makemigrations accounts academics attendance
python manage.py migrate
```

## Authentication API

- `POST /api/auth/token/` accepts `{"username": "...", "password": "..."}` and returns access/refresh JWTs plus a safe user profile. The `username` field accepts either the account username or email address.
- `POST /api/auth/token/refresh/` accepts `{"refresh": "..."}` and rotates the refresh token.
- `GET /api/auth/me/` returns the authenticated user's profile. Send `Authorization: Bearer <access>`.
- `POST /api/auth/logout/` accepts `{"refresh": "..."}`, revokes that refresh token, and returns 205. Possession of the token is required so logout works even after the access token expires. The client should also clear its local auth state.

Access tokens last 15 minutes and refresh tokens last one day. Role and username are JWT claims for client display/routing only; API views must continue checking the authenticated database user and role. `accounts.permissions` has reusable role permission classes. Object-level scoping for student and faculty data belongs in each feature endpoint/queryset and will be added with those APIs.

JWT logout uses Simple JWT's blacklist app. Run `python manage.py migrate` to create its token tables as well as project tables. For production, use a strong private secret key and HTTPS; the current frontend scaffold will need a deliberate token-storage strategy when auth is connected.

## Requirements

- Python 3.11 or newer
- Node.js 20 or newer
- npm

## Run the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The backend listens at `http://127.0.0.1:8000`. JWT routes are available at `/api/auth/token/` and `/api/auth/token/refresh/`.

## Run the frontend

```powershell
cd frontend
npm install
npm run dev
```

The Vite development server listens at `http://127.0.0.1:5173`.

## Configuration

Copy `.env.example` to `.env` in the repository root and set a private `DJANGO_SECRET_KEY` before running outside local development. Backend settings load that file when `python-dotenv` is installed (it is included in backend requirements). SQLite is used by default. Set `DATABASE_URL` to a PostgreSQL connection URL to use PostgreSQL; allowed database drivers are included in backend requirements.

## Planned implementation milestones

1. Project setup and application shell. (scaffolded)
2. Academic and attendance data models with database constraints. (implemented with initial migrations)
3. JWT authentication, roles, and backend authorization. (implemented; API-tested)
4. Faculty attendance entry and student roster. (implemented; API-tested)
5. Attendance history and correction workflow. (implemented; API-tested)
6. Role-specific dashboards, reports, and low-attendance views. (implemented; API-tested)
7. Responsive refinements and accessible loading/error/empty states. (implemented; production build passes)
8. API/UI verification and final requirement audit. (backend checks, migration check, 12 API tests, and frontend build pass; browser/deployment review remains)

The detailed requirement audit, validation limits, AI-use report, architecture decisions, and project-specific interview preparation are in [docs/assessment-review.md](docs/assessment-review.md).

## Verification

Focused Django API tests live in `backend/accounts/tests/` and `backend/attendance/tests/`. They cover username/email login, safe profile output, faculty assignment scope, complete roster validation, duplicate prevention, student mark privacy, correction approval, and threshold reporting.

```powershell
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test accounts.tests attendance.tests
cd ..\frontend
npm run build
```

The backend and frontend dependencies have been installed in the current development environment. The checks, migration drift check, 12 API tests, and Vite build have passed. Interactive browser review and deployment against PostgreSQL have not been performed.

Suggested first commit: `chore: scaffold Django and React applications`.
