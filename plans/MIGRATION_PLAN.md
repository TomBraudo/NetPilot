# NetPilot Cloud Migration Plan

## Executive Summary

This plan outlines the migration of NetPilot's backend and frontend from localhost deployment to a cloud-based architecture that leverages the existing agent-to-VM tunnel infrastructure.

## Current Architecture (What Works)

### ✅ Existing Components
- **Agent (Electron App)**: ✅ Successfully establishes reverse SSH tunnels from routers to cloud VM
- **Cloud VM (34.38.207.87)**: ✅ Port-manager running, handling dynamic port allocation (2200-2299)
- **Tunnel Infrastructure**: ✅ Verified end-to-end tunnel connectivity with credential management
- **Router Setup**: ✅ Agent automatically installs required packages and configures routers

### Current Flow (Localhost)
```
Frontend (localhost) → Backend (localhost) → Direct SSH → Router
```

### Working Infrastructure
- VM IP: `34.38.207.87`
- Port Manager API: `http://34.38.207.87:8080`
- Tunnel Port Range: `2200-2299`
- Agent Status API: Provides router credentials with tunnel information

## Target Architecture (Cloud)

### New Flow
```
Frontend (Cloud) → Backend (Cloud) → Commands-Server (VM) → Port Manager (VM) → SSH via Tunnel → Router
```

### Architecture Components
1. **Frontend**: React app deployed to cloud with domain
2. **Backend**: Flask API deployed to cloud (handles authentication + user databases)
3. **Commands-Server**: New service on VM that executes NetPilot commands via tunnels
4. **Port Manager**: Existing service for tunnel routing and credential management
5. **Central Database**: Multi-user database replacing individual TinyDB instances
6. **Agent**: Unchanged, continues to manage tunnels

## Migration Guidelines

1. **Test Before Implementing**: Validate each component in isolation before integration
2. **Systematic Work**: Use sequential thinking to break down complex tasks
3. **Careful Edits**: Always gain context before modifying existing code
4. **Preserve Logic**: Keep current logical structure, only modify for cloud compatibility

## Migration Phases

## Phase 1: Commands-Server Development
**Goal**: Create the VM-based commands server that routes NetPilot operations via tunnels

### 1.1 Commands-Server Design & API Contract
- [ ] Design Commands-Server API specification
  - [ ] Define endpoints matching current backend API (scan, block, unblock, etc.)
  - [ ] Design router identification mechanism (routerId/tunnelPort)
  - [ ] Plan authentication/authorization flow
- [ ] Create `commands-server` directory structure on VM
- [ ] Set up Node.js/Express server framework
- [ ] Implement basic health check and port routing logic

### 1.2 Router Communication via Tunnels  
- [ ] Implement SSH connection management using tunnel ports
- [ ] Create router command execution module
- [ ] Integrate with existing port-manager for credential retrieval
- [ ] Test basic command routing (uci commands, network scans)

### 1.3 NetPilot Operations Implementation
- [ ] Port network scanning functionality
- [ ] Port device blocking/unblocking operations  
- [ ] Port whitelist/blacklist management
- [ ] Port WiFi management operations
- [ ] Port speed test functionality
- [ ] Port configuration management

### 1.4 Testing & Validation
- [ ] Create test suite for Commands-Server
- [ ] Test with real tunnel connections
- [ ] Validate command execution latency
- [ ] Verify error handling and timeouts

## Phase 2: Database Design & Setup
**Goal**: Design and implement centralized multi-user SQLite3 database with SQLAlchemy and Alembic

### 2.1 SQLite3 Database Architecture
- [ ] **Database File Structure Design**
  - [ ] Plan database file location: `/app/data/netpilot.db`
  - [ ] Design backup strategy for SQLite file
  - [ ] Plan container volume mounting for data persistence
  - [ ] Consider database file locking and concurrent access patterns
- [ ] **Development vs Production Setup**
  - [ ] Development: Local SQLite file in project directory
  - [ ] Production: SQLite file in persistent Docker volume
  - [ ] Testing: In-memory SQLite database for fast tests
- [ ] **Backup & Recovery Strategy**
  - [ ] Automated daily backups of SQLite file to Cloud Storage
  - [ ] Implement backup rotation policy (keep 30 days)
  - [ ] Create restore procedures and test them
  - [ ] Plan for database corruption recovery

