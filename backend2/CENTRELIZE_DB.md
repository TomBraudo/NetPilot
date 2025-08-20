### Centralized DB Session and Transaction Management

Goal: One authoritative place manages SQLAlchemy sessions and transactions for both HTTP requests and scheduler jobs. DB ops never commit/rollback; transaction decision is centralized.

### Components
- **`managers/db_session_context.py`**
  - Context utility backed by contextvars to hold the current SQLAlchemy session.
  - API: `set(session)`, `get() -> Session | None`, `clear()`.
  - Optional helpers: `with_session(session)` contextmanager, `@with_session` decorator (do not manage commits here).

- **`managers/transaction_manager.py`**
  - Central policy for begin/commit/rollback/close.
  - Web API:
    - `begin_request()` → create session, `SessionContext.set(session)`.
    - `finalize_response(response)` → commit on success, rollback on error.
    - `teardown()` → close and `SessionContext.clear()`.
  - Scheduler API:
    - `run(fn)` → create session, set context, call `fn`, commit if success, rollback on error/exception, always close+clear.

### Rules of use
- DB operation modules must call `SessionContext.get()` to obtain the active session; never open/commit/close themselves.
- Services return `(data, error)` and can use `session.flush()` (no commit) when IDs are needed.
- Endpoints are thin; only parse inputs and call services. No direct DB commits.
- Scheduler wraps each task execution with `TransactionManager.run(...)`.

---

### Migration Plan (Phased)

#### Phase 1 — Introduce centralized infrastructure
- [x] Create `managers/db_session_context.py` with contextvars-based storage and helpers
- [x] Create `managers/transaction_manager.py` implementing Web and Scheduler APIs

#### Phase 2 — Wire HTTP lifecycle
- [x] In `backend2/server.py` use TransactionManager:
  - [x] `before_request` → `begin_request()`
  - [x] `after_request` → `finalize_response(response)`
  - [x] `teardown_request` → `teardown()`
- [x] Remove any direct per-handler commits/rollbacks (keep a single decision point)

#### Phase 3 — Make DB ops context-driven
- [x] Replace uses of `g.db_session` and `get_db_session()` inside `services/db_operations/**` with `SessionContext.get()`
- [x] Ensure all DB ops avoid commit/close and use `session.flush()` only when necessary
- [x] If no active session in context, raise a clear error (to catch miswired paths)

#### Phase 4 — Scheduler integration
- [ ] In dispatcher, wrap each due task with `TransactionManager.run(lambda: service_call(...))`
- [ ] Treat service convention `(data, error)` as success flag: commit when `error is None`, else rollback

#### Phase 5 — Clean-up and convergence
- [ ] Sweep endpoints/services to remove any remaining session creation or manual commit/rollback
- [ ] Ensure all DB access goes through `SessionContext.get()` only
- [ ] Keep Flask `g` strictly for request metadata (e.g., `g.user_id`, `g.router_id`, `g.session_id`)

#### Phase 6 — Validation
- [ ] Smoke-test web endpoints: verify success commits and errors rollback
- [ ] Test scheduler path: one success task (commit persists), one failing task (rollback + any compensations)

---

### Notes
- Unifies web and scheduler transaction handling without relying on Flask `g` for DB sessions.
- Maintains a single, auditable transaction boundary and keeps services/DB ops simple.

