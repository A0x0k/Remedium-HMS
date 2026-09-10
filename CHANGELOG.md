# Changelog

All notable changes to Remedium HMS are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased] - 2026-09-10

### Added
- improve dashboard UX with timestamps, notification bell, and mobile nav ([`0e4aaca`])
- add revenue trend and appointment charts to admin dashboard ([`f471c1a`])
- add public landing page with hero, features, and security showcase ([`60c5084`])
- add pagination to document list, create encounter detail template ([`d9c6544`])
- comprehensive UX feedback system and codebase cleanup ([`5265948`])
- standardize dashboard prototypes with global UI components, enhanced branding, and improved CSS design system ([`742c9fe`])
- enhance dashboard prototypes with CRUD UI elements, navigation, and modern styling ([`aa81ac5`])
- implement HTML dashboard prototypes with glassmorphic design and branding ([`5d0df40`])
- implement global UX enhancements (Spotlight Search, page transitions, visual feedback) ([`6497919`])
- **surgery**: apply soft deletes to Surgery model ([`4ee9b72`])
- **laboratory**: apply soft deletes to LabTest model ([`df60a7b`])
- **pharmacy**: apply soft deletes to Prescription model ([`8579717`])
- **billing**: apply soft deletes to Invoice and Payment models ([`e31037f`])
- **appointments**: apply soft deletes to Appointment model ([`e2dd934`])
- **staff**: apply soft deletes to Staff model ([`b0d1639`])
- **patients**: apply soft deletes and PHI encryption to Patient model ([`452097a`])
- implement project-wide soft delete and timestamp base model ([`2cc1680`])
- implement role-based view routing and context processor with full role flags ([`e462ad1`])
- create role-specific dashboards for admin, doctor, nurse, receptionist, pharmacist, labtech, surgeon, and default ([`5e130f1`])
- implement receptionist toolkit (Check-in, Queue, Bed Map) ([`0fe92c9`])
- full-stack UI upgrades for flexible data relations ([`6d81320`])
- professional dashboard redesign â€” consistent stat cards, component CSS, appointment rows, fix card-header color ([`1f06e71`])
- UI/UX overhaul â€” grouped patient form, login redesign, empty states, card hover fix, form spinners, delete toasts ([`7b85ffb`])
- UI/UX overhaul â€” tabbed patient detail, crispy forms, print invoices, notification bell, Chart.js vitals, mobile CSS, fix all tests ([`5f66ea8`])
- fix home URL bug, add whitenoise, 24 API tests, invoice counter, changelog CI check ([`228d51c`])
- add REST API for hospital/inventory/surgery/care_monitoring, fix Redis default, add reporting tests, automate changelog ([`eae568d`])
- add seed_demo management command for realistic demo data ([`102d374`])
- add API documentation with drf-spectacular ([`661dbbf`])
- integrate OpenFDA drug lookup with UI panel ([`0606a1c`])
- add new API endpoints and audit trails ([`0d7b5ab`])
- add invoice auto-numbering and payment tracking ([`35d79ba`])
- add role-based API permissions and fix serializers ([`cfbae69`])
- add Docker health checks and CI/CD pipeline ([`78f2371`])
- **pharmacy**: Add tests and improve code quality for pharmacy app ([`11966a9`])
- **billing**: Add tests and improve code quality for billing app ([`dbe3b4c`])
- **staff**: Add tests and improve code quality for staff app ([`07a8222`])