### 2.2 Database Schema Design & Documentation
- [ ] **Enhanced Schema Design**
  - [ ] Create detailed Entity Relationship Diagram (ERD)
  - [ ] Define all indexes for performance optimization (SQLite supports indexes)
  - [ ] Plan foreign key constraints and cascading rules
  - [ ] Design audit trail tables for security compliance
  - [ ] Optimize schema for SQLite's characteristics (no complex joins)
- [ ] **SQLite Performance Considerations**
  - [ ] Index strategy for common queries (user_id, router_id lookups)
  - [ ] Plan for SQLite's single-writer limitation
  - [ ] Consider using WAL mode for better concurrent reads
  - [ ] Define query performance benchmarks for SQLite
  - [ ] Plan transaction boundaries to minimize lock time

### 2.4 SQLAlchemy ORM Setup
- [ ] **Project Structure Setup**
  - [ ] Create `models/` directory structure:
    ```
    backend/models/
    ├── __init__.py
    ├── base.py          # Base model class
    ├── user.py          # User model
    ├── router.py        # Router model
    ├── device.py        # Device models
    ├── whitelist.py     # Whitelist model
    ├── blacklist.py     # Blacklist model
    └── settings.py      # User settings model
    ```
- [ ] **SQLAlchemy Configuration**
  - [ ] Install dependencies: `sqlalchemy`, `sqlalchemy-utils` (no psycopg2 needed for SQLite)
  - [ ] Create database connection configuration for different environments
  - [ ] Configure SQLite-specific settings (WAL mode, foreign keys, etc.)
  - [ ] Configure session management with proper scoping
  - [ ] Implement database URL construction for SQLite (`sqlite:///path/to/db.sqlite`)
- [ ] **Model Implementation**
  - [ ] Create base model with common fields (id, created_at, updated_at)
  - [ ] Implement all models with proper relationships
  - [ ] Add model validators and constraints
  - [ ] Create model mixins for common functionality
  - [ ] Implement soft delete functionality where appropriate

### 2.5 Alembic Migration System Setup
- [ ] **Alembic Initialization**
  - [ ] Install Alembic: `pip install alembic`
  - [ ] Initialize Alembic in project: `alembic init migrations`
  - [ ] Configure `alembic.ini` for multiple environments
  - [ ] Set up `env.py` to work with SQLAlchemy models
  - [ ] Configure migration templates and naming conventions
- [ ] **Migration Environment Setup**
  - [ ] Create migration configurations for:
    - [ ] Development database (local SQLite file)
    - [ ] Testing database (in-memory SQLite)
    - [ ] Production database (persistent volume SQLite)
  - [ ] Set up environment-specific database file paths
  - [ ] Configure SQLite pragmas and connection parameters per environment
- [ ] **Initial Migration Creation**
  - [ ] Generate initial migration: `alembic revision --autogenerate -m "Initial schema"`
  - [ ] Review and customize auto-generated migration
  - [ ] Test migration on development database
  - [ ] Create rollback procedures and test them

### 2.6 SQLite Connection & Security
- [ ] **Connection Management**
  - [ ] Configure SQLite connection with proper settings
  - [ ] Enable WAL mode for better concurrent reads
  - [ ] Set appropriate SQLite pragmas (foreign_keys=ON, journal_mode=WAL)
  - [ ] Implement file locking and error handling
- [ ] **File Security & Permissions**
  - [ ] Set proper file permissions on SQLite database file
  - [ ] Ensure database file is in secure container volume
  - [ ] Implement file-level backup encryption
  - [ ] Plan for database file integrity checks
- [ ] **Container Volume Management**
  - [ ] Configure persistent Docker volumes for database file
  - [ ] Set up volume backup strategy
  - [ ] Plan for volume migration and scaling
  - [ ] Implement database file corruption detection

### 2.7 Database Testing & Validation
- [ ] **Testing Framework Setup**
  - [ ] Create test database configuration
  - [ ] Set up pytest fixtures for database testing
  - [ ] Implement test data factories using Factory Boy
  - [ ] Create database seeding scripts for development
- [ ] **Migration Testing**
  - [ ] Test all migrations forward and backward
  - [ ] Validate data integrity after migrations
  - [ ] Performance test migrations with large datasets
  - [ ] Create migration rollback procedures


