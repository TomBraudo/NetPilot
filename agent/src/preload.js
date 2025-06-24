const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Configuration
  getConfig: () => ipcRenderer.invoke('get-config'),
  
  // Router credentials management
  getRouterCredentials: () => ipcRenderer.invoke('get-router-credentials'),
  saveRouterPassword: (password) => ipcRenderer.invoke('save-router-password', password),
  getRouterPassword: () => ipcRenderer.invoke('get-router-password'),
  
  // Router configuration state
  getRouterConfigurationState: () => ipcRenderer.invoke('get-router-configuration-state'),
  saveRouterConfigurationState: (state) => ipcRenderer.invoke('save-router-configuration-state', state),
  
  // Cloud VM access
  getCloudVmAccess: () => ipcRenderer.invoke('get-cloud-vm-access'),
  
  // Router operations
  testRouterConnection: (credentials) => ipcRenderer.invoke('test-router-connection', credentials),
  installRouterPackages: (credentials) => ipcRenderer.invoke('install-router-packages', credentials),
  enableWifi: (credentials) => ipcRenderer.invoke('enable-wifi', credentials),
  
  // Package verification
  verifyNetPilotCompatibility: (credentials) => ipcRenderer.invoke('verify-netpilot-compatibility', credentials),
  
  // Port allocation
  allocatePort: (credentials) => ipcRenderer.invoke('allocate-port', credentials),
  releasePort: (port) => ipcRenderer.invoke('release-port', port),
  
  // Tunnel management
  establishTunnel: (config) => ipcRenderer.invoke('establish-tunnel', config),
  getTunnelStatus: () => ipcRenderer.invoke('get-tunnel-status'),
  disconnectTunnel: () => ipcRenderer.invoke('disconnect-tunnel'),
  
  // NetPilot management
  uninstallNetPilot: (credentials) => ipcRenderer.invoke('uninstall-netpilot', credentials),
  
  // Phase 7: Status API and Verification (NEW)
  
  // Status API Server Management
  startStatusServer: () => ipcRenderer.invoke('start-status-server'),
  stopStatusServer: () => ipcRenderer.invoke('stop-status-server'),
  getStatusServerInfo: () => ipcRenderer.invoke('get-status-server-info'),
  
  // Enhanced Verification (Phase 7.1 & 7.2)
  verifyRouterSetup: (credentials) => ipcRenderer.invoke('verify-router-setup', credentials),
  verifyTunnelConnectivity: () => ipcRenderer.invoke('verify-tunnel-connectivity'),
  
  // Command Testing and Latency (Phase 7.2)
  testCommandExecution: (command) => ipcRenderer.invoke('test-command-execution', command),
  measureTunnelLatency: () => ipcRenderer.invoke('measure-tunnel-latency'),
  
  // Comprehensive Status (Phase 7.3)
  getComprehensiveStatus: () => ipcRenderer.invoke('get-comprehensive-status'),
  
  // WiFi status (keeping existing)
  getWifiStatus: (credentials) => ipcRenderer.invoke('get-wifi-status', credentials),
  
  // Dialogs
  showInfo: (options) => ipcRenderer.invoke('show-info', options),
  showError: (options) => ipcRenderer.invoke('show-error', options),
  showConfirm: (options) => ipcRenderer.invoke('show-confirm', options),
  
  // File operations
  saveFile: (options) => ipcRenderer.invoke('save-file', options),
  
  // Data management
  resetAllData: () => ipcRenderer.invoke('reset-all-data'),
  onResetComplete: (callback) => ipcRenderer.on('reset-completed', () => callback()),
  
  // Version info
  version: process.versions.electron
}); 