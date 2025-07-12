# Commands Server Client

This directory contains the commands server client implementation for the NetPilot backend2 server. The client enables the backend2 server to communicate with the remote commands server to execute router operations.

## Architecture

The commands server client follows a layered architecture:

### 1. Service Layer (`services/commands_server_service.py`)
- **Purpose**: Low-level HTTP communication with the commands server
- **Responsibilities**: 
  - HTTP request/response handling
  - Error handling and retry logic
  - Request/response logging
  - Connection management

### 2. Manager Layer (`managers/commands_server_manager.py`)
- **Purpose**: High-level operations and business logic
- **Responsibilities**:
  - Connection health monitoring
  - Caching and optimization
  - Command routing and validation
  - Error handling and recovery

### 3. Client Layer (`commands-server-client.py`)
- **Purpose**: Test client and usage example
- **Responsibilities**:
  - Testing and validation
  - Command-line interface
  - Usage examples

## Configuration

The client uses the following environment variables:

```bash
COMMANDS_SERVER_URL=http://34.38.207.87:5000
```

This should be set in your `.env` file.

## Usage

### Basic Usage

```python
from managers.commands_server_manager import commands_server_manager

# Test connection
is_connected, error = commands_server_manager.test_connection()
if is_connected:
    print("Connected to commands server")

# Execute a router command
response, error = commands_server_manager.execute_router_command(
    router_id="router123",
    command="scan_network",
    params={"timeout": 30}
)
```

### Command Line Testing

```bash
# Run basic tests
python commands-server-client.py test

# Quick health check
python commands-server-client.py health

# Interactive mode
python commands-server-client.py interactive
```

## Available Operations

### Health Check
- **Method**: `health_check()`
- **Purpose**: Check if the commands server is healthy and responsive
- **Returns**: `(response_data, error_message)`

### Server Info
- **Method**: `get_server_info()`
- **Purpose**: Get information about the commands server
- **Returns**: `(server_info, error_message)`

### Router Commands
- **Method**: `execute_router_command(router_id, command, params)`
- **Purpose**: Execute a command on a specific router
- **Parameters**:
  - `router_id`: The target router ID
  - `command`: The command to execute
  - `params`: Additional command parameters
- **Returns**: `(response_data, error_message)`

### Router Status
- **Method**: `get_router_status(router_id)`
- **Purpose**: Get the current status of a router
- **Parameters**:
  - `router_id`: The router ID
- **Returns**: `(status_data, error_message)`

## Integration with Backend2 Services

### Example: Integrating with Whitelist Service

```python
# In services/whitelist_service.py
from managers.commands_server_manager import commands_server_manager

def add_device_to_whitelist(mac, router_id=None):
    """Add a device to the whitelist via commands server."""
    if not router_id:
        return None, "Router ID is required"
    
    # Execute command via commands server
    response, error = commands_server_manager.execute_router_command(
        router_id=router_id,
        command="add_to_whitelist",
        params={"mac": mac}
    )
    
    if error:
        return None, error
    
    return response, None
```

### Example: Integrating with Network Service

```python
# In services/network_service.py
from managers.commands_server_manager import commands_server_manager

def scan_network_via_router(router_id):
    """Scan network via commands server."""
    response, error = commands_server_manager.execute_router_command(
        router_id=router_id,
        command="scan_network"
    )
    
    if error:
        return None, error
    
    return response.get("devices", []), None
```

## Error Handling

The client implements comprehensive error handling:

1. **Connection Errors**: Automatically detected and reported
2. **HTTP Errors**: Status codes >= 400 are treated as errors
3. **Timeout Errors**: Configurable timeout with automatic retry
4. **JSON Parsing Errors**: Gracefully handled with fallback responses

## Logging

All operations are logged using the standard NetPilot logging system:

- **Service Level**: Debug-level HTTP request/response logging
- **Manager Level**: Info-level operation logging
- **Client Level**: User-friendly console output

## Testing

### Unit Tests
Run the test client to verify the integration:

```bash
python commands-server-client.py test
```

### Integration Tests
The client can be integrated into the main backend2 test suite by importing and using the manager:

```python
from managers.commands_server_manager import commands_server_manager

def test_commands_server_integration():
    assert commands_server_manager.test_connection()[0] is True
```

## Adding New Endpoints

To add support for new commands server endpoints:

### 1. Add Service Method
```python
# In services/commands_server_service.py
def new_endpoint(self, param1, param2):
    """Description of new endpoint."""
    data = {"param1": param1, "param2": param2}
    return self._make_request('POST', '/new-endpoint', data=data)
```

### 2. Add Manager Method
```python
# In managers/commands_server_manager.py
def new_operation(self, param1, param2):
    """High-level operation using new endpoint."""
    if not self.is_connected():
        return None, "Commands server is not connected"
    
    service = self._get_service()
    return service.new_endpoint(param1, param2)
```

### 3. Add Client Method
```python
# In commands-server-client.py
def test_new_operation(self, param1, param2):
    """Test the new operation."""
    response, error = self.manager.new_operation(param1, param2)
    # Handle response...
```

## Dependencies

The commands server client requires:

- `requests`: HTTP client library
- `typing`: Type hints (Python 3.5+)
- Backend2 utilities: `utils.logging_config`, `utils.response_helpers`

## Security Considerations

1. **Authentication**: Currently uses basic HTTP. Consider adding API key authentication.
2. **HTTPS**: For production, use HTTPS endpoints.
3. **Validation**: All parameters should be validated before sending to the commands server.
4. **Rate Limiting**: Consider implementing client-side rate limiting.

## Future Enhancements

1. **Authentication**: Add API key or OAuth support
2. **Caching**: Implement response caching for frequently accessed data
3. **Retry Logic**: Add exponential backoff for failed requests
4. **Metrics**: Add performance metrics and monitoring
5. **Circuit Breaker**: Implement circuit breaker pattern for reliability 