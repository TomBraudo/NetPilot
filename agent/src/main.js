const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const keytar = require('keytar');
const logger = require('./utils/Logger');

// Import our modules
const ConfigManager = require('./modules/ConfigManager');
const PortAllocator = require('./modules/PortAllocator');
const RouterManager = require('./modules/RouterManager');
const TunnelManager = require('./modules/TunnelManager');
const StatusServer = require('./modules/StatusServer');

class NetPilotAgent {
  constructor() {
    this.mainWindow = null;
    
    // Initialize managers
    this.configManager = new ConfigManager();
    this.portAllocator = new PortAllocator();
    this.routerManager = new RouterManager(this.configManager);
    this.tunnelManager = new TunnelManager();
    
    // Initialize Status API Server (Phase 7.3)
    this.statusServer = new StatusServer(
      this.routerManager,
      this.tunnelManager,
      this.portAllocator
    );
    
    // Router configuration state
    this.routerConfigState = {
      configured: false,
      profile: null,
      timestamp: null
    };
    
    // Bind methods
    this.createWindow = this.createWindow.bind(this);
    this.setupIpcHandlers = this.setupIpcHandlers.bind(this);
    this.setupCredentialHandlers = this.setupCredentialHandlers.bind(this);
  }

  getCloudVmAccess() {
    return {
      ip: this.configManager.get('cloudVmIp'),
      user: this.configManager.get('cloudUser'),
      port: this.configManager.get('cloudPort'),
      password: this.configManager.get('cloudPassword'),
    };
  }
  
  setupCredentialHandlers() {
    const service = 'NetPilotAgent';
    const account = 'router-password'; // Use a fixed account name for simplicity

    ipcMain.handle('save-router-password', async (event, password) => {
      try {
        if (password) {
          await keytar.setPassword(service, account, password);
          return { success: true };
        }
        // Allow saving an empty password
        await keytar.setPassword(service, account, '');
        return { success: true };
          } catch (error) {
      logger.error('MAIN', 'Failed to save password:', error);
      return { success: false, error: error.message };
    }
    });

    ipcMain.handle('get-router-password', async () => {
      try {
        const password = await keytar.getPassword(service, account);
        return { success: true, password };
      } catch (error) {
        logger.main('Failed to get password:', error);
        return { success: false, error: error.message };
      }
    });

    ipcMain.handle('delete-router-password', async () => {
      try {
        const success = await keytar.deletePassword(service, account);
        return { success };
      } catch (error) {
        logger.main('Failed to delete password:', error);
        return { success: false, error: error.message };
      }
    });
  }

  async createWindow() {
    this.mainWindow = new BrowserWindow({
      width: 800,
      height: 700,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js')
      },
      resizable: true,
      icon: path.join(__dirname, 'renderer/assets/icon.png')
    });

    await this.mainWindow.loadFile(path.join(__dirname, 'renderer/index.html'));
    
    // Show dev tools in development
    if (process.env.NODE_ENV === 'development') {
      this.mainWindow.webContents.openDevTools();
    }

    // Start Status API Server when window is ready
    try {
      await this.statusServer.start();
      logger.main('Status API Server started successfully');
    } catch (error) {
      logger.error('MAIN', 'Failed to start Status API Server:', error);
    }

