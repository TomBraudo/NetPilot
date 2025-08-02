# Device Usage Monitoring Implementation Plan - Commands Server

## Project Overview

Implement device usage monitoring features for the NetPilot Commands Server by leveraging the existing nlbwmon (Network Load Bandwidth Monitor) tool on OpenWRT routers. This commands server executes SSH commands and returns raw data - no database storage, just direct router command execution.

## Architecture Overview

### Commands Server Role
- **Purpose**: Execute SSH commands on routers and return raw results
- **Data Source**: nlbwmon running on OpenWRT routers (35-day retention, JSON/CSV output)
- **No Database**: All data remains on the router filesystem
- **Session Management**: Via RouterConnectionManager with sessionId/routerId context
- **Command Execution**: Direct SSH via `router_connection_manager.execute()`

### Existing Architecture Pattern
```
Endpoints (blueprints) → Services → RouterConnectionManager.execute() → SSH Commands → Router Response
```

### nlbwmon Data Access
- **Tool**: Network Load Bandwidth Monitor on OpenWRT
- **Commands**: `nlbw -c json`, `nlbw -c csv`, `nlbw -z` (reset)
- **Data Format**: JSON with device MAC, IP, bytes up/down, time periods
- **Storage**: Router filesystem `/tmp/nlbw.db` (SQLite)
- **Historical Data**: 35-day retention with 24-hour commit intervals

---

## Phase 1: Core Command Execution Service

### 1.1 Create Device Usage Service
[x] Create `services/device_usage_service.py` following existing service patterns:
  - [x] `get_current_device_usage()` - Execute `nlbw -c json` for current data
  - [x] `get_historical_device_usage(days=7)` - Get historical usage data
  - [x] `get_device_usage_summary()` - Get aggregated usage per device
  - [x] `reset_usage_counters()` - Execute `nlbw -z` to reset counters
  - [x] `check_nlbwmon_status()` - Verify nlbwmon is running

### 1.2 Router Command Implementations
[x] Implement nlbwmon command wrappers:

```python
def get_current_device_usage():
    """Get current device usage via nlbw JSON output."""
    try:
        # Get current usage data
        output, error = router_connection_manager.execute("nlbw -c json")
        if error:
            return None, f"Command failed: {error}"
        
        # Parse and return JSON data
        import json
        usage_data = json.loads(output)
        return usage_data, None
    except Exception as e:
        return None, str(e)
```

### 1.3 Data Processing Utilities
[ ] Create `utils/nlbwmon_parser.py` for data processing:
  - [x] `parse_nlbw_json()` - Parse nlbwmon JSON output
  - [x] `format_device_usage()` - Format device usage data
  - [x] `calculate_totals()` - Calculate bandwidth totals
  - [x] `filter_by_timeframe()` - Filter data by time periods

---

## Phase 2: REST API Endpoints

### 2.1 Create Device Usage Blueprint
[ ] Create `endpoints/device_usage.py` following existing endpoint patterns:

```python
from flask import Blueprint, request
from utils.logging_config import get_logger
from utils.response_helpers import build_success_response, build_error_response
from services.device_usage_service import (
    get_current_device_usage,
    get_historical_device_usage,
    get_device_usage_summary,
    reset_usage_counters,
    check_nlbwmon_status
)

device_usage_bp = Blueprint('device_usage', __name__)
logger = get_logger('endpoints.device_usage')
```

### 2.2 Current Usage Endpoints
[ ] `GET /api/device-usage/current` - Get real-time usage for all devices
```json
{
  "success": true,
  "data": {
    "timestamp": "2024-01-01T12:00:00Z",
    "devices": [
      {
        "mac": "aa:bb:cc:dd:ee:ff",
        "ip": "192.168.1.100",
        "hostname": "Device-Name",
        "bytes_rx": 1048576,
        "bytes_tx": 524288,
        "total_bytes": 1572864,
        "last_seen": "2024-01-01T11:58:00Z"
      }
    ],
    "total_devices": 5,
    "total_bytes": 7864320
  }
}
```

[ ] `GET /api/device-usage/device/{mac}` - Get current usage for specific device

### 2.3 Historical Data Endpoints
[ ] `GET /api/device-usage/history` - Get historical usage data
  - Query parameters: `days` (default: 7), `format` (json|csv)

[ ] `GET /api/device-usage/summary` - Get usage summary and statistics
```json
{
  "success": true,
  "data": {
    "period_days": 7,
    "total_bytes": 10737418240,
    "top_devices": [
      {
        "mac": "aa:bb:cc:dd:ee:ff",
        "hostname": "Device-Name",
        "total_bytes": 3221225472,
        "percentage": 30.0
      }
    ],
    "daily_totals": [
      {"date": "2024-01-01", "bytes": 1500000000},
      {"date": "2024-01-02", "bytes": 1600000000}
    ]
  }
}
```

### 2.4 Management Endpoints
[ ] `POST /api/device-usage/reset` - Reset usage counters (executes `nlbw -z`)
[ ] `GET /api/device-usage/status` - Check nlbwmon service status

---

## Phase 3: Advanced Data Processing

### 3.1 Enhanced Service Functions
[ ] Implement advanced data processing in `device_usage_service.py`:

