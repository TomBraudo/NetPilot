# Detailed Plan: Auth/DB Server - Database Implementation

## 1. Objective

This document provides a detailed, step-by-step implementation plan for the **PostgreSQL database** component of the Auth/DB Server. Its primary purpose is to serve as a practical guide, ensuring the database is built in perfect alignment with the architectural requirements outlined in `plans/AUTH_DB_SERVER_PLAN.md`.

This plan covers database setup, project structure, data modeling with SQLAlchemy, and the specific implementation patterns required to support the Commands-Server contract.

## 2. Core Database Requirements from `AUTH_DB_SERVER_PLAN.md`

- [ ] **Session Management**: The database must persistently store `sessionId` values, linking them directly to a `user_id`.
- [ ] **Authorization**: The schema must enforce and allow for easy verification of resource ownership.
- [ ] **Data Persistence**: The database is the single source of truth for all user-related data.

---

## **Phase 1: PostgreSQL Setup on VM**

### 1.1. Install PostgreSQL Packages
- [ ] Connect to the target VM via SSH.
- [ ] Run `sudo apt update && sudo apt upgrade -y` to update system packages.
- [ ] Install PostgreSQL and its client libraries: `sudo apt install postgresql-15 postgresql-client-15 postgresql-contrib-15 -y`.
- [ ] Start and enable the PostgreSQL service: `sudo systemctl start postgresql` and `sudo systemctl enable postgresql`.

### 1.2. Create Database and User
- [ ] Switch to the `postgres` system user: `sudo -u postgres psql`.
- [ ] Create the application database: `CREATE DATABASE netpilot_db;`.
- [ ] Create the application user with a secure password: `CREATE USER netpilot_user WITH ENCRYPTED PASSWORD 'a_very_secure_password';`.
- [ ] Grant all necessary privileges to the new user: `GRANT ALL PRIVILEGES ON DATABASE netpilot_db TO netpilot_user;`.
- [ ] Connect to the new database (`\c netpilot_db`) and enable the UUID extension: `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`.

### 1.3. Configure Network and Authentication
- [ ] Edit `postgresql.conf` (`sudo nano /etc/postgresql/15/main/postgresql.conf`) to set `listen_addresses = 'localhost'`.
- [ ] Edit `pg_hba.conf` (`sudo nano /etc/postgresql/15/main/pg_hba.conf`) to ensure `md5` authentication is required for `netpilot_user` from `127.0.0.1/32`.
- [ ] Restart the PostgreSQL service to apply all configuration changes: `sudo systemctl restart postgresql`.

---

## **Phase 2: Project Structure & Dependencies**

### 2.1. Update Python Dependencies
- [ ] Add `SQLAlchemy` to `backend/requirements.txt`.
- [ ] Add `alembic` to `backend/requirements.txt`.
- [ ] Add `psycopg2-binary` to `backend/requirements.txt` for PostgreSQL connectivity.
- [ ] Add `python-decouple` to `backend/requirements.txt` for managing environment variables.

### 2.2. Verify Directory Structure
- [ ] Confirm `backend/database/` directory for connection logic.
- [ ] Confirm `backend/models/` directory for SQLAlchemy models.
- [ ] Confirm `backend/migrations/` directory for Alembic scripts.
- [ ] Create `backend/api_client/` directory for the Commands-Server client.

---

## **Phase 3: SQLAlchemy Model Implementation**

### 3.1. Create Base Model
- [ ] Create `models/base.py` with an abstract `BaseModel` containing common columns: `id`, `created_at`, `updated_at`.

### 3.2. Create Core User and Session Models
- [ ] Implement `models/user_session.py` to store `user_id`, a unique `session_id`, and an `expires_at` timestamp. This is critical for the Commands-Server contract.
- [ ] Implement `models/user.py` with fields like `email` and `password_hash`. Add the reverse relationship `sessions` to link to the `UserSession` model.

### 3.3. Create Remaining Data Models
- [ ] Implement `models/router.py` to represent the `user_routers` table, linking users and their routers.
- [ ] Implement `models/device.py` for the `user_devices` table.
- [ ] Implement `models/whitelist.py` and `models/blacklist.py` for their respective tables.

---

## **Phase 4: Alembic Migration**

### 4.1. Configure Alembic Environment
- [ ] Edit `alembic.ini` to securely load the database URL from environment variables.
- [ ] Edit `migrations/env.py` to import all models from the `backend/models/` directory so Alembic can detect schema changes.
- [ ] Set `target_metadata = Base.metadata` in `env.py`.

