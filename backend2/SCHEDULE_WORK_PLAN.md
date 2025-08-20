### Work plan: Scheduler feature (modular, sequential)

#### Phase 1 — Foundations and configuration
- [x] Add dependency for scheduling and timezone handling (Flask-APScheduler; Asia/Jerusalem).
- [x] Add env vars: SCHEDULER_TIMEZONE=Asia/Jerusalem, MAX_CONCURRENT_SCHEDULED_TASKS, MIN_ROUTER_GAP_SECONDS.
- [x] Decide designated process/instance to run the scheduler (single-runner flag/env).

#### Phase 2 — Data model
- [x] Create ScheduledTask model with fields: user_id, router_id, service, task, params (JSON), hour, minute, days_of_week?, enabled, metadata? (incl. last_known_session_id?), last_run_at, last_status, last_error.
- [x] Add indices on (user_id, router_id) and (enabled, hour, minute).
- [x] Generate migration (autogenerate).
- [x] Apply migration (alembic upgrade head) after review.

#### Phase 3 — Scheduler bootstrap
- [x] Initialize APScheduler with timezone Asia/Jerusalem and configured executors.
- [x] Register a single minute-based dispatcher job.
- [x] Add a guard so only the designated instance enables the scheduler.

#### Phase 4 — Task registry and resolution contract
- [x] Create a registry keyed by service + task → { call, resolve_args }.
- [x] Define a minimal resolver contract: input (user_id, router_id, params), output (args/kwargs for the service call).
- [ ] Seed registry with demo tasks (decorators to be added manually in services).

#### Phase 5 — Service-specific group resolvers
- [x] In bandwidth service, add resolve_group_targets(user_id, router_id, group_id) → List of IP strings.
- [x] In AGH service, add resolve_group_targets(user_id, router_id, group_id) → devices/identifiers in the exact format AGH expects.
- [x] In device_group service, add a helper to fetch current group members efficiently (IPs/MACs as needed).

#### Phase 6 — Session management utility
- [x] Implement a scheduler-side helper to ensure/obtain an active session for (user_id, router_id).
- [x] Attempt refresh; if not present/expired, start session with session_id = user_id (project convention).
- [x] Return the valid session_id to the dispatcher for service calls.

#### Phase 7 — Dispatcher implementation
- [x] On each tick, compute current local time (Asia/Jerusalem) and select enabled tasks due now (respect days_of_week).
- [x] Apply throttling: global concurrency cap, per-router single-flight lock, optional per-router cooldown.
- [x] Add small randomized jitter/staggering for simultaneous tasks.
- [x] For each task: ensure session, resolve group targets if group_id in params (delegate to service resolver), pass other params unchanged, then call the mapped service.
- [x] Capture and persist last_run_at, last_status, last_error; optionally update metadata.last_known_session_id.
- [x] Log deferrals and retries with backoff and jitter.

#### Phase 8 — API endpoints (DB-driven scheduling)
- [x] Create minimal CRUD: create, update timing, enable/disable, delete, list, run-now.
- [x] Validate: ownership (user/router), service + task recognized, params schema per task, timing fields, immutability of functional params after creation.
- [x] Ensure responses use the standard JSON envelope.

#### Phase 9 — Services alignment (minimal changes)
- [x] Keep existing service functions unchanged for execution paths.
- [x] Ensure services are request-context free and return the standard tuple.
- [x] Optionally expose thin wrappers only if necessary for clean parameter acceptance (keep logic in resolvers).

#### Phase 10 — Observability and admin
- [ ] Add logs around dispatcher lifecycle, session acquisition, resolutions, calls, errors, deferrals.
- [ ] Expose listing endpoint including last_run_at, last_status, last_error.
- [ ] Add a basic health endpoint for the scheduler (e.g., last tick time).

#### Phase 11 — Validation, security, and safety
- [ ] Enforce user-router scoping on all schedule CRUD and dispatcher queries.
- [ ] Per-task params validation at creation time (bandwidth limits, AGH categories).
- [ ] Rate-limit and/or batch outbound calls to the commands server if needed.

#### Phase 12 — Testing
- [ ] Unit-test resolvers (bandwidth/AGH) with group changes reflected at run time.
- [ ] Unit-test dispatcher selection logic (timezones, days_of_week, DST boundaries).
- [ ] Integration-test session management (refresh-or-start with session_id = user_id).
- [ ] Integration-test throttling: global cap, per-router lock, cooldown, jitter.
- [ ] End-to-end demo flow: create schedule → due tick → service executed → status recorded.

#### Phase 13 — Deployment and rollout
- [ ] Update requirements and Docker image; ensure scheduler runs only on the designated instance.
- [ ] Add feature flag to disable scheduler if needed.
- [ ] Document operational runbook (envs, single-runner, monitoring, rollback).


