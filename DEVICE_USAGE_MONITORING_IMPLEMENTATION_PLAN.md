# Device Usage Monitoring Implementation Plan

## Project Overview

Implement comprehensive device usage monitoring features for NetPilot, leveraging the existing nlbwmon (Network Load Bandwidth Monitor) tool on OpenWRT routers. This implementation follows the established 3-layer architecture pattern and Flask blueprint structure.

## Architecture Overview

### Existing Architecture Components
- **Flask Application**: Blueprint-based REST API with CORS and middleware
- **3-Layer Service Pattern**: 
  - `endpoints/` → Blueprint route handlers
  - `services/` → Business logic orchestration
  - `db_operations/` → Database interaction layer  
  - `commands_server_operations/` → Router command execution
- **RouterConnectionManager**: SSH connection pooling and session management
- **Database Layer**: PostgreSQL with session-based user management
- **OAuth Authentication**: Google OAuth with middleware verification

### Data Source: nlbwmon
- **Tool**: Network Load Bandwidth Monitor on OpenWRT
- **Data Format**: JSON/CSV export capability
- **Retention**: 35-day historical data with 24-hour commit intervals
- **Access**: Via SSH commands: `nlbw -c json`, `nlbw -c csv`

---

## Phase 1: Foundation Setup

### 1.1 Database Schema Design
[ ] Create `device_usage_monitoring` table
```sql
CREATE TABLE device_usage_monitoring (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    router_id VARCHAR(255) NOT NULL,
    device_mac VARCHAR(17) NOT NULL,
    device_name VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    bytes_downloaded BIGINT DEFAULT 0,
    bytes_uploaded BIGINT DEFAULT 0,
    total_bytes BIGINT DEFAULT 0,
    data_source VARCHAR(50) DEFAULT 'nlbwmon',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

[ ] Create `device_usage_history` table for historical data
```sql
CREATE TABLE device_usage_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    router_id VARCHAR(255) NOT NULL,
    device_mac VARCHAR(17) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_download BIGINT DEFAULT 0,
    total_upload BIGINT DEFAULT 0,
    total_usage BIGINT DEFAULT 0,
    data_points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

[ ] Create database indexes for performance
```sql
CREATE INDEX idx_device_usage_session_router ON device_usage_monitoring(session_id, router_id);
CREATE INDEX idx_device_usage_mac ON device_usage_monitoring(device_mac);
CREATE INDEX idx_device_usage_timestamp ON device_usage_monitoring(timestamp);
CREATE INDEX idx_device_history_session_router ON device_usage_history(session_id, router_id);
```

### 1.2 Core Service Layer Setup
[ ] Create `services/device_usage_service.py` - Main orchestration service
[ ] Create `db_operations/device_usage_db.py` - Database operations
[ ] Create `commands_server_operations/device_usage_execute.py` - Router command execution

### 1.3 Blueprint Endpoint Setup
[ ] Create `endpoints/device_usage.py` - REST API routes
[ ] Add device usage blueprint to `server.py`
[ ] Implement middleware integration for session verification

---

## Phase 2: Core Data Collection

### 2.1 Router Command Integration
[ ] Implement nlbwmon data retrieval functions in `device_usage_execute.py`:
  - [ ] `get_current_bandwidth_data()` - Real-time usage via `nlbw -c json`
  - [ ] `get_historical_bandwidth_data(days)` - Historical data retrieval
  - [ ] `get_device_list()` - Active device discovery
  - [ ] `validate_nlbwmon_status()` - Check if nlbwmon is running

### 2.2 Data Processing Layer
[ ] Create data parsing utilities in `utils/nlbwmon_parser.py`:
  - [ ] `parse_nlbw_json()` - Convert nlbwmon JSON to structured data
  - [ ] `normalize_device_data()` - Standardize device information
  - [ ] `calculate_usage_metrics()` - Compute bandwidth statistics
  - [ ] `identify_device_changes()` - Track new/removed devices

### 2.3 Database Operations
[ ] Implement core database functions in `device_usage_db.py`:
  - [ ] `store_device_usage_snapshot()` - Store current usage data
  - [ ] `get_device_usage_history()` - Retrieve historical data
  - [ ] `update_device_metadata()` - Update device information
  - [ ] `cleanup_old_data()` - Data retention management

---

## Phase 3: REST API Endpoints