## Phase 3: Backend Cloud Migration
**Goal**: Enhance Flask backend with authentication, user management, and Commands-Server integration

### 3.1 Authentication & User Management
- [ ] Implement user registration and login system
- [ ] Create JWT or session-based authentication
- [ ] Add password hashing and security measures
- [ ] Implement user profile management
- [ ] Create router-to-user association system

### 3.2 Database Integration
- [ ] Replace TinyDB with centralized database
- [ ] Implement user-scoped data access
- [ ] Add user data isolation and validation
- [ ] Create user-specific configuration management
- [ ] Implement multi-tenant data security

### 3.3 Commands-Server Integration  
- [ ] Create `CommandsServerClient` class
- [ ] Implement router identification via user session
- [ ] Add Commands-Server API client with authentication
- [ ] Route NetPilot commands through Commands-Server
- [ ] Implement command result caching and optimization

### 3.4 API Endpoint Updates
- [ ] Update all endpoints in `endpoints/` directory for user-scoped data
- [ ] Add authentication middleware to all protected endpoints
- [ ] Modify error handling for remote command execution
- [ ] Add latency and timeout handling for Commands-Server calls
- [ ] Update response formats for cloud deployment

### 3.5 Backend Testing
- [ ] Create integration tests with Commands-Server
- [ ] Test all API endpoints with tunnel routing
- [ ] Validate authentication and session flows
- [ ] Test multi-user data isolation
- [ ] Performance testing with tunnel latency

## Phase 4: Frontend Cloud Preparation  
**Goal**: Prepare the React frontend for cloud deployment

### 4.1 Configuration Updates
- [ ] Update API base URLs from localhost to cloud backend
- [ ] Configure environment variables for different deployments
- [ ] Add production build optimizations
- [ ] Update CORS configuration

### 4.2 Authentication Integration
- [ ] Add login/authentication components
- [ ] Implement user registration and profile management
- [ ] Add session management to frontend
- [ ] Create router credential input flow (agent integration)
- [ ] Create router selection interface (multi-router support)

### 4.3 UI/UX Enhancements
- [ ] Add connection status indicators
- [ ] Implement tunnel latency display
- [ ] Add cloud-specific error handling
- [ ] Create user onboarding wizard
- [ ] Add user-specific data views (personal whitelist/blacklist)

### 4.4 Build & Deployment Preparation
- [ ] Configure Vite for production builds
- [ ] Optimize bundle size and performance
- [ ] Add environment-specific configurations
- [ ] Prepare static asset handling

## Phase 5: Infrastructure & Deployment
**Goal**: Deploy all components to cloud infrastructure

### 5.1 Container Volume & Backup Setup
- [ ] **Docker Volume Configuration**
  - [ ] Create persistent volume for SQLite database file
  - [ ] Configure volume mounting in Flask container
  - [ ] Set proper volume permissions and ownership
  - [ ] Test volume persistence across container restarts
- [ ] **Backup Infrastructure**
  - [ ] Set up automated SQLite backup to Cloud Storage
  - [ ] Create backup scripts with compression and encryption
  - [ ] Configure backup scheduling (daily backups, 30-day retention)
  - [ ] Test backup and restore procedures
- [ ] **Monitoring & Alerting**
  - [ ] Monitor database file size and growth
  - [ ] Set up alerts for backup failures
  - [ ] Monitor container disk usage
  - [ ] Create alerts for SQLite corruption or lock errors

### 5.2 VM Configuration
- [ ] Deploy Commands-Server to VM (`/opt/netpilot-commands-server`)
- [ ] Configure PM2 for Commands-Server service management  
- [ ] Set up firewall rules for Commands-Server port
- [ ] Test Commands-Server with existing port-manager

### 5.3 GCP Cloud Deployment Setup
- [ ] Set up GCP project and billing
- [ ] Configure Compute Engine instances for backend
- [ ] Set up Cloud Storage for static frontend assets
- [ ] Configure networking and firewall rules

### 5.4 Backend Deployment
- [ ] Create Docker container for Flask backend with SQLite
- [ ] Configure Dockerfile with proper volume mounting for database
- [ ] Deploy to GCP Compute Engine or Cloud Run
- [ ] Set up persistent volumes for SQLite database file
- [ ] Configure environment variables for Commands-Server integration
- [ ] Configure logging and monitoring

