# NetPilot

NetPilot is a comprehensive cloud-based network management platform that enables users to monitor and control their home routers from anywhere in the world. Through a simple setup process, users can securely manage their network devices, control access, and track usage without being limited to their local network.

## Features

- **Remote Network Management**: Control your home router from anywhere in the world
- **Network Device Scanning**: Discover and monitor all connected devices
- **Access Control**: Manage which devices can connect to your network
- **Usage Tracking**: Monitor bandwidth usage by device
- **WiFi Management**: Configure and optimize your wireless network
- **Multi-User Support**: Secure user authentication and isolated data management
- **Real-time Monitoring**: Live connection status and tunnel health monitoring
- **User-friendly Dashboard**: Modern web interface accessible from any device
- **Dark Mode Support**: Comfortable viewing experience in any lighting condition

## Architecture Overview

NetPilot employs a sophisticated cloud-based architecture that transforms local network management into a globally accessible service:

```
Internet
    ↓
[Web Application] → [Auth + DB Server] → [Commands Server] → [SSH Tunnel] → [Home Router]
    ↓                       ↓                    ↓              ↓
[User Interface]    [Authentication]    [Command Execution]  [Secure Connection]
                    [Data Management]   [Port Management]    [Agent Managed]
```

### System Components

1. **NetPilot Agent** (Local Setup)
   - Electron application installed on user's computer
   - Handles router setup and package installation
   - Establishes secure SSH tunnels to cloud infrastructure
   - Manages tunnel persistence and auto-reconnection

2. **Cloud Infrastructure**
   - **Auth + DB Server**: Handles user authentication, session management, and data storage
   - **Commands Server**: Executes router commands via SSH tunnels
   - **Port Manager**: Manages dynamic port allocation (2200-2299 range)
   - **Web Application**: React-based dashboard accessible globally

3. **Security Layer**
   - End-to-end encrypted SSH tunnels
   - User authentication and authorization
   - Isolated data storage per user
   - Secure command routing and validation

## Technology Stack

### Frontend (Web Application)
- React.js with modern hooks
- React Router DOM for navigation
- TailwindCSS for responsive styling
- Vite for optimized builds and development

### Backend (Cloud Services)
- **Auth + DB Server**: Python Flask with SQLAlchemy
- **Commands Server**: Node.js/Express for command routing
- **Database**: SQLite with multi-user isolation
- **SSH Management**: Paramiko for secure connections
- **Network Tools**: Scapy for packet analysis

### Agent Application
- Electron for cross-platform desktop app
- Node.js backend for system operations
- Automated OpenWrt package installation
- SSH tunnel management and monitoring

### Infrastructure
- Google Cloud Platform deployment
- Docker containerization
- Persistent volume storage
- SSL/TLS encryption
- Domain-based access

## Quick Start

### Step 1: Install the NetPilot Agent

Download and install the NetPilot Agent on a computer within your home network:

### Step 1: Install the NetPilot Agent

Download and install the NetPilot Agent on a computer within your home network:

1. **Download the Agent**
   ```bash
   git clone https://github.com/yourusername/NetPilot.git
   cd NetPilot/agent
   ```

2. **Install and Configure**
   ```bash
   npm install
   cp env.example .env
   # Edit .env with your cloud VM credentials
   ```

3. **Run the Agent**
   ```bash
   npm run dev  # Development mode
   # or
   npm start    # Production mode
   ```

### Step 2: Router Setup

1. **Enter Router Details** in the Agent:
   - Router IP address (usually 192.168.1.1)
   - Admin username (usually "root")
   - Admin password

2. **Test Connection** (recommended)

3. **Install & Connect** - The agent will:
   - Install required OpenWrt packages on your router
   - Establish a secure SSH tunnel to NetPilot cloud
   - Register your router with your user account

### Step 3: Access NetPilot Web Dashboard

Once setup is complete, access your NetPilot dashboard from anywhere:

- **Web Application**: [https://netpilot.yourcloud.com](https://netpilot.yourcloud.com)
- **Login** with your user credentials
- **Manage** your network remotely

## How It Works

### The Complete Flow

1. **Agent Setup**: Install the NetPilot Agent on your home computer
2. **Router Configuration**: Agent automatically configures your OpenWrt router
3. **Tunnel Establishment**: Secure SSH tunnel created from router to cloud VM
4. **Global Access**: Access NetPilot web dashboard from anywhere in the world
5. **Command Routing**: Commands flow securely through the cloud to your router

### Security & Privacy

- **End-to-End Encryption**: All communications use SSH encryption
- **No Open Ports**: No inbound ports opened on your home network
- **User Isolation**: Each user's data and commands are completely isolated
- **Secure Authentication**: Industry-standard user authentication and session management

## Advanced Features

### Multi-Router Support
- Manage multiple routers from a single account
- Each router gets its own secure tunnel
- Isolated management per router

### Real-time Monitoring
- Live device detection and status
- Connection health monitoring
- Bandwidth usage tracking
- Network performance metrics

### Access Control
- Device whitelist/blacklist management
- Time-based access controls
- Bandwidth limiting per device
- QoS priority management

## Prerequisites

### Router Requirements
- OpenWrt-based router (v22.0+)
- SSH access enabled
- Internet connectivity for package installation
- Sufficient storage for additional packages

### Agent Requirements
- Node.js 18+ and npm
- Windows, macOS, or Linux
- Network access to your router
- Internet connectivity

### Web Dashboard
- Modern web browser
- Internet connectivity
- User account registration

## Project Structure

```
NetPilot/
├── agent/                 # Electron desktop application
│   ├── src/              # Agent source code
│   ├── assets/           # Application assets
│   └── README.md         # Agent-specific documentation
├── backend/              # Original Flask server (for development)
│   ├── endpoints/        # API endpoints
│   ├── services/         # Business logic
│   ├── db/              # Database operations
│   └── utils/           # Utility functions
├── backend2/             # Cloud Auth + DB server
│   ├── endpoints/        # Authentication endpoints
│   ├── database/         # Database models and migrations
│   ├── services/         # User and auth services
│   └── managers/         # Command routing managers
├── cloud-port-manager/   # Port allocation service
├── frontend/
│   └── dashboard/        # React web application
│       ├── src/         # React components and logic
│       └── public/      # Static web assets
├── plans/                # Architecture and migration documentation
├── logs/                 # Application logs
└── data/                 # Configuration and data storage
```

## Development Setup

For developers wanting to contribute or customize NetPilot:

### Local Development Environment

1. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/NetPilot.git
   cd NetPilot
   ```

2. **Backend Development** (Legacy - for reference)
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python server.py
   ```

3. **Frontend Development**
   ```bash
   cd frontend/dashboard
   npm install
   npm run dev
   ```

4. **Agent Development**
   ```bash
   cd agent
   npm install
   npm run dev
   ```

### Cloud Infrastructure

The cloud infrastructure runs on Google Cloud Platform with:
- VM Instance for Commands Server and Port Manager
- Container deployment for Auth + DB Server
- Cloud Storage for backups and static assets
- Load balancer and SSL termination

## Migration from Local to Cloud

NetPilot has evolved from a localhost-only application to a comprehensive cloud platform. The migration preserves all existing functionality while adding global accessibility and multi-user support.

### Benefits of the Cloud Architecture

- **Global Access**: Manage your network from anywhere
- **Enhanced Security**: Enterprise-grade security and encryption
- **Scalability**: Support for multiple users and routers
- **Reliability**: Cloud infrastructure with monitoring and backups
- **User Management**: Proper authentication and data isolation
- **Modern Interface**: Responsive web application

## Troubleshooting

### Agent Issues
- **Connection Failed**: Verify router IP and credentials
- **Package Installation Failed**: Ensure router has internet access and sufficient storage
- **Tunnel Failed**: Check cloud VM accessibility and credentials

### Web Dashboard Issues
- **Can't Login**: Verify user credentials and internet connectivity
- **Router Offline**: Check if agent is running and tunnel is established
- **Commands Not Working**: Verify router tunnel status in agent

### Common Solutions
- Restart the NetPilot Agent
- Check router internet connectivity
- Verify cloud service status
- Review application logs

## Support & Documentation

- **Agent Setup Guide**: See `agent/README.md`
- **API Documentation**: See `api_documentation.csv`
- **Migration Plans**: See `plans/` directory
- **Troubleshooting**: See individual component README files

## License

[License information to be added]

---

**NetPilot** - Transforming home network management from local to global, from simple to sophisticated, while maintaining the ease of use that makes network management accessible to everyone.

