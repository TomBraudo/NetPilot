# NetPilot Cloud Port Manager

This service manages port allocation for NetPilot router agents on the cloud VM, enabling multiple routers to establish reverse SSH tunnels simultaneously.

## Features

- **Dynamic Port Allocation**: Automatically assigns ports from range 2200-2299
- **Port Management**: Track, monitor, and release port allocations
- **Health Monitoring**: Check tunnel connectivity and cleanup inactive allocations
- **REST API**: HTTP endpoints for agent communication
- **Persistence**: SQLite database for allocation tracking
- **Security**: Router authentication and port access control

## Installation on Cloud VM

### 1. Upload to Cloud VM

```bash
# From your local machine, upload the cloud-port-manager directory
scp -r agent/cloud-port-manager root@34.38.207.87:/opt/netpilot-port-manager

# SSH into cloud VM
ssh root@34.38.207.87 -p 2222
```

### 2. Install Dependencies

```bash
cd /opt/netpilot-port-manager
npm install
```

### 3. Configure Firewall

```bash
# Open port range for reverse SSH tunnels
ufw allow 2200:2299/tcp comment "NetPilot Router Tunnels"

# Open port for the API
ufw allow 8080/tcp comment "NetPilot Port Management API"

# Verify
ufw status numbered
```

### 4. Start the Service

```bash
# Start with PM2 for production
npm run pm2-start

# Check status
pm2 status

# View logs
npm run pm2-logs
```

## API Endpoints

### Health Check
```
GET /api/health
```

### Allocate Port
```
POST /api/allocate-port
Content-Type: application/json

{
  "routerId": "router-uuid-here"
}
```

### Release Port
```
POST /api/release-port/:port
Content-Type: application/json

{
  "routerId": "router-uuid-here"  
}
```

### Port Status
```
GET /api/port-status?port=2200
GET /api/port-status?routerId=router-uuid
GET /api/port-status  # All allocations
```

### Router Heartbeat
```
POST /api/heartbeat/:port
Content-Type: application/json

{
  "routerId": "router-uuid-here"
}
```

### Admin - View All Allocations
```
GET /api/admin/allocations
```

## Configuration

### Environment Variables

```bash
# Optional: Set custom port (default: 8080)
export PORT=8080

# Optional: Set custom database path
export DB_PATH=/opt/netpilot-port-manager/data/ports.db
```

### Port Range

The service manages ports **2200-2299** (100 concurrent routers).

To change the range, edit `services/PortManager.js`:

```javascript
this.portRange = {
  min: 2200,  // Change start port
  max: 2299   // Change end port
};
```

## Monitoring

### PM2 Management
```bash
# Check service status
pm2 status

# View real-time logs
pm2 logs netpilot-port-manager

# Restart service
npm run pm2-restart

# Stop service
npm run pm2-stop
```

### Health Monitoring

The service includes automatic health monitoring:

- **Port Health Checks**: Every 5 minutes
- **Cleanup Inactive**: Every 1 hour (releases ports inactive >24h)
- **Statistics Logging**: Tracks allocation stats

### Manual Health Check

```bash
# Test API health
curl http://localhost:8080/api/health

# Check allocations
curl http://localhost:8080/api/port-status

# View service logs
tail -f /opt/netpilot-port-manager/logs/port-manager.log
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using port 8080
   netstat -tuln | grep 8080
   
   # Kill process if needed
   fuser -k 8080/tcp
   ```

2. **Database permissions**
   ```bash
   # Fix database directory permissions
   chown -R root:root /opt/netpilot-port-manager/data
   chmod 755 /opt/netpilot-port-manager/data
   ```

3. **Firewall blocking**
   ```bash
   # Check UFW status
   ufw status numbered
   
   # Add rules if missing
   ufw allow 2200:2299/tcp
   ufw allow 8080/tcp
   ```

### Database Management

```bash
# View database directly
sqlite3 /opt/netpilot-port-manager/data/ports.db

# Check active allocations
sqlite3 /opt/netpilot-port-manager/data/ports.db "SELECT * FROM port_allocations WHERE status='active';"

# Clear all allocations (emergency)
sqlite3 /opt/netpilot-port-manager/data/ports.db "UPDATE port_allocations SET status='released';"
```

## Auto-Start on Boot

```bash
# Install PM2 startup script
pm2 startup

# Save current PM2 configuration
pm2 save
```

## Security Considerations

1. **Router Authentication**: Each router requires a unique ID
2. **Port Access Control**: Ports are bound to specific router IDs
3. **Timeout Protection**: Inactive allocations are auto-released
4. **API Security**: Add authentication headers in production

## Integration with Agent

The NetPilot agent will automatically:

1. Request port allocation from this service
2. Use allocated port for reverse SSH tunnel
3. Send periodic heartbeats to maintain allocation
4. Release port when disconnecting

## Production Deployment

For production, consider:

1. **Reverse Proxy**: Use nginx for SSL termination
2. **Authentication**: Add API keys or JWT tokens
3. **Monitoring**: Integrate with monitoring systems
4. **Backups**: Regular database backups
5. **Load Balancing**: Scale across multiple VMs if needed 