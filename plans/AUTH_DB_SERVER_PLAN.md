# Authoritative Plan: Auth/DB Server with PostgreSQL

## 1. Executive Summary

This document provides the authoritative implementation plan for the **Auth/DB Server**, the central backend component of NetPilot. This server's primary roles are user authentication, session management, and persistent data storage using **PostgreSQL**.

This plan is written to be in perfect alignment with the `COMMANDS_SERVER_PLAN.md`. It explicitly details the contract and assumptions between the Auth/DB Server and the Commands-Server, ensuring a clean and robust two-service architecture. The Auth/DB server acts as the "controller" or "brains," while the Commands-Server acts as the "action executor."

As directed, this plan starts from a clean slate, with no data migration from previous TinyDB storage.

## 2. Architectural Relationship & Separation of Concerns

The backend is a two-part system with a clear division of responsibility:

| Component | Role | Technology | State | Key Responsibilities |
| :--- | :--- | :--- | :--- | :--- |
| **Auth/DB Server** | **Controller / Brains** | Python, Flask, PostgreSQL, SQLAlchemy | **Stateful** (Persistent) | User Auth, Session Logic, Data Persistence, Business Rules, API for Frontend |
| **Commands-Server** | **Action Executor / Hands** | Python, Flask, Paramiko | **Stateless** (Ephemeral Sessions) | Executes SSH commands on routers via tunnels. |

The **Auth/DB Server is the *only* client of the Commands-Server**. This is a critical architectural rule. The Commands-Server trusts the Auth/DB Server implicitly.

## 3. The Commands-Server Contract: Expectations for the Auth/DB Server

The Commands-Server is built on a set of assumptions about its client. The Auth/DB Server **must** fulfill the following contract to ensure proper functionality.

### 3.1. Session Management
- **Expectation**: The Commands-Server requires a valid `sessionId` for every API call to manage its internal connection pools. It does not know what user this session belongs to; it only knows the session exists.
- **Implementation**:
    1.  Upon successful user login, the Auth/DB Server **must** generate a unique `sessionId` (e.g., UUID).
    2.  This `sessionId` must be stored in the PostgreSQL database, linked to the `user_id`.
    3.  The Auth/DB Server **must** immediately call `POST /api/session/start` on the Commands-Server, passing the new `sessionId`.
    4.  On user logout or session expiration, the Auth/DB Server **must** call `POST /api/session/end` to allow the Commands-Server to clean up its resources.

### 3.2. Authentication & Authorization
- **Expectation**: The Commands-Server assumes all requests it receives are pre-authenticated and authorized. It performs zero validation on whether a user has permission to perform an action.
- **Implementation**:
    1.  The Auth/DB Server **must** secure its own endpoints, requiring a valid user token (e.g., JWT).
    2.  Before calling the Commands-Server, the Auth/DB Server **must** verify from its database that the authenticated user (`user_id`) owns the target `routerId`.
    3.  Any permission-based logic (e.g., "free vs. paid tier features") resides solely within the Auth/DB Server.

### 3.3. Input Validation & Data Integrity
- **Expectation**: The Commands-Server trusts that all parameters passed to it are valid and sanitized (e.g., an IP address for blocking is in a correct format).
- **Implementation**:
    1.  The Auth/DB Server is fully responsible for validating all user input from the frontend.
    2.  It should validate data formats, check for missing parameters, and enforce business rules **before** sending a command to the Commands-Server.

### 3.4. API Request Orchestration
- **Expectation**: The Commands-Server expects API calls to its command endpoints (e.g., `/api/block`, `/api/scan`) to contain both a `sessionId` and a `routerId`.
- **Implementation**:
    1.  The Auth/DB Server will house a `CommandsServerClient` class. This client will be a dedicated wrapper for making HTTP requests to the Commands-Server.
    2.  When a user requests an action, the corresponding endpoint in the Auth/DB Server will fetch the user's `sessionId` and the target `routerId` from the database.
    3.  It will then use the `CommandsServerClient` to make the downstream call, ensuring all required parameters are included.

### 3.5. Handling Responses
- **Expectation**: The Commands-Server provides structured JSON responses (`{success, data, error, metadata}`).
- **Implementation**:
    1.  The Auth/DB Server must be designed to parse this structure.
    2.  On `success: true`, it will use the `data` payload to update its PostgreSQL database (e.g., add a newly discovered device to the `user_devices` table).
    3.  On `success: false`, it will parse the `error` object and translate it into an appropriate response for the frontend, while also logging the failure.

## 4. Auth/DB Server Implementation Plan

### 4.1. PostgreSQL Database Setup
- **Technology**: PostgreSQL will be installed and configured on the VM.
- **Schema**: The multi-user schema outlined in `PHASE_2_POSTGRESQL_PLAN.md` is well-suited and will be used. It supports `user_id` and `router_id` relationships, which are essential. A `sessions` table or a `session_id` column on the `users` table will be added.
- **ORM & Migrations**: Use `SQLAlchemy` for models and `Alembic` for managing schema migrations.

### 4.2. Project Structure
```
backend/
├── api_client/
│   └── commands_server_client.py  # New client for talking to Commands-Server
├── database/
│   ├── connection.py            # PostgreSQL connection logic
│   └── session.py               # Session management
├── endpoints/
│   └── (All existing endpoints, refactored)
├── models/
│   └── (All SQLAlchemy models for PostgreSQL)
├── services/
│   └── (Services refactored to use the CommandsServerClient)
├── migrations/
│   └── (Alembic migration files)
└── server.py
```

### 4.3. Refactoring Flow (Example: Block IP)

1.  **Frontend**: `POST /api/v1/routers/{routerId}/block` with `{ip: "1.2.3.4"}` and a user auth token in the header.
2.  **Auth/DB Server (`endpoints/blacklist.py`)**:
    a. Authenticates the user via the token, retrieving their `user_id`.
    b. Queries the database to confirm the user owns `routerId`.
    c. Validates that "1.2.3.4" is a valid IP address.
    d. Retrieves the user's active `sessionId` from the database.
    e. Instantiates `CommandsServerClient`.
    f. Calls `client.block_ip(sessionId=..., routerId=..., ip="1.2.3.4")`.
3.  **CommandsServerClient**:
    a. Makes a `POST http://<commands-server-ip>:3000/api/block` request with the correct body.
4.  **Auth/DB Server (Continued)**:
    a. Receives the JSON response from the Commands-Server.
    b. If successful, it creates a new entry in the `user_blacklists` table in PostgreSQL.
    c. Relays a success message to the frontend.

## 5. Action Plan

1.  [ ] **Adopt This Plan**: This document (`AUTH_DB_SERVER_PLAN.md`) is now the single source of truth for the main backend.
2.  [ ] **Delete Obsolete Plans**: Remove `PHASE_2_DETAILED_PLAN.md` and `PHASE_2_POSTGRESQL_PLAN.md`.
3.  [ ] **Initialize Project**: Set up the PostgreSQL database, users, and permissions.
4.  [ ] **Implement Models**: Create the SQLAlchemy models for the PostgreSQL schema, including session storage.
5.  [ ] **Set up Alembic**: Configure Alembic for PostgreSQL and create the initial migration.
6.  [ ] **Build `CommandsServerClient`**: Create the dedicated client for communicating with the Commands-Server.
7.  [ ] **Implement Auth Endpoints**: Build user registration and login endpoints that handle session creation with the Commands-Server.
8.  [ ] **Refactor Service Endpoints**: Rewrite all existing endpoints to remove SSH logic and instead use the `CommandsServerClient`, orchestrating the flow and updating the database based on the results. 