### 3.1 Device Discovery Endpoints
[ ] `GET /api/device-usage/devices` - List all monitored devices
```json
{
  "success": true,
  "data": {
    "devices": [
      {
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": "Device Name",
        "ip": "192.168.1.100",
        "isActive": true,
        "lastSeen": "2024-01-01T12:00:00Z"
      }
    ],
    "totalDevices": 5,
    "activeDevices": 3
  }
}
```

[ ] `GET /api/device-usage/device/{mac}/info` - Get specific device information

### 3.2 Current Usage Endpoints
[ ] `GET /api/device-usage/current` - Get real-time usage for all devices
```json
{
  "success": true,
  "data": {
    "timestamp": "2024-01-01T12:00:00Z",
    "devices": [
      {
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": "Device Name",
        "bytesDown": 1048576,
        "bytesUp": 524288,
        "totalBytes": 1572864
      }
    ],
    "totalBandwidth": {
      "download": 5242880,
      "upload": 2621440,
      "total": 7864320
    }
  }
}
```

[ ] `GET /api/device-usage/device/{mac}/current` - Get current usage for specific device

### 3.3 Historical Data Endpoints
[ ] `GET /api/device-usage/history` - Get usage history for all devices
  - Query parameters: `startDate`, `endDate`, `granularity` (hour/day/week)

[ ] `GET /api/device-usage/device/{mac}/history` - Get usage history for specific device

[ ] `GET /api/device-usage/summary` - Get aggregated usage summary
```json
{
  "success": true,
  "data": {
    "period": "7days",
    "totalUsage": 10737418240,
    "averageDaily": 1534202606,
    "topDevices": [
      {
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": "Device Name",
        "usage": 3221225472,
        "percentage": 30.0
      }
    ],
    "usageTrends": {
      "increasing": ["aa:bb:cc:dd:ee:ff"],
      "stable": ["bb:cc:dd:ee:ff:aa"],
      "decreasing": ["cc:dd:ee:ff:aa:bb"]
    }
  }
}
```

---

## Phase 4: Advanced Features

### 4.1 Data Refresh and Monitoring
[ ] Implement background data collection service:
  - [ ] `services/device_usage_collector.py` - Background data collection
  - [ ] Configurable refresh intervals (5min, 15min, 30min, 1hour)
  - [ ] Error handling and retry logic
  - [ ] Data validation and consistency checks

[ ] Create monitoring endpoints:
  - [ ] `POST /api/device-usage/refresh` - Trigger manual data refresh
  - [ ] `GET /api/device-usage/status` - Get monitoring service status

### 4.2 Device Management Integration
[ ] Enhance device identification:
  - [ ] Cross-reference with existing device scanning
  - [ ] MAC address vendor lookup integration
  - [ ] Device naming and categorization
  - [ ] Historical device tracking (new/removed devices)

[ ] Create device management endpoints:
  - [ ] `PUT /api/device-usage/device/{mac}` - Update device metadata
  - [ ] `DELETE /api/device-usage/device/{mac}` - Remove device from monitoring

### 4.3 Usage Analytics
[ ] Implement analytics functions in `services/device_usage_analytics.py`:
  - [ ] `calculate_usage_trends()` - Identify usage patterns
  - [ ] `detect_anomalies()` - Unusual usage detection
  - [ ] `generate_usage_reports()` - Periodic usage summaries
  - [ ] `compare_periods()` - Period-over-period analysis

[ ] Create analytics endpoints:
  - [ ] `GET /api/device-usage/analytics/trends` - Usage trend analysis
  - [ ] `GET /api/device-usage/analytics/anomalies` - Unusual usage detection
  - [ ] `GET /api/device-usage/analytics/compare` - Period comparison

---

## Phase 5: Data Export and Reporting

### 5.1 Export Capabilities
[ ] Implement export functions in `services/device_usage_export.py`:
  - [ ] `export_to_csv()` - CSV export for Excel analysis
  - [ ] `export_to_json()` - JSON export for API integration
  - [ ] `generate_usage_report()` - PDF report generation (optional)

[ ] Create export endpoints:
  - [ ] `GET /api/device-usage/export/csv` - CSV data export
  - [ ] `GET /api/device-usage/export/json` - JSON data export
  - [ ] `POST /api/device-usage/report/generate` - Generate usage report

