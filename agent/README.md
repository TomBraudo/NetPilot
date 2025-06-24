# NetPilot Router Agent

A powerful Electron application that automates OpenWrt router setup and establishes secure reverse SSH tunnels to NetPilot Cloud.

## Features

- 🔧 **Automated Router Setup**: Installs required packages on OpenWrt routers
- 🔐 **Secure SSH Tunnels**: Establishes persistent reverse tunnels to cloud VM
- 🌐 **Multi-user Support**: Dynamic port allocation for multiple routers
- 📊 **Real-time Monitoring**: Connection status and tunnel health monitoring
- ✨ **Modern UI**: Clean, intuitive interface built with Electron

## Prerequisites

- Node.js 18+ and npm
- OpenWrt router with SSH access (v22.0+)
- Router credentials (username/password)

## Installation

1. **Clone or navigate to the agent directory**:
   ```bash
   cd agent
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment variables**:
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env with your actual credentials
   nano .env
   ```

   **Required Configuration:**
   - `CLOUD_VM_IP`: Your cloud VM IP address (default: 34.38.207.87)
   - `CLOUD_VM_USER`: SSH username for cloud VM (default: netpilot-agent)
   - `CLOUD_VM_PASSWORD`: SSH password for cloud VM (**REQUIRED**)
   - `CLOUD_VM_PORT`: SSH port (default: 22)
   - `PORT_RANGE_MIN`: Minimum port for allocation (default: 2200)
   - `PORT_RANGE_MAX`: Maximum port for allocation (default: 2299)

   **⚠️ Important**: The application will warn you if `CLOUD_VM_PASSWORD` is not set, as tunnel establishment will fail without proper authentication.

## Running the Application

### Development Mode
```bash
npm run dev
```
This opens the app with developer tools enabled.

### Production Mode
```bash
npm start
```

## Building for Distribution

### Build for current platform
```bash
npm run build
```

### Build for specific platforms
```bash
# Windows
npm run build-win

# macOS
npm run build-mac

# Linux
npm run build-linux
```

Built applications will be available in the `dist/` directory.

## Usage

1. **Launch the application**
2. **Enter router credentials**:
   - Router IP (usually 192.168.1.1)
   - Username (usually "root")
   - Password (or leave empty if none)

3. **Test connection** (optional but recommended)
4. **Click "Install & Connect"** to:
   - Install required packages on router
   - Allocate a tunnel port from cloud VM
   - Establish secure reverse SSH tunnel
   - Enable NetPilot cloud management

## Configuration

### Advanced Options
- **Cloud VM IP**: NetPilot cloud server address
- **SSH Port**: Router SSH port (default: 22)

### Default Settings
- Cloud VM: `34.38.207.87`
- Port Range: `2200-2299` (100 concurrent users)
- Tunnel User: `netpilot-agent`

## Troubleshooting

### Common Issues

**Connection Failed**
- Verify router IP address and credentials
- Ensure router SSH service is enabled
- Check network connectivity

**Package Installation Failed**
- Router may need internet access for package downloads
- Check available storage space on router
- Verify OpenWrt version compatibility

**Tunnel Establishment Failed**
- Check if cloud VM is accessible
- Verify firewall allows outbound connections
- Ensure required packages (openssh-client, autossh) are installed

### Logs
Application logs are available through the "View Logs" button in the footer.

## Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌──────────────┐
│ NetPilot Agent  │───▶│ OpenWrt      │───▶│ Cloud VM     │
│ (This App)      │    │ Router       │    │ (34.38.207.87)│
└─────────────────┘    └──────────────┘    └──────────────┘
        │                       │                    │
        │                       │                    │
        ▼                       ▼                    ▼
   - Router Setup          - Package Install    - Port Allocation
   - Tunnel Config         - SSH Tunnel         - NetPilot Backend
   - Status Monitor        - Auto-restart       - Dashboard Access
```

## Required Router Packages

The agent automatically installs these packages:

- `openssh-client`, `autossh` - For tunnel establishment
- `firewall4`, `iptables-mod-ipopt` - For NetPilot firewall features
- `tc`, `kmod-sched`, `kmod-sched-core` - For bandwidth limiting
- `uci`, `ip-full`, `dnsmasq` - For configuration management
- `curl`, `wget`, `ca-certificates` - For external communication
- `cron` - For scheduled operations

## API Integration

After successful setup, the agent provides router credentials for NetPilot frontend integration:

```javascript
// Access router credentials in frontend
const credentials = app.getRouterApiCredentials();
if (credentials) {
  // Use for API calls to router through tunnel
  console.log('Router Host:', credentials.host);
  console.log('Tunnel Port:', credentials.tunnelPort);
  console.log('Cloud VM IP:', credentials.cloudVmIp);
}
```

**Available API Methods:**
- `getRouterApiCredentials()`: Returns router connection details
- `getConfig()`: Returns current application configuration
- `getRouterCredentials()`: Returns full router credential object
- `getCloudVmAccess()`: Returns cloud VM access information

## Security

### Password Management
- Router passwords are stored securely using the system keychain (keytar)
- All passwords in logs are automatically redacted as `[REDACTED]`
- Environment variables are used for sensitive configuration
- No credentials are hardcoded in source files

### Test Files
- All test files use placeholder credentials (`YOUR_ROUTER_PASSWORD_HERE`)
- Update test credentials locally before running tests
- Never commit real passwords or keys to the repository

### Log File Security
- Log files are automatically gitignored
- Sensitive data is masked in log output
- Clear logs before committing changes

### Environment Configuration
1. Copy `env.example` to `.env`
2. Fill in your actual credentials
3. Never commit the `.env` file

## License

MIT License - © 2024 NetPilot Team

---

**Need Help?** Check the troubleshooting section or contact support. 