    logger.main(`[ENV] AUTOSSH_CLEANUP_TOKEN loaded: ${this.configManager.get('autosshCleanupToken') ? '******' : 'NOT FOUND'}`);
  }

  setupIpcHandlers() {
    // Get app config
    ipcMain.handle('get-config', async (event) => {
      const cloudVmConfig = this.configManager.getCloudVmConfig();
      return { 
        success: true, 
        data: {
          cloudVm: cloudVmConfig,
          portRange: {
            start: cloudVmConfig.portRange.start,
            end: cloudVmConfig.portRange.end
          }
        }
      };
    });

    // Get router credentials for frontend API calls
    ipcMain.handle('get-router-credentials', (event) => {
      return this.tunnelManager.getRouterCredentials();
    });

    // Get cloud VM access info
    ipcMain.handle('get-cloud-vm-access', (event) => {
      return this.getCloudVmAccess();
    });

    // Show info dialog
    ipcMain.handle('show-info', (event, { title, message }) => {
      return dialog.showErrorBox(title, message);
    });
    
    // Test router connection
    ipcMain.handle('test-router-connection', async (event, credentials) => {
      try {
        const result = await this.routerManager.testConnection(credentials);
        return { success: true, data: result };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Install router packages
    ipcMain.handle('install-router-packages', async (event, credentials) => {
      try {
        const result = await this.routerManager.installPackages(credentials);
        return { success: true, data: result };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Enable WiFi
    ipcMain.handle('enable-wifi', async (event, credentials) => {
      try {
        const result = await this.routerManager.enableWifi(credentials);
        return { success: true, data: result };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Get WiFi status
    ipcMain.handle('get-wifi-status', async (event, credentials) => {
      try {
        const result = await this.routerManager.getWifiStatus(credentials);
        return result;
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Allocate port for tunnel
    ipcMain.handle('allocate-port', async (event, credentials = null) => {
      try {
        // Pass router credentials to port allocation so they can be stored with the port
        const routerCredentials = credentials ? {
          username: credentials.username,
          password: credentials.password
        } : null;
        
        const port = await this.portAllocator.allocatePort(routerCredentials);
        return { success: true, data: { port } };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Establish tunnel
    ipcMain.handle('establish-tunnel', async (event, { credentials, port }) => {
      try {
        // Get the routerId from PortAllocator to ensure consistency
        const portInfo = this.portAllocator.getPortInfo();
        const routerId = portInfo.routerId;
        
        const result = await this.tunnelManager.establishTunnel(credentials, port, routerId);
        return { success: true, data: result };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Verify NetPilot compatibility
    ipcMain.handle('verify-netpilot-compatibility', async (event, credentials) => {
      try {
        // Connect to router first
        await this.routerManager.ssh.connect({
          host: credentials.host,
          username: credentials.username,
          password: credentials.password,
          port: credentials.port || 22,
          readyTimeout: 10000
        });
        this.routerManager.isConnected = true;
        
        const result = await this.routerManager.verifyNetPilotCompatibility();
        
        // Disconnect after verification
        await this.routerManager.disconnect();
        
        return { success: true, data: result };
      } catch (error) {
        await this.routerManager.disconnect();
        return { success: false, error: error.message };
      }
    });

    // Get tunnel status
    ipcMain.handle('get-tunnel-status', async (event) => {
      try {
        const status = await this.tunnelManager.getStatus();
        return { success: true, data: status };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Disconnect tunnel
    ipcMain.handle('disconnect-tunnel', async (event) => {
      try {
        const result = await this.tunnelManager.stopTunnel();
        return { success: result };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Release allocated port on tunnel disconnect
    ipcMain.handle('release-port', async (event, port) => {
      try {
        const result = await this.portAllocator.releasePort();
        return { success: true, data: result };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Uninstall NetPilot from router
    ipcMain.handle('uninstall-netpilot', async (event, credentials) => {
      try {
        const result = await this.routerManager.uninstallNetPilot(credentials);
        return { success: true, data: result };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Show confirmation dialog
    ipcMain.handle('show-confirm', async (event, { title, message, buttons = ['OK', 'Cancel'] }) => {
      const response = await dialog.showMessageBox(null, {
        type: 'question',
        title: title,
        message: message,
        buttons: buttons,
        defaultId: 0,
        cancelId: 1
      });
      return response.response === 0;
    });

    // Save file dialog
    ipcMain.handle('save-file', async (event, { title, defaultPath, content }) => {
      const response = await dialog.showSaveDialog(null, {
        title: title,
        defaultPath: defaultPath,
        filters: [
          { name: 'Text Files', extensions: ['txt'] },
          { name: 'All Files', extensions: ['*'] }
        ]
      });

      if (!response.canceled && response.filePath) {
        const fs = require('fs').promises;
        await fs.writeFile(response.filePath, content, 'utf8');
        return { success: true, filePath: response.filePath };
      }
      
      return { success: false, error: 'Save cancelled' };
    });

    // Show error dialog
    ipcMain.handle('show-error', async (event, { title, message }) => {
      return dialog.showErrorBox(title, message);
    });

    // Phase 7: Status API and Verification Endpoints
    
    // Start Status API Server
    ipcMain.handle('start-status-server', async (event) => {
      try {
        await this.statusServer.start();
        return { 
          success: true, 
          data: this.statusServer.getServerInfo() 
        };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Stop Status API Server
    ipcMain.handle('stop-status-server', async (event) => {
      try {
        await this.statusServer.stop();
        return { success: true };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Get Status API Server Info
    ipcMain.handle('get-status-server-info', async (event) => {
      try {
        return { 
          success: true, 
          data: this.statusServer.getServerInfo() 
        };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Enhanced Router Verification (Phase 7.1)
    ipcMain.handle('verify-router-setup', async (event, credentials) => {
      try {
        const verification = await this.statusServer.verifyRouterSetup(credentials);
        return { success: true, data: verification };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Tunnel Connectivity Verification (Phase 7.2)
    ipcMain.handle('verify-tunnel-connectivity', async (event) => {
      try {
        const verification = await this.statusServer.verifyTunnelConnectivity();
        return { success: true, data: verification };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Test Command Execution
    ipcMain.handle('test-command-execution', async (event, command) => {
      try {
        const result = await this.statusServer.testCommandExecution(command);
        return { success: true, data: result };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Measure Tunnel Latency
    ipcMain.handle('measure-tunnel-latency', async (event) => {
      try {
        const latency = await this.statusServer.measureTunnelLatency();
        return { success: true, data: latency };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Get Comprehensive Status
    ipcMain.handle('get-comprehensive-status', async (event) => {
      try {
        const status = await this.statusServer.getComprehensiveStatus();
        return { success: true, data: status };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });

    // Reset all data (new)
    ipcMain.handle('reset-all-data', async (event) => {
      try {
        // Show confirmation dialog before resetting
        const { response } = await dialog.showMessageBox({
          type: 'warning',
          buttons: ['Reset Cached Data', 'Cancel'],
          defaultId: 1,
          title: 'Reset Cached User Data',
          message: 'Are you sure you want to reset cached user data?',
          detail: 'This will delete saved router credentials, configuration states, and logs. Your .env file with cloud VM settings will be preserved. The application will restart.',
          checkboxLabel: 'Also clear router profiles',
          checkboxChecked: true
        });

        if (response === 0) {
          // If confirmed, reset cached user data only
          await this.resetAllData();
          return { success: true };
        } else {
          return { success: false, canceled: true };
        }
      } catch (error) {
        return { success: false, error: error.message };
      }
    });
    
    // Router configuration state
    ipcMain.handle('get-router-configuration-state', async (event) => {
      try {
        return { 
          success: true, 
          data: this.routerConfigState 
        };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });
    
    ipcMain.handle('save-router-configuration-state', async (event, state) => {
      try {
        this.routerConfigState = {
          ...state,
          timestamp: Date.now()
        };
        return { success: true };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });
  }

  init() {
    // Set up app event handlers
    app.whenReady().then(() => {
      this.setupIpcHandlers();
      this.setupCredentialHandlers();
      this.createWindow();
    });

    app.on('window-all-closed', async () => {
      // Cleanup resources before closing
      await this.cleanup();
      
      if (process.platform !== 'darwin') {
        app.quit();
      }
    });

    app.on('before-quit', async (event) => {
      // Prevent quit until cleanup is complete
      event.preventDefault();
      await this.cleanup();
      app.exit();
    });

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        this.createWindow();
      }
    });
  }

  async cleanup() {
    logger.main('Cleaning up NetPilot Agent resources...');
    
    try {
      // Stop Status API Server
      if (this.statusServer) {
        await this.statusServer.stop();
        logger.main('Status API Server stopped');
      }

      // Disconnect tunnel
      if (this.tunnelManager && this.tunnelManager.isConnected) {
        await this.tunnelManager.disconnect();
        logger.main('Tunnel disconnected');
      }

      // Disconnect router
      if (this.routerManager && this.routerManager.isConnected) {
        await this.routerManager.disconnect();
        logger.main('Router disconnected');
      }

      // Release allocated port
      if (this.portAllocator && this.portAllocator.allocatedPort) {
        await this.portAllocator.releasePort();
        logger.main('Port released');
      }

      logger.main('NetPilot Agent cleanup completed');
    } catch (error) {
      logger.error('MAIN', 'Error during cleanup:', error);
    }
  }

  async resetAllData() {
    logger.main('Resetting cached user data (preserving .env configuration)...');
    
    try {
      // First perform normal cleanup
      await this.cleanup();
      
      // Delete all stored passwords and credentials
      logger.main('Deleting stored credentials...');
      try {
        await keytar.deletePassword('NetPilotAgent', 'router-password');
      } catch (error) {
        // Ignore if password doesn't exist
        logger.main('No stored router password to delete');
      }
      
      // Reset router configuration state (cached data only)
      logger.main('Resetting router configuration state...');
      this.routerConfigState = {
        configured: false,
        profile: null,
        timestamp: null
      };
      
      // Delete all logs
      logger.main('Deleting log files...');
      const fs = require('fs').promises;
      const logFiles = [
        'main.log', 'config.log', 'tunnel.log', 'router.log',
        'port.log', 'status.log', 'error.log', 'debug.log',
        'custom.log', 'info.log', 'warn.log'
      ];
      
      for (const file of logFiles) {
        const logPath = path.join(this.configManager.getLogsPath(), file);
        try {
          await fs.unlink(logPath);
        } catch (err) {
          // Ignore file not found errors
          if (err.code !== 'ENOENT') {
            logger.warn(`Failed to delete log file ${file}: ${err.message}`);
          }
        }
      }
      
      logger.main('Cached user data reset completed (.env file preserved). Application will restart.');
      
      // Tell the renderer the reset is complete before restarting
      if (this.mainWindow) {
        this.mainWindow.webContents.send('reset-completed');
      }
      
      // Wait a moment for logs to flush
      setTimeout(() => {
        app.relaunch();
        app.exit(0);
      }, 1000);
      
    } catch (error) {
      logger.error('MAIN', 'Error during data reset:', error);
      throw error;
    }
  }
}

// Create and initialize the agent when the app is ready
app.whenReady().then(() => {
  const agent = new NetPilotAgent();
  agent.init();
});

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
  });
}); 