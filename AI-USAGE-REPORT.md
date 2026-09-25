# AI Usage Report

## Tool used

ChatGPT through Codex.

## How AI was used

AI assistance was used throughout development to interpret the supplied task, plan the implementation, draft and edit application code, review role and data access rules, troubleshoot errors, and prepare project documentation. AI generated or edited portions of the backend, frontend, and tests; this was substantial implementation assistance, not only proofreading.

During review, AI helped identify and fix issues found by checks, API tests, build output, and the candidate's browser feedback. Examples include a dashboard query error and a faculty dashboard response that was incomplete when no Faculty profile existed.

## Candidate contribution and review

The candidate supplied the assignment context, approved the staged implementation, created local user and academic records through the admin interface, exercised the application in a browser, and reported issues for investigation. The candidate should review this description and add any other manual code changes or contributions before submitting.

## Verification

During AI-assisted development, the following checks were run successfully:

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test accounts.tests attendance.tests` — 12 tests passed, including dashboard and role-access cases
- `npm run build` — Vite production build passed

The candidate also ran the app locally and shared browser screenshots while exercising admin, faculty, and student setup/workflows. The application was not deployed, and PostgreSQL hosting was not tested.

## Limitations

The candidate is responsible for reviewing the code and this report for accuracy before submission. AI assistance does not replace the candidate's understanding of the implementation. The assignment document was supplied as context; the Google Drive copy was not independently reviewed during preparation of this report.
