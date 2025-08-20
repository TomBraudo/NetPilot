# Dynamic Task Scheduling in Flask Backend

## Summary

### 1. Use Flask-APScheduler for Scheduling
- Flask-APScheduler integrates APScheduler with Flask.
- Runs scheduled jobs in background threads without blocking the server.
- Supports cron, interval, and date triggers for job scheduling.
- Allows adding, updating, removing, and listing jobs dynamically via an API.

### 2. Single Dynamic Schedule Management Endpoint
- Create one generic scheduling endpoint (e.g., `/schedule-task`) that accepts a **task name/ID** and schedules the corresponding internal Python function.
- Avoid creating separate schedule endpoints for each task.
- Maintain a **map of task names to internal functions** for easy extensibility.
- Register functions dynamically with decorators if tasks grow large.

### 3. Keep Core Task Logic Separate from Endpoints
- Extract core task code into internal functions called by both:
  - Flask route handlers (if manual triggering is needed).
  - Scheduler jobs (for automatic execution).
- This avoids the need for Flask request context in scheduled jobs.
- Scheduled jobs call internal functions directly, not HTTP endpoints.

### 4. Passing Parameters to Scheduled Tasks (Demo Rules)
- Store task parameters as JSON exactly as provided by the user; the scheduler passes them through unchanged.
- Persist identity context with the task: `user_id` and `router_id` must be stored with each scheduled task.
- Session handling: do not rely on Flask `g`. The scheduler ensures an active `session_id` at run time (see Session Management section). Optionally store a `last_known_session_id` for diagnostics, but do not depend on it.
- The only interpretation the scheduler performs is resolving dynamic group membership when a `group_id` is present.
- Use Flask-APScheduler’s `args`/`kwargs` to call the mapped service function with the resolved arguments.

### 5. Handling Multiple Tasks and Concurrent Execution
- APScheduler runs multiple jobs scheduled at the same time concurrently in a thread pool.
- Concurrency level configurable by adjusting worker pool size.
- Jobs run independently without blocking or affecting each other.

### 6. Handling Dynamic Data for Scheduled Jobs
- Demo policy: no snapshots. Always resolve dynamic group membership at execution time.
- Group changes automatically affect the next run; users cannot change other parameters in-place.
- If users want to change non-membership parameters (e.g., bandwidth values, AGH categories), they must disable/delete the schedule and create a new one.

### 7. Multi-user Setup with Database-backed Task Scheduling
- Create a `ScheduledTask` DB model storing:
  - User ID
  - Service (general type, e.g., `bandwidth`, `agh`)
  - Task name (action within service, e.g., `apply_group_limits`)
  - Task parameters (as JSON)
  - Scheduled time (hour/minute, stored as Asia/Jerusalem local time)
  - Days of week (optional for demo; e.g., integers 0-6)
  - Enabled flag
- Schedule a **single periodic “dispatcher” job** (runs every minute, timezone Asia/Jerusalem) that:
  - Queries enabled user tasks due for the current local minute (timezone-aware comparison)
  - Applies throttling caps and staggering (see Throttling section)
  - Calls the appropriate service-layer function with parameters
- Manage scheduling lifecycle entirely via database operations and user API calls.
- Ensure user-task isolation and security via DB filtering and validation.

### 8. Israel Timezone (Asia/Jerusalem)
- Configure APScheduler with timezone `Asia/Jerusalem`.
- Accept input times in Israel local time; convert to timezone-aware datetimes on write.
- Store schedules as local hour:minute (+ optional days_of_week) and the timezone name; compare using `datetime.now(tz=Asia/Jerusalem)`.
- Server location (europe-west1) is irrelevant as long as comparisons are done with the configured timezone; DST transitions are handled by the timezone library.

### 9. Throttling and Load Control (Router-Safe Execution)
- Global cap: `MAX_CONCURRENT_SCHEDULED_TASKS` to limit simultaneous executions (e.g., 5–10 for demo).
- Per-router single-flight: ensure at most one scheduled task per `router_id` at a time (keyed in-memory locks/semaphores in the dispatcher).
- Staggering/jitter: when many tasks are due the same minute, spread dispatch with small randomized delays (e.g., 50–2000 ms) to avoid thundering herds.
- Optional per-router cooldown: `MIN_ROUTER_GAP_SECONDS` between tasks on the same router (e.g., 5s) to protect the device.
- Backoff and retry with jitter for transient failures; cap retries to keep load predictable.
- Visibility: log deferrals due to throttling and record last_run_at/last_status per task in DB.

