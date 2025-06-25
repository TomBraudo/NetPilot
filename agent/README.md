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

## Local Testing Guide

### Testing on Windows

1. **Native Windows (Recommended)**:
   ```bash
   # Navigate to agent directory
   cd agent

   # Install dependencies and run
   npm install
   npm run dev
   ```

2. **Windows with WSL** (requires additional setup - see WSL section below)

### Testing on macOS

```bash
# Navigate to agent directory
cd agent

# Install dependencies
npm install

# Run in development mode
npm run dev
```

### Testing on Linux

#### Native Linux (Ubuntu/Debian)

1. **Install system dependencies**:
   ```bash
   # Update package lists
   sudo apt-get update

   # Install required Electron dependencies
   sudo apt-get install build-essential clang libdbus-1-dev libgtk-3-dev \
                        libnotify-dev libasound2-dev libcap-dev \
                        libcups2-dev libxtst-dev libxss1 libnss3-dev \
                        gcc-multilib g++-multilib curl gperf bison \
                        python3-dbusmock openjdk-8-jre

   # Install runtime libraries
   sudo apt-get install libnss3 libnss3-tools libatk-bridge2.0-0 \
                        libdrm2 libxcomposite1 libxdamage1 libxrandr2 \
                        libgbm1 libxkbcommon0 libgtk-3-0 libasound2

   # Install keytar dependencies (for secure credential storage)
   sudo apt-get install libsecret-1-0
   ```

2. **Run the application**:
   ```bash
   cd agent
   npm install
   npm run dev
   ```

#### WSL (Windows Subsystem for Linux)

1. **Install system dependencies** (same as Linux above):
   ```bash
   sudo apt-get update
   sudo apt-get install build-essential clang libdbus-1-dev libgtk-3-dev \
                        libnotify-dev libasound2-dev libcap-dev \
                        libcups2-dev libxtst-dev libxss1 libnss3-dev \
                        gcc-multilib g++-multilib curl gperf bison \
                        python3-dbusmock openjdk-8-jre

   sudo apt-get install libnss3 libnss3-tools libatk-bridge2.0-0 \
                        libdrm2 libxcomposite1 libxdamage1 libxrandr2 \
                        libgbm1 libxkbcommon0 libgtk-3-0 libasound2 \
                        libsecret-1-0
   ```

2. **Setup display server** (for GUI):
   ```bash
   # Option 1: Use WSLg (Windows 11 with WSL 2.0+)
   # WSLg should work automatically - just run the app

   # Option 2: Use X11 forwarding (if WSLg not available)
   export DISPLAY=:0
   
   # Option 3: Use software rendering (fallback)
   npm run dev -- --disable-gpu --disable-software-rasterizer
   ```

3. **Run the application**:
   ```bash
   cd agent
   npm install
   npm run dev
   ```

4. **Common WSL warnings** (can be ignored):
   ```
   Warning: vkCreateInstance: Found no drivers!
   Warning: EGL_EXT_create_context_robustness must be supported
   ```
   These are normal graphics warnings in WSL and don't affect functionality.

### Testing Environment Setup

1. **Create test configuration**:
   ```bash
   # Copy example environment
   cp env.example .env

   # Edit with test credentials
   nano .env
   ```

2. **Test credentials** (for local testing):
   ```env
   CLOUD_VM_IP=34.38.207.87
   CLOUD_VM_USER=netpilot-agent
   CLOUD_VM_PASSWORD=your_cloud_vm_password
   CLOUD_VM_PORT=22
   PORT_RANGE_MIN=2200
   PORT_RANGE_MAX=2299
   ```

### Testing Different Scenarios

#### 1. **Router Connection Testing**
   - Test with valid router credentials
   - Test with invalid credentials
   - Test connection timeout scenarios
   - Test with different router IP formats

#### 2. **Package Installation Testing**
   - Test on routers with internet access
   - Test on routers without internet access
   - Test with insufficient storage space
   - Test package installation rollback

#### 3. **Tunnel Establishment Testing**
   - Test successful tunnel creation
   - Test tunnel with cloud VM authentication
   - Test tunnel persistence and auto-restart
   - Test multiple simultaneous tunnels

#### 4. **Error Handling Testing**
   - Test network connectivity issues
   - Test SSH authentication failures
   - Test cloud VM unreachable scenarios
   - Test port allocation conflicts

### Development Tools

1. **Enable Developer Tools**:
   ```bash
   npm run dev  # Automatically enables DevTools
   ```

2. **View Application Logs**:
   - Use the "View Logs" button in the app footer
   - Or check log files in `logs/` directory
   - Real-time logging in DevTools console

3. **Debug Mode**:
   ```bash
   # Run with additional debugging
   DEBUG=* npm run dev
   ```

### Testing Commands Reference

```bash
# Install and run
npm install && npm run dev

# Clean install (if dependencies have issues)
rm -rf node_modules package-lock.json
npm install
npm run dev

# Test build process
npm run build

# Run with specific Electron version
npx electron@28.0.0 .

# Run with software rendering (WSL)
npm run dev -- --disable-gpu --disable-software-rasterizer

# Run in verbose mode
DEBUG=* npm run dev
```

### Troubleshooting Local Testing

#### **Missing Shared Libraries (Linux/WSL)**
If you encounter `libXXX.so: cannot open shared object file`:

1. **Identify the missing library**:
   ```bash
   ldd node_modules/electron/dist/electron | grep "not found"
   ```

2. **Install the missing library**:
   ```bash
   # For Ubuntu/Debian
   sudo apt-get install lib[package-name]
   
   # Examples:
   sudo apt-get install libnss3        # for libnss3.so
   sudo apt-get install libasound2     # for libasound.so.2
   sudo apt-get install libsecret-1-0  # for libsecret-1.so.0
   ```

#### **Display Issues (WSL)**
```bash
# Try different display configurations
export DISPLAY=:0.0
export DISPLAY=localhost:0.0

# Use software rendering
npm run dev -- --disable-gpu

# Check if WSLg is available
echo $WAYLAND_DISPLAY
```

#### **Permission Errors**
```bash
# Fix npm permissions (Linux/macOS)
sudo chown -R $(whoami) ~/.npm
sudo chown -R $(whoami) node_modules/

# Fix Electron permissions
chmod +x node_modules/electron/dist/electron
```

#### **Port Already in Use**
```bash
# Find and kill process using port 3000
sudo lsof -ti:3000 | xargs kill -9

# Or use different port
PORT=3001 npm run dev
```

### Testing Checklist

Before submitting changes, verify:

- ✅ App starts without errors on your platform
- ✅ UI loads and displays correctly
- ✅ Router connection test works
- ✅ Environment variables are loaded
- ✅ Logs are being written correctly
- ✅ No sensitive data in logs
- ✅ DevTools console shows no critical errors
- ✅ App can be built for distribution

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