### 5.2 Scheduled Reporting
[ ] Implement scheduled reporting system:
  - [ ] Daily/weekly/monthly usage summaries
  - [ ] Email reporting integration (optional)
  - [ ] Usage alert system for threshold monitoring

---

## Phase 6: Testing and Validation

### 6.1 Unit Testing
[ ] Create test files following existing patterns:
  - [ ] `test_device_usage_service.py` - Service layer tests
  - [ ] `test_device_usage_db.py` - Database operation tests
  - [ ] `test_device_usage_execute.py` - Router command tests
  - [ ] `test_device_usage_endpoints.py` - API endpoint tests

### 6.2 Integration Testing
[ ] Router integration tests:
  - [ ] nlbwmon command execution validation
  - [ ] Data parsing accuracy verification
  - [ ] SSH connection stability testing
  - [ ] Error handling validation

### 6.3 Performance Testing
[ ] Database performance testing:
  - [ ] Large dataset handling
  - [ ] Query optimization validation
  - [ ] Index effectiveness testing
  - [ ] Data retention cleanup testing

---

## Phase 7: Documentation and Deployment

### 7.1 API Documentation
[ ] Create comprehensive API documentation:
  - [ ] Endpoint specifications with request/response examples
  - [ ] Error code documentation
  - [ ] Rate limiting and authentication requirements
  - [ ] Integration examples

### 7.2 Configuration Documentation
[ ] Document configuration requirements:
  - [ ] Environment variables
  - [ ] Database setup instructions
  - [ ] nlbwmon router requirements
  - [ ] Performance tuning guidelines

### 7.3 Deployment Preparation
[ ] Deployment readiness checklist:
  - [ ] Database migration scripts
  - [ ] Environment configuration templates
  - [ ] Monitoring and logging setup
  - [ ] Backup and recovery procedures

---

## Implementation Notes

### Following Existing Patterns

1. **Service Layer Pattern**: Each feature follows the established pattern:
   ```
   endpoints/device_usage.py → services/device_usage_service.py → {db_operations/, commands_server_operations/}
   ```

2. **RouterConnectionManager Integration**: All router commands use the existing SSH connection pooling system via `g.session_id` and `g.router_id`.

3. **Middleware Integration**: All endpoints use existing session verification and router context middleware.

4. **Error Handling**: Follow established error response patterns with consistent JSON structure.

5. **Logging**: Use the existing logging configuration for all components.

### Security Considerations

- [ ] Input validation for all API endpoints
- [ ] SQL injection prevention in database operations
- [ ] Rate limiting for data-intensive endpoints
- [ ] Sensitive data handling (MAC addresses, usage patterns)
- [ ] Session-based access control enforcement

### Performance Optimization

- [ ] Database query optimization with proper indexing
- [ ] Caching strategy for frequently accessed data
- [ ] Pagination for large dataset endpoints
- [ ] Background processing for data-intensive operations
- [ ] Connection pooling optimization

### Error Handling Strategy

- [ ] Graceful degradation when nlbwmon is unavailable
- [ ] Retry logic for network connectivity issues
- [ ] Data validation and sanitization
- [ ] Comprehensive error logging and monitoring
- [ ] User-friendly error messages in API responses

---

## Success Criteria

### Functional Requirements
✅ **Device Discovery**: Automatically identify and track network devices
✅ **Usage Monitoring**: Collect and store bandwidth usage data per device
✅ **Historical Analysis**: Provide historical usage data and trends
✅ **Real-time Data**: Offer current usage information
✅ **Data Export**: Enable data export in multiple formats

### Technical Requirements
✅ **Architecture Compliance**: Follow established 3-layer service pattern
✅ **Performance**: Handle multiple concurrent users without degradation
✅ **Reliability**: 99%+ uptime with proper error handling
✅ **Scalability**: Support growing number of devices and data points
✅ **Security**: Maintain session-based access control and data protection

### Integration Requirements
✅ **Router Compatibility**: Work with existing nlbwmon setup
✅ **Database Integration**: Seamless PostgreSQL integration
✅ **API Consistency**: Match existing API patterns and conventions
✅ **Authentication**: Integrate with existing OAuth system
✅ **Monitoring**: Comprehensive logging and error tracking

This implementation plan provides a comprehensive roadmap for adding device usage monitoring capabilities to NetPilot while maintaining architectural consistency and following established patterns.
