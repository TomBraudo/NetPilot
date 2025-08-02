# Network Dashboard

A beautiful and responsive React dashboard for monitoring network traffic and device usage with interactive charts and filtering capabilities.

## Features

### 📊 **Charts & Visualizations**

1. **Bar Chart**: Compares download vs upload traffic per device

   - X-axis: Device IP addresses
   - Y-axis: Traffic in MB
   - Side-by-side comparison of download (blue) and upload (red) data

2. **Pie Chart**: Shows total bandwidth usage distribution

   - Each device gets a distinct color
   - Proportional segments based on total traffic (download + upload)
   - Legend shows device IP and MAC address (last 8 characters)

3. **Sparkline Charts**: Mini trend charts for each device card
   - Shows traffic patterns over time
   - Interactive tooltips
   - Color-coded per device

### 🎛️ **Filtering & Controls**

- **Time Range Filter**: Last Day / Last Week / Last Month
- **Device Filter**: View all devices or focus on a specific MAC address
- **Sorting Options**: Sort by Download, Upload, or Connections (ascending/descending)
- **Real-time Refresh**: Manual refresh button with loading indicator

### 📱 **Dashboard Layout**

1. **Summary Cards**:

   - Total Download traffic
   - Total Upload traffic
   - Total Connections count
   - Active Devices count

2. **Device Information Cards**:
   - IP address and MAC address
   - Download/Upload statistics
   - Connection count
   - Total traffic calculation
   - Individual sparkline chart

### 🎨 **Design Features**

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark Mode Support**: Automatic theme switching
- **Modern UI**: Clean Tailwind CSS styling
- **Loading States**: Smooth loading animations
- **Empty States**: Helpful messages when no data matches filters

## Data Structure

The dashboard expects data in this JSON format:

```json
{
  "data": [
    {
      "connections": 210541,
      "download": 10969.18,
      "ip": "192.168.1.122",
      "mac": "d8:bb:c1:47:3a:43",
      "unit": "MB",
      "upload": 1681.12
    }
  ],
  "metadata": {
    "executionTime": 0.72,
    "routerId": "xxx",
    "sessionId": "xxx",
    "timestamp": "2025-08-02T19:59:45.89"
  }
}
```

## API Integration

The dashboard includes API integration utilities in `src/utils/dashboardApi.js`:

- `fetchNetworkData(timeRange, macAddress)`: Fetches filtered network data
- `fetchDevices()`: Gets list of available devices
- `getMockData()`: Provides fallback mock data
- `formatBytes()`: Formats data sizes with appropriate units
- `formatNumber()`: Formats numbers with thousands separators
- `getTimeLabels()`: Generates time-based chart labels

## Installation & Setup

1. **Install Dependencies**:

   ```bash
   npm install chart.js react-chartjs-2 date-fns
   ```

2. **Start Development Server**:

   ```bash
   npm run dev
   ```

3. **Access Dashboard**:
   Open http://localhost:5174 in your browser

## Configuration

Update the API endpoints in `src/constants/api.js` to match your backend:

```javascript
export const API_ENDPOINTS = {
  NETWORK: "http://localhost:5000/api/network",
  DEVICES: "http://localhost:5000/api/devices",
  // ... other endpoints
};
```

## Usage Tips

1. **Filter by Device**: Select a specific MAC address to view individual device analytics
2. **Time Range Analysis**: Use different time ranges to identify usage patterns
3. **Sort & Compare**: Sort devices by different metrics to find top consumers
4. **Refresh Data**: Use the refresh button to get the latest network statistics
5. **Responsive Views**: The dashboard adapts to your screen size automatically

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- Optimized chart rendering with Chart.js
- Memoized calculations for fast filtering
- Efficient re-renders with React hooks
- Lightweight bundle size

---

**Note**: The dashboard currently uses mock data for development. Replace the API calls in `dashboardApi.js` with your actual backend endpoints for production use.