### 5.5 Frontend Deployment
- [ ] Build production frontend bundle
- [ ] Deploy to GCP Cloud Storage + CDN or Cloud Run
- [ ] Configure custom domain and SSL certificates
- [ ] Set up CDN for global performance

### 5.6 Domain & SSL Configuration
- [ ] Configure DNS for custom domain
- [ ] Set up SSL certificates (Let's Encrypt or Google-managed)
- [ ] Configure load balancing (if needed)
- [ ] Test end-to-end HTTPS connectivity

## Phase 6: Integration & Testing
**Goal**: Validate the complete cloud deployment

### 6.1 End-to-End Testing
- [ ] Test complete user flow: Agent → Cloud Frontend → Backend → Commands-Server → Router
- [ ] Validate all NetPilot operations in cloud environment
- [ ] Test with multiple concurrent users/routers
- [ ] Test multi-user data isolation and security
- [ ] Performance and latency validation

### 6.2 Security Validation
- [ ] Test authentication and authorization
- [ ] Validate user data isolation in database
- [ ] Test tunnel security and isolation
- [ ] Test SSL/TLS configuration
- [ ] Security audit of Commands-Server and database access

### 6.3 Monitoring & Logging
- [ ] Set up application monitoring
- [ ] Configure centralized logging
- [ ] Add performance metrics collection
- [ ] Set up alerting for critical issues
- [ ] Monitor database performance and connections

## Technical Specifications

### Database Schema Design
```sql
-- Users and Authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Router registrations per user
CREATE TABLE user_routers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    router_id VARCHAR(255) NOT NULL, -- From agent tunnel
    router_name VARCHAR(255),
    router_ip VARCHAR(45), -- IPv4/IPv6
    tunnel_port INTEGER,
    cloud_vm_ip VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(user_id, router_id)
);

-- User-specific device whitelists
CREATE TABLE user_whitelists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    router_id VARCHAR(255) REFERENCES user_routers(router_id),
    device_ip VARCHAR(45) NOT NULL,
    device_mac VARCHAR(17),
    device_name VARCHAR(255),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, router_id, device_ip)
);

-- User-specific device blacklists
CREATE TABLE user_blacklists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    router_id VARCHAR(255) REFERENCES user_routers(router_id),
    device_ip VARCHAR(45) NOT NULL,
    device_mac VARCHAR(17),
    device_name VARCHAR(255),
    reason VARCHAR(500),
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, router_id, device_ip)
);

-- User-specific device registry
CREATE TABLE user_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    router_id VARCHAR(255) REFERENCES user_routers(router_id),
    ip VARCHAR(45) NOT NULL,
    mac VARCHAR(17),
    hostname VARCHAR(255),
    device_type VARCHAR(100),
    manufacturer VARCHAR(255),
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, router_id, ip)
);

-- User preferences and settings
CREATE TABLE user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    UNIQUE(user_id, setting_key)
);
```

### Commands-Server API Design
```javascript
// Base URL: http://34.38.207.87:3000/api

// Router identification via routerId or tunnelPort
POST /commands/execute
{
  "routerId": "router-uuid-here",
  "command": "uci show network",
  "timeout": 30000
}

// NetPilot operations
POST /network/scan?routerId=router-uuid
POST /network/block?routerId=router-uuid
POST /network/unblock?routerId=router-uuid
GET /network/blocked?routerId=router-uuid
POST /network/reset?routerId=router-uuid
GET /network/speedtest?routerId=router-uuid

// Integration with port-manager
GET /routers/active  // List active tunnels
GET /routers/:routerId/status  // Tunnel status
```

### Backend Configuration Changes
```python
# Enhanced backend architecture with SQLite
from sqlalchemy import create_engine
from flask_jwt_extended import JWTManager
import os

class NetPilotCloudBackend:
    def __init__(self):
        # SQLite database connection
        db_path = os.getenv('DATABASE_PATH', '/app/data/netpilot.db')
        self.db_url = f'sqlite:///{db_path}'
        
        # Configure SQLite with WAL mode and foreign keys
        self.engine = create_engine(
            self.db_url,
            connect_args={
                'check_same_thread': False,  # Allow multi-threading
                'timeout': 20  # 20 second timeout for locks
            },
            pool_pre_ping=True  # Verify connections
        )
        
        # Enable SQLite features
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
        
        # Commands-Server integration
        self.commands_server_url = os.getenv('COMMANDS_SERVER_URL', 'http://34.38.207.87:3000')
        self.session = requests.Session()
        
        # JWT authentication
        self.jwt = JWTManager()
    
    def execute_router_command(self, user_id, router_id, command):
        # 1. Validate user owns this router
        # 2. Route command through Commands-Server
        # 3. Store results in user database if needed
        pass
    
    def get_user_data(self, user_id, data_type):
        # Retrieve user-specific whitelist/blacklist/devices
        pass

# User authentication middleware
@jwt_required()
def protected_endpoint():
    current_user = get_jwt_identity()
    # All endpoints now user-scoped

# Docker configuration
# Dockerfile:
# VOLUME ["/app/data"]  # Persistent volume for SQLite
# ENV DATABASE_PATH=/app/data/netpilot.db
```

### Frontend Environment Configuration
```javascript
// config/environment.js
const config = {
  development: {
    API_BASE_URL: 'http://localhost:5000',
  },
  production: {
    API_BASE_URL: 'https://api.your-domain.com',
  }
};
```

## Risk Mitigation

### Technical Risks
- **Tunnel Latency**: Commands may be slower via tunnel - implement timeouts and user feedback
- **Connection Reliability**: Handle tunnel disconnections gracefully with retry logic
- **Security**: Ensure proper authentication and router isolation in cloud environment

### Migration Risks  
- **Service Downtime**: Plan for phased rollout with ability to rollback to localhost
- **Data Migration**: Ensure user data and configurations are preserved
- **Agent Compatibility**: Verify agent continues to work with new cloud backend

## Success Criteria

### Phase 1 Complete
- [ ] Commands-Server successfully executes router commands via tunnels
- [ ] All NetPilot operations work through Commands-Server
- [ ] Performance meets acceptable thresholds (<2s for most operations)

### Phase 2 Complete  
- [ ] Backend successfully communicates with Commands-Server
- [ ] All existing API endpoints work in cloud mode
- [ ] Authentication and session management functional

### Phase 3 Complete
- [ ] Frontend builds and deploys successfully
- [ ] All UI features work with cloud backend
- [ ] User authentication flow complete

### Phase 4 Complete
- [ ] All services deployed and accessible via custom domain
- [ ] SSL certificates configured and working
- [ ] Monitoring and logging operational

### Final Success
- [ ] End-to-end user flow: Agent setup → Cloud access → Router control
- [ ] Performance meets or exceeds localhost experience
- [ ] Multiple users can operate independently
- [ ] System is secure and scalable

## Deployment Architecture

```
Internet
    ↓
[Custom Domain] → [Cloud Load Balancer]
    ↓                       ↓
[Frontend CDN]         [Backend API]
                           ↓
                    [Commands-Server on VM]
                           ↓
                    [Port Manager on VM]
                           ↓
                    [SSH Tunnels (2200-2299)]
                           ↓
                    [Individual Routers]
```

## Timeline Estimate

- **Phase 1**: 2-3 weeks (Commands-Server development)
- **Phase 2**: 2-3 weeks (Database design & setup)
- **Phase 3**: 3-4 weeks (Backend migration with authentication & database)  
- **Phase 4**: 1-2 weeks (Frontend preparation)
- **Phase 5**: 1-2 weeks (Infrastructure deployment)
- **Phase 6**: 1 week (Integration testing)

**Total**: 10-15 weeks for complete migration

## Next Steps

1. **Immediate**: Start Phase 1.1 - Commands-Server API design
2. **Parallel**: Begin Phase 2.1 - Database schema design
3. **Validate**: Test existing agent tunnel functionality
4. **Plan**: Detailed technical specifications for both Commands-Server and database
5. **Develop**: Begin Commands-Server implementation with systematic testing

## Enhanced Architecture Benefits

With this improved architecture, the Flask backend becomes a powerful central hub:

- **User Management**: Complete authentication and authorization system
- **Data Sovereignty**: Each user has isolated, secure data storage
- **Multi-Router Support**: Users can manage multiple routers independently  
- **Scalability**: Database handles concurrent users efficiently
- **Audit Trail**: Complete logging of user actions and router commands
- **Business Logic**: Centralized location for NetPilot business rules
- **Caching**: Intelligent caching of router data and command results

This transforms the backend from a simple proxy into a comprehensive multi-tenant NetPilot management platform. 