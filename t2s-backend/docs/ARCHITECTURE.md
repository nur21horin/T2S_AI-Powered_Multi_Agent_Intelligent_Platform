# Backend Architecture

## Database migrations

SQLAlchemy models inherit from `app.db.base.Base`. Its metadata defines stable
names for primary keys, foreign keys, unique constraints, check constraints,
and indexes. `app.models` imports model modules for Alembic metadata discovery;
model modules import `Base` from `app.db.base` and should use string-based ORM
relationship targets to avoid import cycles.

Alembic reads `DATABASE_URL` through the same Pydantic settings used by the
application. It does not create application tables at startup. Schema changes
are generated and applied explicitly with the commands in `docs/MIGRATIONS.md`.

## Access-token revocation

Access JWTs include the user's `auth_version`, which is checked against the
database on every authenticated request. Password changes and resets increment
that version in the same transaction as refresh-token revocation. Individual
logout revocation stores only the token `jti` in shared Redis until its expiry.
Redis is a required runtime dependency for authenticated routes and for logout
requests that revoke an access JWT; health endpoints do not depend on it.

## Profiles, skills, and technical rooms

Step 4 keeps account identity and role authority in `users` and stores
role-specific data in one-to-one `student_profiles`, `teacher_profiles`, and
`alumni_profiles` tables. `skills` and `interests` are normalized shared
catalogs with user association tables. Catalog records cannot be deleted or
globally edited through user APIs.

`technical_rooms` owns visibility and room metadata. `room_memberships` is the
separate access relationship, while `membership_requests` records the request
lifecycle (`PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`). Public discovery
does not grant membership. Room ownership is assigned server-side and owner
membership is created atomically with the room. Only owners may update/archive
rooms or approve/reject requests; database constraints and row locking protect
duplicate requests and concurrent approvals.

## Tasks, submissions, evaluations, and progress

Step 5 adds `tasks`, `submissions`, and `evaluations`. A task belongs to one
technical room and one creator, and uses the lifecycle `DRAFT`, `PUBLISHED`,
`CLOSED`, and `ARCHIVED`. Room owners and active teacher members may manage
tasks. Public task visibility does not grant submission rights; submissions
require active room membership.

Each submission is an immutable attempt record for a user and task. The server
assigns the attempt number and enforces the task's resubmission policy. No file
storage is introduced; submissions contain text and optional HTTP(S) project or
repository links. A submission has at most one current evaluation. Evaluators
may finalize or return work, and students cannot evaluate their own submissions
or change scores.

Progress is calculated at read time from non-archived published/closed tasks,
the student's latest attempt, and finalized evaluations. Completion percentage
is completed eligible tasks divided by eligible tasks; returned evaluations are
not completed. Client-supplied progress totals are never accepted.

The main Step 5 API routes are:

- `POST/GET /api/v1/rooms/{room_id}/tasks`
- `GET/PATCH /api/v1/tasks/{task_id}`
- `POST /api/v1/tasks/{task_id}/publish|close|archive`
- `POST /api/v1/tasks/{task_id}/submissions`
- `GET /api/v1/tasks/{task_id}/submissions|submissions/mine`
- `GET /api/v1/submissions/{submission_id}`
- `PUT/GET /api/v1/submissions/{submission_id}/evaluation`
- `GET /api/v1/progress/me` and `GET /api/v1/progress/rooms/{room_id}/users/{user_id}`
## Step 6 Phase 1: Projects, teams, and collaboration

Projects are independent from technical rooms. A project has one owner and may be associated with at most one active team; a team may support multiple projects. Team creation atomically creates the owner membership. Team ownership is distinct from the optional delegated leader role, and ownership transfer is not implemented in Phase 1.

Team membership is historical: active, left, and removed records are retained, with a database partial unique index allowing only one active membership per user/team and one active delegated leader per team. Invitations and join requests are separate state machines. Invitation expiry is checked during response; approval of a join request or invitation creates membership in the same transaction, while rejection never grants membership. Public visibility does not imply membership, and private team/project details are authorization-filtered.

Phase 1 routes are registered under `/api/v1/projects` and `/api/v1/teams`. List routes use bounded page/limit pagination (1–100). Project-team association requires the project owner to be an active member of the target team, preventing unauthorized private-team attachment.

## Step 6 Phase 2: Hackathon management and participation

Hackathons are managed by `HackathonService`, with `Hackathon` holding lifecycle, schedule, visibility, participation mode, capacity, and team-size configuration. The lifecycle is linear: `DRAFT` -> `PUBLISHED` -> `OPEN` -> `CLOSED` -> `COMPLETED` -> `ARCHIVED`; archived records are terminal. The service owns organizer/admin authorization, date and team-size validation, bounded listing with status/participation filters, and lifecycle timestamps.

Routes are registered under `/api/v1/hackathons` for CRUD, filtered lists, lifecycle actions, individual/team registration, participant registration views, and organizer registration lists. Registration review and participant-wide views are under `/api/v1/hackathon-registrations`. Registrations are `PENDING`, `APPROVED`, `REJECTED`, or `CANCELLED`; team registrations snapshot eligible active verified members and their roles.

Capacity is enforced by locking the hackathon row and counting distinct users represented by pending and approved registration-member snapshots. Rejected and cancelled registrations do not reserve capacity, and a null participant limit means unlimited capacity. Private hackathons and registration details are actor-scoped: organizers/admins manage them, while participants see only their own pending/approved registration details.

## Step 6 Phase 3: Project-hackathon integration and submissions

`HackathonSubmission` links one existing active `Project` to one `Hackathon`; it does not copy the project entity. The submitter and optional team identify the authenticated actor and team context used for authorization, while repository URL, demo URL, and additional details are submission-specific metadata. A uniqueness constraint prevents more than one submission for a project in the same hackathon.

The submission lifecycle is `DRAFT` -> `SUBMITTED` -> `WITHDRAWN`. The service permits creation and draft edits only while the hackathon is `OPEN`, from `registration_start_at` through `start_at`; finalization and withdrawal re-lock the hackathon and submission and re-check eligibility. Withdrawn submissions are terminal. The service uses the existing project status, team membership, hackathon registration snapshot, lifecycle, exception, pagination, and audit conventions.

Individual submissions require an approved individual registration and an unassigned project owned by the submitter. Team submissions require an approved registration for the project's team and an active member present in that registration snapshot. Organizer/admin listing is separated from participant access, and participant reads require current ownership/team membership plus an approved registration. Hackathon, current-user, project, detail, update, finalize, and withdrawal routes are registered by `app/api/v1/endpoints/hackathon_submissions.py` under the `/api/v1` router.