```python
def get_device_usage_by_timeframe(timeframe='24h'):
    """Get device usage for specific timeframe."""
    # Map timeframe to nlbwmon parameters
    timeframe_map = {
        '1h': '-c json -t 1',
        '24h': '-c json -t 24', 
        '7d': '-c json -t 168',
        '30d': '-c json -t 720'
    }
    
    cmd = f"nlbw {timeframe_map.get(timeframe, '-c json')}"
    output, error = router_connection_manager.execute(cmd)
    
    if error:
        return None, f"Command failed: {error}"
    
    return json.loads(output), None
```

### 3.2 Data Export Functions
[ ] Add export capabilities:
  - [ ] `export_usage_csv()` - Export usage data as CSV
  - [ ] `export_usage_json()` - Export usage data as JSON
  - [ ] `generate_usage_report()` - Generate formatted usage report

### 3.3 Device Identification Enhancement
[ ] Enhance device identification:
  - [ ] Cross-reference with router ARP table
  - [ ] Include device hostnames from DHCP leases
  - [ ] Add MAC vendor lookup integration
  - [ ] Device categorization by usage patterns

---

## Phase 4: Service Integration

### 4.1 Router State Integration
[ ] Integrate with existing `router_state_manager.py`:
  - [ ] Store usage monitoring preferences in router state
  - [ ] Track monitoring intervals and retention settings
  - [ ] Manage device aliases and custom names

### 4.2 Network Service Integration
[ ] Enhance existing `network_service.py`:
  - [ ] Add usage data to device scanning results
  - [ ] Include bandwidth information in device lists
  - [ ] Cross-reference scanned devices with usage data

### 4.3 Blueprint Registration
[ ] Register new blueprint in `server.py`:
```python
from endpoints.device_usage import device_usage_bp

app.register_blueprint(device_usage_bp, url_prefix='/api/device-usage')
```

---

## Phase 5: Monitoring and Utilities

### 5.3 Error Handling and Logging
[ ] Implement comprehensive error handling:
  - [ ] Handle nlbwmon service failures gracefully
  - [ ] Log usage data collection issues
  - [ ] Provide fallback when nlbwmon unavailable

---

## Implementation Notes

### Commands Server Architecture Compliance

1. **No Database Storage**: All data comes directly from router via SSH commands
2. **Session Context**: All operations use `g.session_id` and `g.router_id`
3. **RouterConnectionManager**: Use existing SSH connection pooling
4. **Service Pattern**: Follow `services/*.py` → `router_connection_manager.execute()`
5. **Blueprint Pattern**: Follow existing `endpoints/*.py` structure
6. **Response Format**: Use existing `build_success_response()` and `build_error_response()`

### nlbwmon Command Reference

```bash
# Current usage (JSON)
nlbw -c json

# Current usage (CSV)  
nlbw -c csv

# Historical data (24 hours)
nlbw -c json -t 24

# Reset counters
nlbw -z

# Check service status
/etc/init.d/nlbwmon status

# Get detailed device info
nlbw -c json -i
```

### Error Handling Strategy

- [ ] Graceful degradation when nlbwmon unavailable
- [ ] Clear error messages for missing dependencies
- [ ] Fallback to basic router statistics if needed
- [ ] Proper logging for troubleshooting

### Performance Considerations

- [ ] Cache expensive nlbwmon queries for short periods
- [ ] Implement query timeouts for large datasets
- [ ] Paginate results for large device lists
- [ ] Optimize JSON parsing for large data sets

---

## File Structure

### New Files to Create
```
backend/
├── services/
│   └── device_usage_service.py          # Core service functions
├── endpoints/
│   └── device_usage.py                  # REST API blueprint
├── utils/
│   └── nlbwmon_parser.py               # Data parsing utilities
└── DEVICE_USAGE_MONITORING_IMPLEMENTATION_PLAN.md
```

### Files to Modify
```
backend/
├── server.py                           # Register device_usage_bp
└── endpoints/health.py                 # Add nlbwmon health checks
```

---

## Success Criteria

### Functional Requirements
✅ **Device Usage Retrieval**: Successfully execute nlbwmon commands and parse results
✅ **Historical Data Access**: Retrieve and format historical usage data
✅ **Real-time Monitoring**: Provide current bandwidth usage per device
✅ **Data Export**: Enable CSV/JSON export of usage data
✅ **Service Management**: Monitor and manage nlbwmon service status

### Technical Requirements
✅ **Commands Server Compliance**: Follow existing SSH command execution patterns
✅ **Session Management**: Proper sessionId/routerId context handling
✅ **Error Handling**: Robust error handling for command failures
✅ **Performance**: Efficient data processing and response times
✅ **Documentation**: Clear API documentation and usage examples

### Integration Requirements
✅ **Router Compatibility**: Work with existing nlbwmon installations
✅ **Service Integration**: Integrate with existing network services
✅ **API Consistency**: Match existing endpoint patterns and response formats
✅ **Logging**: Comprehensive logging using existing logging system
✅ **Health Monitoring**: Integration with health check endpoints

This implementation plan provides a focused approach to adding device usage monitoring to the NetPilot Commands Server while maintaining architectural consistency and leveraging the router's existing nlbwmon capabilities.