### Changed
- Fix psycopg2 to binary version ([`2a407be`])
- Fix psycopg2 to binary version ([`8324825`])
- Fix psycopg2 to binary version ([`559ab66`])
- add engineering highlights to README ([`b6dff88`])
- Refine billing templates, dashboard views, and minor view updates ([`87e9aef`])
- add TLS config to nginx.conf and remove stray 1.1 file ([`daa960c`])
- extract homepage role context helpers and wire PatientBriefSerializer ([`0327738`])
- add pytest step to test job and fix SECRET_KEY length ([`94aa29b`])
- redesign README with modern layout and professional structure ([`85a8fb5`])
- standardize appointment form layout and improve DevOps config ([`550bfed`])
- harden CSRF, add login throttling, enforce password validation ([`036d507`])
- add template rendering tests for all apps and fix conftest ([`a36fa65`])
- remove stale templates and unused JS modules ([`bd6e0f0`])
- remove dead code from integration views ([`17e0430`])
- regenerate OpenAPI schema after model and serializer changes ([`dba6ad9`])
- update core project configuration ([`8b29910`])
- move billing signal from models.py to dedicated signals.py ([`41d2d6c`])
- add postman/ to .gitignore ([`abf7af3`])
- comprehensive UI/UX improvements across the board ([`9283399`])
- remove obsolete design scripts ([`62eb9cf`])
- switch dashboard wireframes to PNG format for improved compatibility ([`8e4aaf6`])
- add high-fidelity SVG wireframes for all specialized dashboards ([`8efce66`])
- modernize README with color-coded diagrams and security lifecycle flow ([`367ff9a`])
- expand README with clinical workflow, dashboard wireframes, and test accounts ([`1b1fa11`])
- redesign README with professional enterprise showcase and architecture diagram ([`9a91238`])
- add helper scripts for local admin and receptionist creation ([`7ad2177`])
- update completion summary with June 2026 refactoring details ([`409795e`])
- add verification tests for database security and integrity ([`6255452`])
- add encryption dependency and basic config ([`e795613`])
- update README with role-based dashboards, test accounts table, UI/UX design section ([`76cb352`])
- add management command to create test users for all 13 roles ([`29822b6`])
- enhance list templates (appointments, staff, invoices) and partials (pagination, field, empty-state) ([`779d0b4`])
- enhance patient templates and views with breadcrumbs, modal deletes, improved UX ([`f5e7e2a`])
- add scroll-to-top, loading overlay, breadcrumb support, polished login page ([`d0fe781`])
- improve toast stacking, page transitions, loading overlay, form helpers ([`bdbc0e7`])
- overhaul design system with animations, skeletons, dark mode prep, responsive polish ([`6ee15de`])
- update README with new architecture and receptionist toolkit features ([`edaff0c`])
- professionalize codebase with automated formatting and linting ([`a44e11e`])
- professionalize DB and API layers ([`146f678`])
- untrack .coverage and .env (now gitignored) ([`3c107e5`])
- stage all unstaged working-tree changes from 13-commit backlog ([`4a511f3`])
- add full-stack production showcase document ([`ebac8dc`])
- add flake8 configuration file ([`f82e5d4`])
- Update crispy-bootstrap5 to available version 2026.3 ([`393f59b`])
- Update crispy-bootstrap5 to available version 2026.3 ([`35642b0`])
- Revise email reporting instructions in SECURITY.md ([`e8525a9`])
- rewrite README with architecture diagram, badges, and API documentation ([`33b1b2d`])
- finalize app configuration and management commands ([`b6fd1e9`])
- add comprehensive test suite across all apps (93 tests) ([`39c4d1f`])
- improve templates and styling across all apps ([`3ac04a7`])
- add select_related and pagination to prevent N+1 queries ([`c2d1766`])
- unify phone validation and fix model constraints ([`e793b58`])
- Add GitHub Actions Python CI/CD workflow ([`1640b27`])
- Add MIT License ([`b069dcc`])
- Update completion date to November 18, 2025 ([`ae12d38`])
- Update last updated date to November 18, 2025 ([`19ef143`])
- Update CHECKLIST.md ([`f462c47`])
- Delete CHAT_SESSION_SUMMARY.md ([`5939d27`])
- Delete .vscode directory ([`f37adae`])
- Delete .qoder directory ([`fd8ad67`])
- Clean up repository: Remove Python cache files, add API views and serializers, update documentation, and exclude database file from tracking ([`615c4cd`])
- enhanc repo ([`69a5486`])
- **patients, appointments**: Improve code quality and test coverage ([`d907a89`])
- f1_work ([`9174355`])
- up-commit ([`e486e25`])
- Initial commit of project files ([`fbeb48c`])