### 4.2. Generate and Apply Initial Schema
- [ ] Set the required database connection environment variables (`DB_USER`, `DB_PASS`, `DB_HOST`, `DB_NAME`).
- [ ] From the `backend/` directory, run `alembic revision --autogenerate -m "Initial schema creation"` to generate the first migration script.
- [ ] Manually review the generated script to ensure it matches the models correctly.
- [ ] Run `alembic upgrade head` to apply the new schema to the PostgreSQL database.

---

## **Phase 5: Building the Commands-Server API Client**

### 5.1. Implement the Client Class
- [ ] Create the file `api_client/commands_server_client.py`.
- [ ] Implement the `CommandsServerClient` class. Its `__init__` method must require a `session_id` and `router_id` to ensure all operations are properly contextualized.
- [ ] Implement a private `_make_request` method. This method is responsible for all HTTP calls, centralizing error handling (e.g., for timeouts), and automatically injecting the `sessionId` and `routerId` into every outgoing request payload or its query parameters.

### 5.2. Implement Client Methods
- [ ] For each router operation, add a corresponding public method to the client. These methods should be simple and accept only the specific arguments for that command.
- [ ] **Minimal Example:**
    ```python
    # In CommandsServerClient class
    def block_ip(self, ip_to_block: str):
        """Requests the Commands-Server to block an IP."""
        # The internal _make_request method handles adding session/router context
        return self._make_request('POST', '/blacklist', payload={'ip': ip_to_block})

    def get_scanned_devices(self):
        """Requests the list of scanned devices."""
        # No extra payload is needed; context is added automatically
        return self._make_request('GET', '/scan')
    ```

---

## **Phase 6: Service Layer Orchestration (Corrected)**

### 6.1. Refactor Services to Orchestrate
- [ ] Modify all backend services (e.g., `blacklist_service.py`) to remove direct SSH logic. Their new role is to coordinate between the API endpoint and the Commands-Server.

### 6.2. Core Orchestration Pattern
- [ ] Inside each service function, the logic should be:
    1.  Get the user's active `session_id` from the database.
    2.  Instantiate the `CommandsServerClient` with the session and router context.
    3.  Call the client's high-level method.
    4.  Process the response to update the database and return a result.
- [ ] **Minimal Example:**
    ```python
    # In a service method, e.g., in blacklist_service.py
    def add_device_to_blacklist(self, user_id, router_id, ip_to_block, ...):
        session_id = get_active_session_id(db, user_id)
        api_client = CommandsServerClient(session_id=session_id, router_id=router_id)
        
        # Simple, clean call to the client
        response = api_client.block_ip(ip_to_block)

        # ... process response and update database (see Phase 7) ...
    ```

---

## **Phase 7: Response Handling and Data Persistence (Corrected)**

### 7.1. Implement Response Processing Logic
- [ ] For every service call, check the `success` flag in the response from the Commands-Server.
- [ ] On `success: false`, log the `error` object and return an appropriate error to the user. **The database state should not be changed.**
- [ ] On `success: true`, parse the `data` object to persist the results.

### 7.2. Pattern for Data Persistence
- [ ] **For simple commands** (e.g., `block_ip`), the `success` flag is confirmation. The Auth/DB server can then create its own record in the corresponding table (e.g., `user_blacklists`).
- [ ] **For data-rich commands** (e.g., `get_scanned_devices`), the `data` payload contains the information to be persisted. Use an efficient "upsert" pattern to sync this data with the database.
- [ ] **Minimal "Upsert" Example for Scan Results:**
    ```python
    # On successful scan response
    scan_data = response.get('data', [])
    if not scan_data:
        return # Nothing to do

    # Use a modern SQLAlchemy "upsert" statement
    from sqlalchemy.dialects.postgresql import insert
    
    devices_to_upsert = [
        {'user_id': user_id, 'router_id': router_id, 'ip': dev['ip'], 'mac': dev['mac'], ...}
        for dev in scan_data
    ]
    
    stmt = insert(UserDevice).values(devices_to_upsert)
    stmt = stmt.on_conflict_do_update(
        index_elements=['user_id', 'router_id', 'ip'], # Assumes a UNIQUE constraint
        set_={'last_seen': func.current_timestamp()}
    )
    db_session.execute(stmt)
    ```

This plan provides a clear and actionable path to building the database component correctly, ensuring it seamlessly integrates with the Commands-Server as intended by the master architectural plan. 


