# NetPilot

NetPilot is an application designed to simplify home network management. It provides an intuitive interface for monitoring devices, controlling access, and tracking usage without dealing with complex router settings.

## Features

- **Network Device Scanning**: Discover and monitor all connected devices
- **Access Control**: Manage which devices can connect to your network
- **Usage Tracking**: Monitor bandwidth usage by device
- **WiFi Management**: Configure and optimize your wireless network
- **User-friendly Dashboard**: Visual representation of network status
- **Dark Mode Support**: Comfortable viewing experience in any lighting condition

## Technology Stack

### Frontend
- React.js
- React Router DOM
- TailwindCSS (for styling)
- Vite (build tool)

### Backend
- Python Flask
- SQLite (database)
- Paramiko (SSH client)
- Scapy (network packet manipulation)

## Installation

### Prerequisites
- Node.js (v16 or higher)
- Python 3.8+
- npm or yarn

### Setup Instructions

1. **Clone the repository**
   ```
   git clone https://github.com/yourusername/NetPilot.git
   cd NetPilot
   ```

2. **Backend Setup**
   ```
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```
   cd frontend/dashboard
   npm install
   ```

4. **Configuration**
   - Create a `.env` file in the project root folder (see example below)
   ```
   SERVER_PORT=5000
   ROUTER_IP=192.168.1.1
   USERNAME=admin
   PASSWORD=password
   ```

## Usage

1. **Start the backend server**
   ```
   cd backend
   python server.py
   ```
   Or use the provided batch script:
   ```
   run_server.bat
   ```

2. **Start the frontend development server**
   ```
   cd frontend/dashboard
   npm run dev
   ```

3. **Access the application**
   - Open your browser and navigate to: `http://localhost:5173`

## Project Structure

```