### 10. Task Registry Mapped to Service Layer (Quick Integration)
- Maintain a task registry keyed by `service` and `task name` → functions in `backend2/services/*_service.py`.
- Service-specific group resolution:
  - Each service exposes its own `group_id → devices/targets` resolver that returns the exact format that service expects (e.g., bandwidth: IP list; AGH: device objects or MACs).
  - The scheduler’s per-task resolver delegates to the corresponding service resolver based on the `service` field (and task name), then passes other params through unchanged.
- If `params` contains `group_id`, call the service’s resolver and inject the resolved targets into the args expected by that service; otherwise pass `params` as-is.
- Keep services otherwise unchanged; the small resolver functions live within their service modules. The scheduler contains no business logic.

Example registry entry (conceptual):
- service=`bandwidth`, task=`apply_group_limits` → call: `bandwidth_service.apply_group_limits`, resolve_args: if `group_id` present → `ips = bandwidth_service.resolve_group_targets(user_id, router_id, group_id)` then map to `ips`, else expect `ips` already provided.
- service=`agh`, task=`apply_group_rules` → call: `agh_service.apply_group_rules`, resolve_args: if `group_id` present → `devices = agh_service.resolve_group_targets(user_id, router_id, group_id)` then map accordingly.

### 11. Demo Scope (3 Weeks, Quick Wins)
- Scheduling model: hour:minute (+ optional days_of_week). No complex cron editor for now.
- Fixed timezone: `Asia/Jerusalem` (no per-user timezone management yet).
- Single dispatcher in one process/instance. If multiple replicas exist, run the scheduler only on a designated instance.
- Minimal API: create/update (`/schedule-task`), list, enable/disable, delete, and "run now".
- Parameter immutability: functional params (e.g., bandwidth values, AGH categories) are immutable after creation. To change them, delete/disable and create a new scheduled task. Group membership remains dynamic by design.
- Observability: store `last_run_at`, `last_status`, and `last_error` (if any) on the `ScheduledTask` record; expose a simple listing endpoint.
- Config via env: `SCHEDULER_TIMEZONE=Asia/Jerusalem`, `MAX_CONCURRENT_SCHEDULED_TASKS`, `MIN_ROUTER_GAP_SECONDS`.

### 12. Parameter Schema (DB `params` field) — Minimal, Pass-through
- Common envelope (stored per task): `{ "user_id", "router_id", "service", "task", "params", "metadata?": { "last_known_session_id?": "..." } }`.
- Device limit apply: `params = { "ip": "1.2.3.4", "download_mbps": 5, "upload_mbps": 1 }`.
- Group limit apply (dynamic only): `params = { "group_id": 123, "download_mbps": 5, "upload_mbps": 1 }`.
- AGH group example (dynamic only): `params = { "group_id": 123, "categories": ["social_media"], "action": "block" }`.
- The resolver only adds derived fields (e.g., `ips`) when needed and never mutates the stored record.

### 13. Session Management for Scheduled Runs (No Flask `g`)
- Before executing any task, the scheduler must ensure there is an active router session for the stored `user_id`/`router_id`:
  1) Attempt to refresh an existing session if available (optional: use `metadata.last_known_session_id`).
  2) If refresh fails or no session is known, call `session_service.start_session(user_id, router_id, session_id)` to create one.
  3) Use the active `session_id` when calling the target service function.
- The scheduler maintains no long-lived reliance on request context and opens any required DB sessions directly.
- Services keep their current signatures `(user_id, router_id, session_id, ...)`.

Convention (project-specific): for this demo, `session_id` should be the same as `user_id` when starting sessions. The scheduler must pass `session_id = user_id` to `start_session` to align with existing commands-server expectations.

Execution flow per scheduled job (simplified):
1) Load task → extract `user_id`, `router_id`, `params`.
2) Ensure active session (refresh or start) → obtain `session_id`.
3) Resolve group membership if `group_id` present → inject `ips`/devices.
4) Apply throttling (global and per-router) and optional jitter.
5) Call mapped service with `(user_id, router_id, session_id, **resolved_params)`.
6) Record `last_run_at`, `last_status`, and any error; optionally update `metadata.last_known_session_id`.

## Benefits of This Approach
- Simple API surface (single scheduling endpoint).
- Scalable to many users and tasks.
- Code modularity and separation of concerns.
- Robust and easy maintenance with database-backed state.
- Efficient and concurrent task execution without blocking the server.

---

If you implement this, you’ll have a powerful, maintainable, and user-friendly dynamic scheduling system tailored for a multi-user Flask backend environment.