### Fixed
- remove billing.urls double-include, DEBUG print, enforce invoice validation, DB filter for medical staff ([`2402a9e`])
- remove page transition delay and improve search scope ([`2f3db4c`])
- resolve DTL syntax errors and URL namespace in patient templates ([`594e904`])
- add hospital: namespace prefix to template URL tags ([`9b47562`])
- add null=True to created_at/updated_at on remaining model files ([`64ddfc5`])
- improve accessibility, SEO, and error pages ([`f251f29`])
- update InventoryItemSerializer fields after model rename ([`5ea0252`])
- remove duplicate STATUS_CHOICES inline definition in Surgery model ([`f17be79`])
- add raise_exception=True to 11 hospital views ([`c0ceb25`])
- use get_object_or_404 and reverse_lazy in reporting views ([`7f1c97d`])
- correct permission name in check_in_appointment view ([`1f634dc`])
- enforce permission checks and require POST on notification views ([`c0feb23`])
- prevent XSS via json_script filter and escapejs ([`5f00392`])
- make RemediumBaseModel timestamps nullable for backward compatibility ([`d681da8`])
- apply all review suggestions ([`68aba1b`])
- resolve XML parsing errors by explicitly writing SVGs with UTF-8 encoding and XML headers ([`70d09b9`])
- CI/CD â€” align Python versions, split dev deps, fix gitignore, drop python-ci.yml ([`1a00b92`])
- media serving, 404/500 pages, README stats, audit log, vital trends redirect, +9 tests (113 total, 75% coverage) ([`b58d50c`])
- dashboard â€” add admitted_patients stat, fix progress bar normalization, fix now context, fix status badge, replace dark admin card with light ([`daa31f4`])
- modernize all list/delete templates, fix validators, fix migration deprecations, fix ordering warnings, fix enum naming ([`4377e36`])
- create all missing templates, rebuild old-style detail pages, add hospital templates ([`2b4b9c0`])
- resolve all broken URL names â€” remove app_name from urls.py files, register all CRUD routes globally ([`d59b6f6`])
- register all missing list URLs, add InventoryItemDetailView, fix integration views, fix surgery select_related bug ([`1b04ede`])
- add missing timezone import to billing/models.py ([`fbd1a3c`])
- add missing timezone import to patients/models.py ([`2d35ad8`])
- update crispy-bootstrap5 to compatible existing version 2025.6 ([`cd522d1`])
- update crispy-bootstrap5 to compatible existing version 2025.6 ([`50c25d0`])
- resolve django-crispy-forms and crispy-bootstrap5 dependency conflict in requirements.txt ([`f551db5`])
- resolve django-crispy-forms and crispy-bootstrap5 dependency conflict ([`0ea80b4`])
- resolve settings security issues and rate limiting ([`78d8112`])


## [1.1.0] - 2026-05-01

### Added
- REST API for `hospital` app: `WardViewSet`, `RoomViewSet` — endpoints `/api/v1/wards/`, `/api/v1/rooms/`
- REST API for `inventory` app: `InventoryItemViewSet` — endpoint `/api/v1/inventory/` with `/low_stock/` action
- REST API for `surgery` app: `SurgeryViewSet` — endpoint `/api/v1/surgeries/` with `/scheduled/` action
- REST API for `care_monitoring` app: `PatientCareViewSet` — endpoint `/api/v1/care-monitoring/` with `/critical/` action
- Serializers for all four new API apps (`hospital`, `inventory`, `surgery`, `care_monitoring`)
- `report_list` URL (`/reports/`) was missing from `reporting/urls.py` — added
- 7 tests for `reporting` app covering model CRUD, `__str__`, ordering, auth enforcement, and file download

### Changed
- `REDIS_ENABLED` now defaults to `False` in `settings.py` — dev installs no longer require a running Redis instance
- `django-redis==5.4.0` and `redis==5.0.1` moved to base `requirements.txt` (were only in `requirements-prod.txt`)
- Deduplicated `django-redis` and `redis` entries in `requirements.txt`
- Registered 5 new ViewSets in `remedium_hms/urls.py`

### Removed
- `.qwen/` AI tool artifact directory deleted and added to `.gitignore`
- `appointments/models_fixed.py` leftover patch file deleted and added to `.gitignore`

### Fixed
- `db.sqlite3` confirmed not git-tracked (already in `.gitignore`)
- Indentation inconsistency in `remedium_hms/urls.py` (`path("api/v1/", ...)` was misaligned)

---

## [1.0.0] - 2026-04-08

### Added
- 14 Django apps: `core`, `patients`, `staff`, `appointments`, `billing`, `pharmacy`, `laboratory`, `surgery`, `care_monitoring`, `medical_records`, `notifications`, `integration`, `inventory`, `hospital`, `reporting`
- REST API with DRF across 7 apps, JWT authentication via `djangorestframework-simplejwt`
- Role-based permissions: Admin, Doctor, Nurse, Receptionist, Pharmacist, Lab Technician
- OpenFDA drug label and adverse event integration with 24-hour caching
- Audit trails on all clinical models via `django-simple-history`
- Auto-numbered invoices (`INV-YYYY-NNNNN`) with race-condition-safe generation
- Appointment conflict detection with 30-minute slot overlap logic
- Vital signs tracking with BMI calculation and critical condition alerts
- 93 automated tests, 75% coverage
- OpenAPI 3.0 documentation via `drf-spectacular` (Swagger UI + ReDoc)
- Docker support with non-root user and health checks
- GitHub Actions CI/CD: flake8, bandit, pytest, Docker build verification
- Rate limiting: 100 req/hr anonymous, 1000 req/hr authenticated
- Fernet encryption for external API keys
- File upload support for medical records (PDF, images, 10MB limit)
- `seed_demo` management command for realistic demo data
