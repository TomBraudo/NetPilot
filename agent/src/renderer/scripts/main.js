// NetPilot Router Agent - Main Renderer Script

// Simple logger for renderer process
const logger = {
  main: (...args) => console.log('[UI]', ...args),
  config: (...args) => console.log('[CONFIG]', ...args),
  error: (...args) => console.error('[ERROR]', ...args),
  warn: (...args) => console.warn('[WARN]', ...args),
  info: (...args) => console.info('[INFO]', ...args)
};

// Generate a UUID if crypto.randomUUID() isn't available
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

class NetPilotAgentUI {
  constructor() {
    this.currentStep = 0;
    this.currentTunnelStep = 0;
    this.isProcessing = false;
    this.isWifiActionInProgress = false;
    this.allocatedPort = null;
    this.appConfig = null;
    this.routerCredentials = null;
    this.routerProfiles = {};
    this.currentRouterProfile = null;
    this.routerConfigured = false;
    this.logs = [];
    this.settings = {
      autoSavePassword: true,
      autoReconnect: true,
      debugMode: false,
      cloudIp: '34.38.207.87',
      cloudPort: 22,
      cloudUser: 'netpilot-agent',
      timeout: 30,
      heartbeatInterval: 60,
      retryAttempts: 3
    };
    
    // Bind methods
    this.init = this.init.bind(this);
    this.loadConfiguration = this.loadConfiguration.bind(this);
    this.loadSavedPassword = this.loadSavedPassword.bind(this);
    this.handleTestConnection = this.handleTestConnection.bind(this);
    this.handleConfigureRouter = this.handleConfigureRouter.bind(this);
    this.handleConnectTunnel = this.handleConnectTunnel.bind(this);
    this.handleEnableWifi = this.handleEnableWifi.bind(this);
    this.handleReconnect = this.handleReconnect.bind(this);
    this.handleDisconnect = this.handleDisconnect.bind(this);
    this.handleUninstall = this.handleUninstall.bind(this);
    this.showNotification = this.showNotification.bind(this);
    this.updateProgress = this.updateProgress.bind(this);
    this.updateStepStatus = this.updateStepStatus.bind(this);
    this.updateConnectionStatus = this.updateConnectionStatus.bind(this);
    this.openSettings = this.openSettings.bind(this);
    this.saveSettings = this.saveSettings.bind(this);
    this.resetSettings = this.resetSettings.bind(this);
    this.resetAllData = this.resetAllData.bind(this);
    this.openLogViewer = this.openLogViewer.bind(this);
    this.refreshLogs = this.refreshLogs.bind(this);
    this.clearLogs = this.clearLogs.bind(this);
    this.exportLogs = this.exportLogs.bind(this);
    this.openHelp = this.openHelp.bind(this);
    this.handleVerifyConfig = this.handleVerifyConfig.bind(this);
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', this.init);
    } else {
      this.init();
    }
  }

  async init() {
    logger.main('NetPilot Router Agent UI initialized');
    
    // Get DOM elements
    this.elements = {
      connectionForm: document.getElementById('connection-form'),
      testConnectionBtn: document.getElementById('test-connection-btn'),
      configureRouterBtn: document.getElementById('configure-router-btn'),
      verifyConfigBtn: document.getElementById('verify-config-btn'),
      connectTunnelBtn: document.getElementById('connect-tunnel-btn'),
      enableWifiBtn: document.getElementById('enable-wifi-btn'),
      enableWifiStatus: document.getElementById('enable-wifi-status'),
      configStatus: document.getElementById('config-status'),
      configDetails: document.getElementById('config-details'),
      progressSection: document.getElementById('progress-section'),
      progressFill: document.getElementById('progress-fill'),
      progressText: document.getElementById('progress-text'),
      statusIndicator: document.getElementById('status-indicator'),
      statusDetails: document.getElementById('status-details'),
      statusActions: document.getElementById('status-actions'),
      reconnectBtn: document.getElementById('reconnect-btn'),
      disconnectBtn: document.getElementById('disconnect-btn'),
      uninstallBtn: document.getElementById('uninstall-btn'),
      settingsBtn: document.getElementById('settings-btn'),
      logsBtn: document.getElementById('logs-btn'),
      helpBtn: document.getElementById('help-btn'),
      aboutBtn: document.getElementById('about-btn'),
      versionText: document.getElementById('version-text'),
      routerIpInput: document.getElementById('router-ip'),
      usernameInput: document.getElementById('username'),
      passwordInput: document.getElementById('password'),
      // Modals
      settingsModal: document.getElementById('settings-modal'),
      logsModal: document.getElementById('logs-modal'),
      helpModal: document.getElementById('help-modal'),
      closeSettings: document.getElementById('close-settings'),
      saveSettings: document.getElementById('save-settings'),
      resetSettings: document.getElementById('reset-settings'),
      resetAllDataBtn: document.getElementById('reset-all-data'),
      refreshLogsBtn: document.getElementById('refresh-logs'),
      clearLogsBtn: document.getElementById('clear-logs'),
      exportLogsBtn: document.getElementById('export-logs'),
      closeLogsBtn: document.getElementById('close-logs-btn'),
      closeHelpBtn: document.getElementById('close-help-btn'),
      closeHelp: document.getElementById('close-help')
    };

    // Load configuration and settings
    await this.loadConfiguration();
    await this.loadSavedPassword();
    this.loadSettings();
    this.loadRouterProfiles();
    this.loadRouterConfigurationState(); // Load router configuration state
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Initialize UI state
    this.updateConnectionStatus('unconfigured', 'Router not configured');
    await this.checkRouterConfiguration();
    
    // Set version info
    if (this.elements.versionText && window.electronAPI) {
      this.elements.versionText.textContent = `v1.0.0 (Electron ${window.electronAPI.version})`;
    }

    // Check if router is already connected
    await this.checkExistingConnection();
    
    // Phase 8: Start coordinated auto-restore process now that UI is ready
    logger.main('🎯 UI initialization complete, triggering coordinated auto-restore...');
    await this.startCoordinatedAutoRestore();
  }

  async loadConfiguration() {
    try {
      const result = await window.electronAPI.getConfig();
      if (result.success) {
        this.appConfig = result.data;
        logger.config('Configuration loaded:', this.appConfig);
        
        // Check if cloud VM password is set
        if (!this.appConfig.cloudVm.password) {
          this.showNotification('Cloud VM password not configured. Please create a .env file with your credentials.', 'warning');
        } else {
          logger.config(`Cloud VM configured: ${this.appConfig.cloudVm.user}@${this.appConfig.cloudVm.ip}`);
        }
      } else {
        logger.error('Failed to load configuration:', result.error);
        this.showNotification('Failed to load configuration', 'error');
      }
    } catch (error) {
      logger.error('Configuration loading error:', error);
      this.showNotification('Configuration loading failed', 'error');
    }
  }

  async loadSavedPassword() {
    try {
      const result = await window.electronAPI.getRouterPassword();
      if (result && result.success && result.password) {
        this.elements.passwordInput.value = result.password;
        this.showNotification('Loaded saved password', 'info');
      }
    } catch (error) {
      logger.error('Failed to load router credentials:', error);
    }
  }

  async loadRouterCredentials() {
    try {
      const result = await window.electronAPI.getRouterCredentials();
      // This is the fix: check if 'result' exists before trying to read its properties.
      if (result && result.success && result.data) {
        this.routerCredentials = result.data;
        console.log('Router credentials loaded:', {
          host: this.routerCredentials.host,
          username: this.routerCredentials.username,
          tunnelPort: this.routerCredentials.tunnelPort,
          isConnected: this.routerCredentials.isConnected
        });
      } else {
        // This case is normal if no connection has been established yet.
        console.log('No router credentials available yet');
        this.routerCredentials = null;
      }
    } catch (error) {
      console.error('Failed to load router credentials:', error);
      this.routerCredentials = null;
    }
  }

  setupEventListeners() {
    // Connection form actions
    this.elements.testConnectionBtn?.addEventListener('click', this.handleTestConnection);
    this.elements.configureRouterBtn?.addEventListener('click', this.handleConfigureRouter);
    this.elements.verifyConfigBtn?.addEventListener('click', this.handleVerifyConfig);
    this.elements.connectTunnelBtn?.addEventListener('click', this.handleConnectTunnel);
    this.elements.enableWifiBtn?.addEventListener('click', this.handleEnableWifi);
    
    // Status actions
    this.elements.reconnectBtn?.addEventListener('click', this.handleReconnect);
    this.elements.disconnectBtn?.addEventListener('click', this.handleDisconnect);
    this.elements.uninstallBtn?.addEventListener('click', this.handleUninstall);
    
    // Utility buttons
    this.elements.settingsBtn?.addEventListener('click', this.openSettings);
    this.elements.logsBtn?.addEventListener('click', this.openLogViewer);
    this.elements.helpBtn?.addEventListener('click', this.openHelp);
    this.elements.aboutBtn?.addEventListener('click', () => this.showAbout());
    
    // Enter key in form fields
    const formFields = [
      this.elements.routerIpInput,
      this.elements.usernameInput,
      this.elements.passwordInput
    ];

    formFields.forEach(field => {
      if (field) {
        field.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            this.handleTestConnection(e);
          }
        });
      }
    });

    // Modal event listeners
    this.setupModalListeners();

    // Password field - allow empty for "no password" routers
    const passwordField = document.getElementById('password');
    if (passwordField) {
      passwordField.addEventListener('input', (e) => {
        // Remove required attribute if user wants no password
        if (e.target.value === '') {
          e.target.removeAttribute('required');
        } else {
          e.target.setAttribute('required', 'required');
        }
      });
    }

    // Settings modal
    this.elements.closeSettings?.addEventListener('click', () => this.hideModal(this.elements.settingsModal));
    this.elements.saveSettings?.addEventListener('click', this.saveSettings);
    this.elements.resetSettings?.addEventListener('click', this.resetSettings);
    
    // Reset all data button
    this.elements.resetAllDataBtn?.addEventListener('click', this.resetAllData);
    
    // Logs modal
    this.elements.closeLogsBtn?.addEventListener('click', () => this.hideModal(this.elements.logsModal));
    this.elements.refreshLogsBtn?.addEventListener('click', this.refreshLogs);
    this.elements.clearLogsBtn?.addEventListener('click', this.clearLogs);
    this.elements.exportLogsBtn?.addEventListener('click', this.exportLogs);
    
    // Help modal
    this.elements.closeHelpBtn?.addEventListener('click', () => this.hideModal(this.elements.helpModal));
    this.elements.closeHelp?.addEventListener('click', () => this.hideModal(this.elements.helpModal));
    
    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        this.filterLogs(e.target.dataset.level);
      });
    });
    
    // Listen for reset complete
    window.electronAPI.onResetComplete(() => {
      this.showNotification('✅ Reset Complete: Application will restart now.', 'success');
    });
  }

  setupModalListeners() {
    // Settings modal
    document.getElementById('close-settings')?.addEventListener('click', () => {
      this.closeModal(this.elements.settingsModal);
    });

    document.getElementById('save-settings')?.addEventListener('click', () => {
      this.saveSettings();
    });

    document.getElementById('reset-settings')?.addEventListener('click', () => {
      this.resetSettings();
    });

    // Settings tabs
    document.querySelectorAll('.tab-btn').forEach(tab => {
      tab.addEventListener('click', (e) => {
        this.switchTab(e.target.dataset.tab);
      });
    });

    // Logs modal
    document.getElementById('close-logs')?.addEventListener('click', () => {
      this.closeModal(this.elements.logsModal);
    });

    document.getElementById('close-logs-btn')?.addEventListener('click', () => {
      this.closeModal(this.elements.logsModal);
    });

    document.getElementById('refresh-logs')?.addEventListener('click', () => {
      this.refreshLogs();
    });

    document.getElementById('clear-logs')?.addEventListener('click', () => {
      this.clearLogs();
    });

    document.getElementById('export-logs')?.addEventListener('click', () => {
      this.exportLogs();
    });

    // Log filters
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        this.filterLogs(e.target.dataset.level);
      });
    });

    // Help modal
    document.getElementById('close-help')?.addEventListener('click', () => {
      this.closeModal(this.elements.helpModal);
    });

    document.getElementById('close-help-btn')?.addEventListener('click', () => {
      this.closeModal(this.elements.helpModal);
    });

    // Close modals on backdrop click
    [this.elements.settingsModal, this.elements.logsModal, this.elements.helpModal].forEach(modal => {
      if (modal) {
        modal.addEventListener('click', (e) => {
          if (e.target === modal) {
            this.closeModal(modal);
          }
        });
      }
    });
  }

  async checkExistingConnection() {
    try {
      await this.loadRouterCredentials();
      if (this.routerCredentials && this.routerCredentials.isConnected) {
        // Get comprehensive verification status
        try {
          const verificationResult = await window.electronAPI.verifyTunnelConnectivity();
          if (verificationResult.success && verificationResult.data) {
            const verification = verificationResult.data;
            if (verification.overall) {
              this.updateConnectionStatus('connected', `Tunnel verified and active on port ${this.routerCredentials.tunnelPort}`);
            } else {
              this.updateConnectionStatus('warning', `Tunnel on port ${this.routerCredentials.tunnelPort} - Issues: ${verification.details?.join(', ') || 'Verification failed'}`);
            }
          } else {
            // Fallback to basic status if verification fails
            this.updateConnectionStatus('connected', `Connected via tunnel port ${this.routerCredentials.tunnelPort}`);
          }
        } catch (verifyError) {
          // Verification failed, show basic status
          this.updateConnectionStatus('warning', `Connected via tunnel port ${this.routerCredentials.tunnelPort} - Verification unavailable`);
        }
        this.showStatusActions();
      }
    } catch (error) {
      console.log('No existing connection found');
    }
  }

  async startCoordinatedAutoRestore() {
    try {
      logger.main('🎯 Starting coordinated auto-restore with UI feedback...');
      
      // Set up event listeners for auto-restore progress
      window.electronAPI.onAutoRestoreProgress(this.handleAutoRestoreProgress.bind(this));
      window.electronAPI.onAutoRestoreComplete(this.handleAutoRestoreComplete.bind(this));
      window.electronAPI.onAutoRestoreError(this.handleAutoRestoreError.bind(this));
      
      // Show progress and start auto-restore
      this.showTunnelProgress();
      this.updateProgress(0, 'Starting auto-restore...');
      this.updateTunnelStepStatus(1, 'active');
      
      // Signal to main process that UI is ready and start auto-restore
      const result = await window.electronAPI.uiReadyStartAutoRestore();
      
      if (!result.success) {
        throw new Error(result.error);
      }
      
    } catch (error) {
      logger.error('Failed to start coordinated auto-restore:', error);
      this.handleAutoRestoreError({ error: error.message });
    }
  }

  handleAutoRestoreProgress(data) {
    logger.main(`Auto-restore progress: Step ${data.step} - ${data.message}`);
    
    if (data.step === 1) {
      this.updateProgress(25, data.message);
      this.updateTunnelStepStatus(1, 'completed');
      this.updateTunnelStepStatus(2, 'active');
    } else if (data.step === 2) {
      this.updateProgress(75, data.message);
      this.updateTunnelStepStatus(2, 'completed');
    }
  }

  async handleAutoRestoreComplete(restoration) {
    try {
      logger.info('Auto-restore completed with results:', restoration);
      
      this.updateProgress(100, 'Auto-restore completed');
      this.updateTunnelStepStatus(3, 'completed');
      
      // Update UI based on restored state
      if (restoration.tunnelRestored) {
        const tunnelData = restoration.details.tunnel;
        this.allocatedPort = tunnelData.port;
        
        // Set the button states for connected status
        this.setButtonState('connectTunnelBtn', 'hidden');
        this.setButtonState('disconnectTunnelBtn', 'normal');
        this.setButtonState('reconnectTunnelBtn', 'normal');
        
        if (tunnelData.status === 'restored_restarted') {
          this.updateConnectionStatus('connected', `Tunnel auto-restored and restarted on port ${tunnelData.port}`);
          this.showNotification(`🔄 Tunnel auto-restored and restarted on port ${tunnelData.port}`, 'success');
        } else {
          this.updateConnectionStatus('connected', `Tunnel auto-restored on port ${tunnelData.port}`);
          this.showNotification(`✅ Tunnel auto-restored on port ${tunnelData.port}`, 'success');
        }
        
        // Show connection actions since tunnel is restored
        this.showStatusActions();
        
        // Load router credentials if available
        const routerCreds = await window.electronAPI.getRouterCredentials();
        if (routerCreds && routerCreds.host) {
          this.elements.routerIpInput.value = routerCreds.host;
          this.elements.usernameInput.value = routerCreds.username;
          if (routerCreds.password) {
            this.elements.passwordInput.value = routerCreds.password;
          }
          
          // Store credentials for current session
          this.routerCredentials = {
            host: routerCreds.host,
            username: routerCreds.username,
            password: routerCreds.password,
            port: routerCreds.port || 22,
            tunnelPort: tunnelData.port
          };
        }
        
        // Verify the tunnel is actually working
        try {
          const statusResult = await window.electronAPI.getTunnelStatus();
          if (statusResult.success && statusResult.data) {
            const status = statusResult.data;
            logger.info('Tunnel status verified:', status);
            
            if (status.isConnected) {
              logger.info('✅ Auto-restored tunnel verified as active');
            } else {
              logger.warn('⚠️ Auto-restored tunnel status shows disconnected');
              this.updateConnectionStatus('warning', `Tunnel restored on port ${tunnelData.port} but status unclear`);
            }
          }
        } catch (statusError) {
          logger.warn('Could not verify tunnel status:', statusError);
        }
        
      } else if (restoration.portRestored) {
        const portData = restoration.details.port;
        this.allocatedPort = portData.port;
        this.showNotification(`📦 Port allocation restored: ${portData.port}`, 'info');
      } else {
        logger.info('No previous state found to restore - starting fresh');
        this.showNotification('No previous connection to restore', 'info');
      }
      
      // Hide progress after a short delay
      setTimeout(() => {
        const progressSection = document.getElementById('progress-section');
        if (progressSection) {
          progressSection.style.display = 'none';
        }
      }, 2000);
      
    } catch (error) {
      logger.error('Error handling auto-restore completion:', error);
      this.handleAutoRestoreError({ error: error.message });
    }
  }

  handleAutoRestoreError(data) {
    logger.error('Auto-restore failed:', data.error);
    this.updateProgress(0, 'Auto-restore failed');
    this.updateTunnelStepStatus(1, 'error');
    this.showNotification(`Auto-restore failed: ${data.error}`, 'error');
    
    // Hide progress after showing error
    setTimeout(() => {
      const progressSection = document.getElementById('progress-section');
      if (progressSection) {
        progressSection.style.display = 'none';
      }
    }, 3000);
  }

  async handleTestConnection(event) {
    event.preventDefault();
    
    if (this.isProcessing) return;
    
    const credentials = this.getFormCredentials();
    if (!credentials) return;

    this.setButtonLoading(this.elements.testConnectionBtn, true);
    this.showNotification('Testing connection...', 'info');
    
    try {
      const result = await window.electronAPI.testRouterConnection(credentials);
      
      if (result.success) {
        this.showNotification('Connection successful!', 'success');
        // Save password on successful connection
        await window.electronAPI.saveRouterPassword(credentials.password);
        
        // Check WiFi status after successful connection test
        this.showNotification('Checking WiFi interface status...', 'info');
        await this.checkWifiStatus();
      } else {
        this.showNotification(`Connection failed: ${result.error}`, 'error');
        console.error('Connection test failed:', result.error);
      }
    } catch (error) {
      console.error('Test connection error:', error);
      this.showNotification('Connection test failed', 'error');
    } finally {
      this.setButtonLoading(this.elements.testConnectionBtn, false);
    }
  }

  async executeStep(stepNumber, message, asyncFn) {
    this.currentStep = stepNumber;
    this.updateStepStatus(stepNumber, 'active');
    this.updateProgress((stepNumber - 1) * 20, message); // Changed from 25 to 20 for 5 steps

    try {
      const result = await asyncFn();
      this.updateStepStatus(stepNumber, 'completed');
      this.updateProgress(stepNumber * 20, `Step ${stepNumber} completed`); // Changed from 25 to 20 for 5 steps
      return result;
    } catch (error) {
      this.updateStepStatus(stepNumber, 'error');
      throw error;
    }
  }

  getFormCredentials() {
    const routerIp = document.getElementById('router-ip')?.value;
    const username = document.getElementById('username')?.value;
    const password = document.getElementById('password')?.value;
    const cloudVmIp = document.getElementById('cloud-vm-ip')?.value || '34.38.207.87';
    const sshPort = document.getElementById('ssh-port')?.value || '22';

    // Validate inputs
    if (!routerIp || !username) {
      this.showNotification('Please fill in all required fields', 'error');
      return null;
    }

    // Validate IP format
    const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    if (!ipRegex.test(routerIp)) {
      this.showNotification('Please enter a valid IP address', 'error');
      return null;
    }

    return {
      host: routerIp,
      username: username,
      password: password || '', // Allow empty password
      port: parseInt(sshPort),
      cloudVmIp: cloudVmIp
    };
  }

  showProgressSection() {
    if (this.elements.progressSection) {
      this.elements.progressSection.style.display = 'block';
      this.elements.progressSection.scrollIntoView({ behavior: 'smooth' });
    }
  }

  showConfigurationProgress() {
    this.showProgressSection();
    
    // Show configuration steps, hide tunnel steps
    const configSteps = document.getElementById('config-progress-steps');
    const tunnelSteps = document.getElementById('tunnel-progress-steps');
    const progressTitle = document.getElementById('progress-title');
    
    if (configSteps) configSteps.style.display = 'flex';
    if (tunnelSteps) tunnelSteps.style.display = 'none';
    if (progressTitle) progressTitle.textContent = 'Router Configuration Progress';
    
    // Reset all config step statuses
    for (let i = 1; i <= 5; i++) {
      this.updateConfigStepStatus(i, 'pending');
    }
    this.currentStep = 0;
  }

  showTunnelProgress() {
    this.showProgressSection();
    
    // Show tunnel steps, hide configuration steps
    const configSteps = document.getElementById('config-progress-steps');
    const tunnelSteps = document.getElementById('tunnel-progress-steps');
    const progressTitle = document.getElementById('progress-title');
    
    if (configSteps) configSteps.style.display = 'none';
    if (tunnelSteps) tunnelSteps.style.display = 'flex';
    if (progressTitle) progressTitle.textContent = 'Tunnel Connection Progress';
    
    // Reset all tunnel step statuses
    for (let i = 1; i <= 4; i++) {
      this.updateTunnelStepStatus(i, 'pending');
    }
    this.currentTunnelStep = 0;
  }

  updateProgress(percentage, text) {
    if (this.elements.progressFill) {
      this.elements.progressFill.style.width = `${percentage}%`;
    }
    if (this.elements.progressText) {
      this.elements.progressText.textContent = text;
    }
  }

  updateStepStatus(stepNumber, status) {
    const step = document.querySelector(`[data-step="${stepNumber}"]`);
    const statusElement = document.getElementById(`step-${stepNumber}-status`);
    
    if (step) {
      // Remove existing status classes
      step.classList.remove('active', 'completed', 'error');
      step.classList.add(status);
    }
    
    if (statusElement) {
      statusElement.textContent = status;
    }
  }

  updateConfigStepStatus(stepNumber, status) {
    const configSteps = document.getElementById('config-progress-steps');
    if (!configSteps) return;
    
    const step = configSteps.querySelector(`[data-step="${stepNumber}"]`);
    const statusElement = document.getElementById(`step-${stepNumber}-status`);
    
    if (step) {
      step.classList.remove('active', 'completed', 'error');
      step.classList.add(status);
    }
    
    if (statusElement) {
      statusElement.textContent = status;
    }
  }

  updateTunnelStepStatus(stepNumber, status) {
    const tunnelSteps = document.getElementById('tunnel-progress-steps');
    if (!tunnelSteps) return;
    
    const step = tunnelSteps.querySelector(`[data-step="${stepNumber}"]`);
    const statusElement = document.getElementById(`tunnel-step-${stepNumber}-status`);
    
    if (step) {
      step.classList.remove('active', 'completed', 'error');
      step.classList.add(status);
    }
    
    if (statusElement) {
      statusElement.textContent = status;
    }
  }

  async executeConfigStep(stepNumber, message, asyncFn) {
    this.currentStep = stepNumber;
    this.updateConfigStepStatus(stepNumber, 'active');
    this.updateProgress((stepNumber - 1) * 20, message);

    try {
      const result = await asyncFn();
      this.updateConfigStepStatus(stepNumber, 'completed');
      this.updateProgress(stepNumber * 20, `${message} completed`);
      return result;
    } catch (error) {
      this.updateConfigStepStatus(stepNumber, 'error');
      throw error;
    }
  }

  async executeTunnelStep(stepNumber, message, asyncFn) {
    this.currentTunnelStep = stepNumber;
    this.updateTunnelStepStatus(stepNumber, 'active');
    this.updateProgress((stepNumber - 1) * 25, message);

    try {
      const result = await asyncFn();
      this.updateTunnelStepStatus(stepNumber, 'completed');
      this.updateProgress(stepNumber * 25, `${message} completed`);
      return result;
    } catch (error) {
      this.updateTunnelStepStatus(stepNumber, 'error');
      throw error;
    }
  }

  updateConnectionStatus(status, details) {
    const statusDot = this.elements.statusIndicator?.querySelector('.status-dot');
    const statusText = this.elements.statusIndicator?.querySelector('.status-text');
    
    if (statusDot) {
      statusDot.className = `status-dot ${status}`;
    }
    
    if (statusText) {
      const statusLabels = {
        unconfigured: '⚪ Router not configured',
        configuring: '🔄 Configuring router',
        'configured-disconnected': '✅ Ready to connect',
        connecting: '🔄 Connecting tunnel',
        connected: '✅ Connected',
        reconnecting: '🔄 Reconnecting',
        error: '❌ Connection failed'
      };
      statusText.textContent = statusLabels[status] || status;
    }
    
    if (this.elements.statusDetails) {
      // Enhanced status details with better messaging
      let enhancedDetails = details;
      if (status === 'connected' && this.allocatedPort) {
        enhancedDetails = `${details} (Port: ${this.allocatedPort})`;
      } else if (status === 'connecting') {
        enhancedDetails = `${details}...`;
      } else if (status === 'error') {
        enhancedDetails = `${details}. Please check your credentials and try again.`;
      }
      this.elements.statusDetails.innerHTML = `<p>${enhancedDetails}</p>`;
    }

    // Update button visibility based on connection state
    this.updateButtonVisibility(status);

    // Update status card styling
    this.updateStatusCardStyling(status);

    // Add to logs
    this.addLog('INFO', `Status: ${status} - ${details}`);
  }

  updateStatusCardStyling(status) {
    const statusCard = this.elements.statusCard;
    if (!statusCard) return;

    // Remove all status classes
    statusCard.classList.remove('unconfigured', 'configuring', 'configured-disconnected', 'connecting', 'connected', 'reconnecting', 'error');
    
    // Add current status class  
    statusCard.classList.add(status);
  }

  updateButtonVisibility(connectionState) {
    // Define button visibility matrix based on connection state
    const buttonStates = {
      'unconfigured': {
        testConnection: { visible: true, enabled: true },
        enableWifi: { visible: true, enabled: true },
        configureRouter: { visible: true, enabled: true },
        connectTunnel: { visible: false, enabled: false },
        reconnect: { visible: false, enabled: false },
        disconnect: { visible: false, enabled: false },
        uninstall: { visible: false, enabled: false }
      },
      'configuring': {
        testConnection: { visible: false, enabled: false },
        enableWifi: { visible: false, enabled: false },
        configureRouter: { visible: true, enabled: false, loading: true },
        connectTunnel: { visible: false, enabled: false },
        reconnect: { visible: false, enabled: false },
        disconnect: { visible: false, enabled: false },
        uninstall: { visible: false, enabled: false }
      },
      'configured-disconnected': {
        testConnection: { visible: true, enabled: true },
        enableWifi: { visible: true, enabled: true },
        configureRouter: { visible: false, enabled: false },
        connectTunnel: { visible: true, enabled: true },
        reconnect: { visible: false, enabled: false },
        disconnect: { visible: false, enabled: false },
        uninstall: { visible: true, enabled: true }
      },
      'connecting': {
        testConnection: { visible: false, enabled: false },
        enableWifi: { visible: false, enabled: false },
        configureRouter: { visible: false, enabled: false },
        connectTunnel: { visible: true, enabled: false, loading: true },
        reconnect: { visible: false, enabled: false },
        disconnect: { visible: false, enabled: false },
        uninstall: { visible: false, enabled: false }
      },
      'connected': {
        testConnection: { visible: true, enabled: true },
        enableWifi: { visible: true, enabled: true },
        configureRouter: { visible: false, enabled: false },
        connectTunnel: { visible: false, enabled: false },
        reconnect: { visible: true, enabled: true },
        disconnect: { visible: true, enabled: true },
        uninstall: { visible: true, enabled: true }
      },
      'reconnecting': {
        testConnection: { visible: false, enabled: false },
        enableWifi: { visible: false, enabled: false },
        configureRouter: { visible: false, enabled: false },
        connectTunnel: { visible: false, enabled: false },
        reconnect: { visible: true, enabled: false, loading: true },
        disconnect: { visible: true, enabled: true },
        uninstall: { visible: false, enabled: false }
      },
      'error': {
        testConnection: { visible: true, enabled: true },
        enableWifi: { visible: true, enabled: true },
        configureRouter: { visible: true, enabled: true },
        connectTunnel: { visible: false, enabled: false },
        reconnect: { visible: false, enabled: false },
        disconnect: { visible: false, enabled: false },
        uninstall: { visible: true, enabled: true }
      }
    };

    const currentStates = buttonStates[connectionState] || buttonStates['unconfigured'];

    // Apply button states
    this.setButtonState('testConnectionBtn', currentStates.testConnection);
    this.setButtonState('enableWifiBtn', currentStates.enableWifi);
    this.setButtonState('configureRouterBtn', currentStates.configureRouter);
    this.setButtonState('connectTunnelBtn', currentStates.connectTunnel);
    this.setButtonState('reconnectBtn', currentStates.reconnect);
    this.setButtonState('disconnectBtn', currentStates.disconnect);
    this.setButtonState('uninstallBtn', currentStates.uninstall);

    // Show/hide status actions section based on visibility of management buttons
    const hasVisibleManagementActions = currentStates.reconnect.visible || 
                                       currentStates.disconnect.visible || 
                                       currentStates.uninstall.visible;
    
    if (hasVisibleManagementActions) {
      this.showStatusActions();
    } else {
      this.hideStatusActions();
    }
  }

  setButtonState(buttonElementKey, state) {
    const button = this.elements[buttonElementKey];
    if (!button) return;

    // Handle visibility
    if (state.visible === false) {
      button.style.display = 'none';
    } else {
      button.style.display = '';
    }

    // Handle enabled/disabled state
    button.disabled = !state.enabled;

    // Handle loading state
    if (state.loading) {
      this.setButtonLoading(button, true);
    } else if (!state.loading && state.enabled) {
      this.setButtonLoading(button, false);
    }

    // Add visual feedback classes
    button.classList.toggle('btn-disabled', !state.enabled);
    button.classList.toggle('btn-hidden', !state.visible);
  }

  setButtonLoading(button, loading) {
    if (!button) return;
    
    const spinner = button.querySelector('.btn-spinner');
    const text = button.querySelector('.btn-text');
    
    if (loading) {
      button.disabled = true;
      if (spinner) spinner.style.display = 'inline-block';
      if (text) text.style.opacity = '0.7';
    } else {
      button.disabled = false;
      if (spinner) spinner.style.display = 'none';
      if (text) text.style.opacity = '1';
    }
  }

  showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    if (!container) return;

    // Create or get existing shared backdrop for all notifications
    let backdrop = document.querySelector('.notification-backdrop');
    if (!backdrop) {
      backdrop = document.createElement('div');
      backdrop.className = 'notification-backdrop';
      document.body.appendChild(backdrop);
      
      // Click outside to dismiss ALL notifications
      backdrop.addEventListener('click', () => {
        this.removeAllNotifications();
      });
    }

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Extract emoji from message for cleaner display
    const emojiMatch = message.match(/^([✅❌⚠️🔒⚙️📋]+)\s*(.*)/);
    const emoji = emojiMatch ? emojiMatch[1] : this.getNotificationIcon(type);
    const cleanMessage = emojiMatch ? emojiMatch[2] : message;
    
    notification.innerHTML = `
      <div style="display: flex; align-items: center; gap: 0.5rem; font-weight: 500; margin-bottom: 0.25rem;">
        <span style="font-size: 1rem;">${emoji}</span>
        <span>${this.getNotificationTitle(type)}</span>
      </div>
      <div style="font-size: 0.85rem; line-height: 1.4;">${cleanMessage}</div>
    `;

    container.appendChild(notification);

    // Auto-remove after 6 seconds
    const autoRemove = setTimeout(() => {
      this.removeNotification(notification);
    }, 6000);

    // Allow manual dismiss on click
    notification.addEventListener('click', () => {
      clearTimeout(autoRemove);
      this.removeNotification(notification);
    });

    // Store timeout for cleanup
    notification._autoRemove = autoRemove;
  }

  removeNotification(notification) {
    if (notification && notification.parentNode) {
      // Clear any pending auto-remove timeout
      if (notification._autoRemove) {
        clearTimeout(notification._autoRemove);
      }
      notification.parentNode.removeChild(notification);
    }
    
    // Remove backdrop if no more notifications
    this.cleanupBackdrop();
  }

  removeAllNotifications() {
    const container = document.getElementById('notification-container');
    if (!container) return;

    // Get all notifications and clear their timeouts
    const notifications = container.querySelectorAll('.notification');
    notifications.forEach(notification => {
      if (notification._autoRemove) {
        clearTimeout(notification._autoRemove);
      }
    });

    // Clear all notifications
    container.innerHTML = '';
    
    // Remove backdrop
    this.cleanupBackdrop();
  }

  cleanupBackdrop() {
    const container = document.getElementById('notification-container');
    const backdrop = document.querySelector('.notification-backdrop');
    
    // Remove backdrop if no notifications remain
    if (backdrop && container && container.children.length === 0) {
      backdrop.parentNode.removeChild(backdrop);
    }
  }

  getNotificationTitle(type) {
    const titles = {
      success: 'Success',
      error: 'Error',
      warning: 'Warning',
      info: 'Information'
    };
    return titles[type] || 'Notification';
  }

  getNotificationIcon(type) {
    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: '📋'
    };
    return icons[type] || '📋';
  }

  async showAboutDialog() {
    // Build configuration info
    let configInfo = '';
    if (this.appConfig) {
      configInfo = `\n\nConfiguration:
• Cloud VM: ${this.appConfig.cloudVm.user}@${this.appConfig.cloudVm.ip}:${this.appConfig.cloudVm.port}
• Password: ${this.appConfig.cloudVm.password ? 'Configured' : 'Not Set'}
• Port Range: ${this.appConfig.portRange.min}-${this.appConfig.portRange.max}`;
    }

    // Build router info
    let routerInfo = '';
    if (this.routerCredentials) {
      routerInfo = `\n\nRouter Connection:
• Host: ${this.routerCredentials.host}
• Username: ${this.routerCredentials.username}
• Tunnel Port: ${this.routerCredentials.tunnelPort}
• Status: ${this.routerCredentials.isConnected ? 'Connected' : 'Disconnected'}`;
    }

    const aboutMessage = `NetPilot Router Agent v1.0.0

A powerful tool to automate OpenWrt router setup and establish secure tunnels to NetPilot Cloud.

Features:
• Automated package installation
• Secure SSH tunnel establishment  
• Multi-user support
• Real-time connection monitoring

Built with Electron ${window.electronAPI?.version || 'Unknown'}${configInfo}${routerInfo}

© 2024 NetPilot Team`;

    await window.electronAPI.showInfo({
      title: 'About NetPilot Router Agent',
      message: aboutMessage
    });
  }

  // Public method for external access to router credentials
  getRouterApiCredentials() {
    return this.routerCredentials ? {
      host: this.routerCredentials.host,
      username: this.routerCredentials.username,
      password: this.routerCredentials.password,
      port: this.routerCredentials.port,
      tunnelPort: this.routerCredentials.tunnelPort,
      cloudVmIp: this.routerCredentials.cloudVmIp
    } : null;
  }

  async handleEnableWifi() {
    // Prevent multiple simultaneous requests
    if (this.isWifiActionInProgress) return;
    
    const credentials = this.getFormCredentials();
    if (!credentials) return;

    this.isWifiActionInProgress = true;
    this.setButtonLoading(this.elements.enableWifiBtn, true);
    this.elements.enableWifiStatus.textContent = 'Checking WiFi status...';
    this.elements.enableWifiStatus.className = 'status-text';
    this.showNotification('Checking current WiFi status...', 'info');

    try {
      // First check current WiFi status
      const statusResult = await window.electronAPI.getWifiStatus(credentials);
      
      if (statusResult.success && statusResult.status) {
        const wifiStatus = statusResult.status;
        const statusText = `WiFi: ${wifiStatus.isEnabled ? 'Enabled' : 'Disabled'} | SSID: ${wifiStatus.ssid} | Mode: ${wifiStatus.hwMode} | Channel: ${wifiStatus.channel}`;
        
        if (wifiStatus.isEnabled) {
          this.elements.enableWifiStatus.textContent = statusText;
          this.elements.enableWifiStatus.classList.add('success');
          this.showNotification(`✅ WiFi is already enabled. ${statusText}`, 'success');
          return;
        } else {
          this.elements.enableWifiStatus.textContent = 'WiFi is disabled, enabling...';
          this.showNotification('WiFi is currently disabled. Enabling...', 'info');
        }
      }
      
      // Enable WiFi if it's disabled
      const result = await window.electronAPI.enableWifi(credentials);
      if (result.success) {
        const successMessage = result.data.message;
        const statusInfo = result.data.status ? 
          ` | Mode: ${result.data.status.hwMode} | Channel: ${result.data.status.channel}` : '';
        
        this.showNotification(`✅ ${successMessage}`, 'success');
        this.elements.enableWifiStatus.textContent = `${successMessage}${statusInfo}`;
        this.elements.enableWifiStatus.classList.add('success');
        
        // Save password on successful action
        await window.electronAPI.saveRouterPassword(credentials.password);
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      this.showNotification(`❌ Failed to enable WiFi: ${error.message}`, 'error');
      this.elements.enableWifiStatus.textContent = 'Failed to enable WiFi';
      this.elements.enableWifiStatus.classList.add('error');
      console.error('Enable WiFi error:', error);
    } finally {
      this.setButtonLoading(this.elements.enableWifiBtn, false);
      this.isWifiActionInProgress = false;
    }
  }

  async checkWifiStatus() {
    const credentials = this.getFormCredentials();
    if (!credentials) return;

    try {
      const result = await window.electronAPI.getWifiStatus(credentials);
      if (result.success && result.status) {
        const wifiStatus = result.status;
        const statusText = `WiFi: ${wifiStatus.isEnabled ? 'Enabled' : 'Disabled'} | SSID: ${wifiStatus.ssid} | Mode: ${wifiStatus.hwMode} | Channel: ${wifiStatus.channel}`;
        this.elements.enableWifiStatus.textContent = statusText;
        this.elements.enableWifiStatus.className = wifiStatus.isEnabled ? 'status-text success' : 'status-text';
        return wifiStatus;
      }
    } catch (error) {
      console.error('Failed to check WiFi status:', error);
      this.elements.enableWifiStatus.textContent = 'Unable to check WiFi status';
      this.elements.enableWifiStatus.className = 'status-text error';
    }
  }

  async handleReconnect(event) {
    event.preventDefault();
    
    if (this.isProcessing) return;
    
    this.isProcessing = true;
    this.updateConnectionStatus('reconnecting', 'Attempting to reconnect tunnel');
    this.showNotification('Reconnecting tunnel...', 'info');
    
    try {
      // Use existing credentials for reconnection
      if (!this.routerCredentials) {
        throw new Error('No previous connection found');
      }

      const credentials = {
        host: this.routerCredentials.host,
        username: this.routerCredentials.username,
        password: this.routerCredentials.password,
        port: this.routerCredentials.port || 22
      };

      // Re-establish tunnel without full installation
      const result = await window.electronAPI.establishTunnel({
        credentials,
        port: this.routerCredentials.tunnelPort
      });
      
      if (result.success) {
        this.updateConnectionStatus('connected', `Tunnel active and accessible on port ${this.routerCredentials.tunnelPort}`);
        this.showNotification('✅ Tunnel reconnected successfully!', 'success');
        this.addLog('INFO', 'Tunnel reconnected successfully');
      } else {
        throw new Error(result.error);
      }
      
    } catch (error) {
      console.error('Reconnection error:', error);
      this.updateConnectionStatus('error', `Reconnection failed: ${error.message}`);
      this.showNotification(`❌ Reconnection failed: ${error.message}`, 'error');
      this.addLog('ERROR', `Reconnection failed: ${error.message}`);
    } finally {
      this.isProcessing = false;
      // Button states are managed by updateConnectionStatus() -> updateButtonVisibility()
    }
  }

  async handleDisconnect(event) {
    event.preventDefault();
    
    if (this.isProcessing) return;
    
    const confirmed = await window.electronAPI.showConfirm({
      title: 'Disconnect Router',
      message: 'Are you sure you want to disconnect the tunnel? This will stop remote access to your router.',
      buttons: ['Disconnect', 'Cancel']
    });
    
    if (!confirmed) return;
    
    this.isProcessing = true;
    this.showNotification('Disconnecting...', 'info');
    
    try {
      const result = await window.electronAPI.disconnectTunnel();
      
      if (result.success) {
        // Return to configured-disconnected state if router is still configured
        if (this.currentRouterProfile && this.currentRouterProfile.isConfigured) {
          this.updateConnectionStatus('configured-disconnected', 'Tunnel disconnected - router ready for reconnection');
        } else {
          this.updateConnectionStatus('unconfigured', 'Tunnel disconnected');
        }
        this.showNotification('✅ Tunnel disconnected successfully', 'success');
        this.addLog('INFO', 'Tunnel disconnected by user');
      } else {
        throw new Error(result.error);
      }
      
    } catch (error) {
      console.error('Disconnect error:', error);
      this.showNotification(`❌ Disconnect failed: ${error.message}`, 'error');
      this.addLog('ERROR', `Disconnect failed: ${error.message}`);
    } finally {
      this.isProcessing = false;
      // Button states are managed by updateConnectionStatus() -> updateButtonVisibility()
    }
  }

  async handleUninstall(event) {
    event.preventDefault();

    if (this.isProcessing) return;

    const confirmed = await window.electronAPI.showConfirm({
      title: 'Uninstall NetPilot',
      message: 'This will remove NetPilot configurations and cleanup packages from your router. Continue?',
      buttons: ['Uninstall', 'Cancel']
    });

    if (!confirmed) return;

    this.isProcessing = true;
    const button = this.elements.uninstallBtn;
    this.setButtonLoading(button, true);
    const statusSection = document.getElementById('connection-status-section');

    try {
      this.showNotification('Uninstalling NetPilot from router...', 'info');
      this.addLog('INFO', 'Starting NetPilot uninstallation from router');

      const credentials = this.getFormCredentials();
      
      if (!this.validateCredentials(credentials)) {
        this.isProcessing = false;
        this.setButtonLoading(button, false);
        return;
      }

      // Call uninstall API
      const result = await window.electronAPI.uninstallNetPilot(credentials);
      
      if (result.success) {
        // Reset router configuration state
        this.routerConfigured = false;
        this.saveRouterConfigurationState();
        
        // Update UI elements
        this.updateRouterConfigButtonsVisibility();
        
        // Show connection status section again
        if (statusSection) statusSection.style.display = 'block';

        this.showNotification('✅ NetPilot uninstalled successfully from router', 'success');
        this.addLog('INFO', 'NetPilot uninstalled successfully from router');
        
        // Reset connection status
        this.updateConnectionStatus('unconfigured', 'Router not configured');
        
        // Clear router profile
        if (this.currentRouterProfile) {
          const routerKey = `${this.currentRouterProfile.host}:${this.currentRouterProfile.username}`;
          delete this.routerProfiles[routerKey];
          this.currentRouterProfile = null;
          this.saveRouterProfiles();
        }
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      this.showNotification(`❌ Uninstall failed: ${error.message}`, 'error');
      this.addLog('ERROR', `NetPilot uninstallation failed: ${error.message}`);
    } finally {
      this.isProcessing = false;
      this.setButtonLoading(button, false);
    }
  }

  showStatusActions() {
    if (this.elements.statusActions) {
      this.elements.statusActions.style.display = 'flex';
    }
  }

  hideStatusActions() {
    if (this.elements.statusActions) {
      this.elements.statusActions.style.display = 'none';
    }
  }

  // Router Configuration Management
  loadRouterProfiles() {
    try {
      const saved = localStorage.getItem('netpilot-router-profiles');
      if (saved) {
        this.routerProfiles = JSON.parse(saved);
      }
    } catch (error) {
      console.error('Failed to load router profiles:', error);
      this.routerProfiles = {};
    }
  }

  saveRouterProfiles() {
    try {
      localStorage.setItem('netpilot-router-profiles', JSON.stringify(this.routerProfiles));
    } catch (error) {
      console.error('Failed to save router profiles:', error);
    }
  }

  async checkRouterConfiguration() {
    const credentials = this.getFormCredentials();
    if (!credentials) return;

    const routerKey = `${credentials.host}:${credentials.username}`;
    const profile = this.routerProfiles[routerKey];
    
    if (profile && profile.isConfigured) {
      this.currentRouterProfile = profile;
      this.updateConfigurationStatus('configured', `Router configured on ${new Date(profile.lastConfigured).toLocaleDateString()}`);
      this.updateConnectionStatus('configured-disconnected', 'Router ready for tunnel connection');
      
      // Check if there's an existing tunnel connection
      await this.checkExistingConnection();
    } else {
      this.updateConfigurationStatus('unconfigured', 'Router needs initial configuration');
      this.updateConnectionStatus('unconfigured', 'Router not configured for NetPilot');
    }
  }

  updateConfigurationStatus(status, details) {
    const configStatus = this.elements.configStatus;
    const configDetails = this.elements.configDetails;
    const configDot = configStatus?.querySelector('.config-dot');
    
    if (configStatus) {
      configStatus.style.display = 'block';
      configStatus.className = `config-status ${status}`;
    }
    
    if (configDot) {
      configDot.className = `config-dot ${status}`;
    }
    
    if (configDetails) {
      configDetails.innerHTML = `<p>${details}</p>`;
    }
  }

  async handleConfigureRouter(event) {
    event.preventDefault();
    
    if (this.isProcessing) return;
    
    // Validate form inputs
    const credentials = this.getFormCredentials();
    if (!this.validateCredentials(credentials)) return;
    
    // Confirm configuration
    const confirmed = await window.electronAPI.showConfirm({
      title: 'Configure Router',
      message: 'This will install required packages and configure your router for NetPilot. Continue?',
      buttons: ['Configure', 'Cancel']
    });
    
    if (!confirmed) return;
    
    this.isProcessing = true;
    
    try {
      // Lock UI during configuration
      const button = this.elements.configureRouterBtn;
      this.setButtonLoading(button, true);
      this.elements.enableWifiBtn.disabled = true;
      this.elements.testConnectionBtn.disabled = true;
      
      // Display configuration progress
      this.showConfigurationProgress();
      
      // Step 1: Test Connection
      await this.executeConfigStep(1, 'Testing connection to router...', async () => {
        const result = await window.electronAPI.testRouterConnection(credentials);
        if (!result.success) {
          throw new Error(`Connection failed: ${result.error}`);
        }
        return result.data;
      });

      // Step 2: Check Compatibility
      await this.executeConfigStep(2, 'Checking router compatibility...', async () => {
        const result = await window.electronAPI.verifyNetPilotCompatibility(credentials);
        if (!result.success) {
          throw new Error(`Compatibility check failed: ${result.error}`);
        }
        return result.data;
      });

      // Step 3: Install Required Packages
      await this.executeConfigStep(3, 'Installing required packages...', async () => {
        const result = await window.electronAPI.installRouterPackages(credentials);
        if (!result.success) {
          throw new Error(`Package installation failed: ${result.error}`);
        }
        return result.data;
      });

      // Step 4: Configure Router
      await this.executeConfigStep(4, 'Configuring router for NetPilot...', async () => {
        await window.electronAPI.installRouterPackages(credentials);
        return { configured: true };
      });

      // Step 5: Verify Configuration
      await this.executeConfigStep(5, 'Verifying router configuration...', async () => {
        // Verify all packages and configuration are correct
        const verifyResult = await window.electronAPI.verifyRouterSetup(credentials);
        if (!verifyResult.success) {
          throw new Error(`Verification failed: ${verifyResult.error}`);
        }
        return verifyResult.data;
      });

      // Success - save router profile and update status
      const routerKey = `${credentials.host}:${credentials.username}`;
      this.routerProfiles[routerKey] = {
        id: crypto.randomUUID ? crypto.randomUUID() : generateUUID(),
        host: credentials.host,
        username: credentials.username,
        lastConfigured: Date.now(),
        configVersion: '1.0.0',
        isConfigured: true,
        packagesInstalled: true,
        netpilotConfigured: true
      };
      
      this.currentRouterProfile = this.routerProfiles[routerKey];
      this.saveRouterProfiles();
      
      // Set router as configured and save this state
      this.routerConfigured = true;
      this.saveRouterConfigurationState();
      
      this.updateConfigurationStatus('configured', 'Router successfully configured for NetPilot');
      this.updateConnectionStatus('configured-disconnected', 'Router ready for tunnel connection');
      this.updateProgress(100, 'Configuration completed successfully!');
      
      this.showNotification('Router configured successfully!', 'success');
      this.addLog('INFO', 'Router configuration completed successfully');
      
      await window.electronAPI.showInfo({
        title: 'Configuration Complete',
        message: `Your router has been successfully configured for NetPilot!\n\nYou can now use the "Connect Tunnel" button to establish a secure connection to NetPilot Cloud.`
      });

    } catch (error) {
      // Reset configuration state on error
      this.routerConfigured = false;
      this.saveRouterConfigurationState();
      
      this.updateConfigurationStatus('error', error.message);
      this.updateConnectionStatus('error', `Configuration failed: ${error.message}`);
      this.showNotification(`❌ Configuration failed: ${error.message}`, 'error');
      this.addLog('ERROR', `Configuration failed: ${error.message}`);
      console.error('Router configuration error:', error);
      
      this.updateProgress(0, 'Configuration failed');
      
      // Show error dialog
      await window.electronAPI.showError({
        title: 'Configuration Error',
        message: `Failed to configure router: ${error.message}\n\nPlease check your connection settings and try again.`
      });
    } finally {
      const button = this.elements.configureRouterBtn;
      this.setButtonLoading(button, false);
      this.elements.enableWifiBtn.disabled = false;
      this.elements.testConnectionBtn.disabled = false;
      this.isProcessing = false;
      
      // Update button visibility based on configuration state
      this.updateRouterConfigButtonsVisibility();
    }
  }

  async handleConnectTunnel(event) {
    event.preventDefault();
    
    if (this.isProcessing) return;
    
    const credentials = this.getFormCredentials();
    if (!credentials) return;

    // Verify router is configured
    if (!this.currentRouterProfile || !this.currentRouterProfile.isConfigured) {
      this.showNotification('Router must be configured first', 'error');
      return;
    }

    this.isProcessing = true;
    this.updateConnectionStatus('connecting', 'Establishing tunnel connection');
    this.showTunnelProgress();
    
    try {
      // Step 1: Allocate Port
      await this.executeTunnelStep(1, 'Allocating port from cloud VM...', async () => {
        const result = await window.electronAPI.allocatePort(credentials);
        if (!result.success) {
          throw new Error(result.error);
        }
        this.allocatedPort = result.data.port;
        this.showNotification(`Port ${this.allocatedPort} allocated successfully`, 'success');
        return result.data;
      });

      // Step 2: Create Tunnel Script
      await this.executeTunnelStep(2, 'Creating tunnel script on router...', async () => {
        // The script creation is handled by the establish tunnel function
        await new Promise(resolve => setTimeout(resolve, 1000));
        return { scriptCreated: true };
      });

      // Step 3: Establish Tunnel
      await this.executeTunnelStep(3, 'Establishing secure tunnel...', async () => {
        const tunnelResult = await window.electronAPI.establishTunnel({
          credentials,
          port: this.allocatedPort
        });
        
        if (!tunnelResult.success) {
          throw new Error(tunnelResult.error);
        }
        return tunnelResult.data;
      });

      // Step 4: Verify Connection (with delay to avoid race condition)
      await this.executeTunnelStep(4, 'Verifying tunnel connection...', async () => {
        // Wait 5 seconds for tunnel to fully establish before verification
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        // Retry verification up to 3 times with exponential backoff
        let lastError = null;
        for (let attempt = 1; attempt <= 3; attempt++) {
          try {
            const verifyResult = await window.electronAPI.verifyTunnelConnectivity();
            if (verifyResult.success) {
              return verifyResult.data;
            }
            lastError = new Error(verifyResult.error);
          } catch (error) {
            lastError = error;
          }
          
          if (attempt < 3) {
            // Wait progressively longer between retries (2s, 4s)
            await new Promise(resolve => setTimeout(resolve, 2000 * attempt));
          }
        }
        
        throw lastError || new Error('Verification failed after 3 attempts');
      });

      // Success - update profile and status
      const routerKey = `${credentials.host}:${credentials.username}`;
      this.routerProfiles[routerKey].lastConnected = Date.now();
      this.routerProfiles[routerKey].lastAllocatedPort = this.allocatedPort;
      this.saveRouterProfiles();
      
      this.updateConnectionStatus('connected', `Tunnel active and accessible on port ${this.allocatedPort}`);
      this.updateProgress(100, 'Tunnel established successfully!');
      this.showNotification('Tunnel connected successfully!', 'success');
      this.addLog('INFO', `Tunnel established on port ${this.allocatedPort}`);
      
      // Load router credentials for management
      await this.loadRouterCredentials();

    } catch (error) {
      console.error('Connection error:', error);
      this.updateTunnelStepStatus(this.currentTunnelStep, 'error');
      this.updateProgress(0, `Error: ${error.message}`);
      this.updateConnectionStatus('error', `Connection failed: ${error.message}`);
      this.showNotification(`Connection failed: ${error.message}`, 'error');
      this.addLog('ERROR', `Connection failed: ${error.message}`);
    } finally {
      this.isProcessing = false;
    }
  }

  // Settings Management
  loadSettings() {
    const saved = localStorage.getItem('netpilot-settings');
    if (saved) {
      this.settings = { ...this.settings, ...JSON.parse(saved) };
    }
  }

  saveSettings() {
    const settings = {
      autoSavePassword: document.getElementById('settings-auto-save-password')?.checked,
      autoReconnect: document.getElementById('settings-auto-reconnect')?.checked,
      debugMode: document.getElementById('settings-debug-mode')?.checked,
      cloudIp: document.getElementById('settings-cloud-ip')?.value,
      cloudPort: parseInt(document.getElementById('settings-cloud-port')?.value),
      cloudUser: document.getElementById('settings-cloud-user')?.value,
      timeout: parseInt(document.getElementById('settings-timeout')?.value),
      heartbeatInterval: parseInt(document.getElementById('settings-heartbeat-interval')?.value),
      retryAttempts: parseInt(document.getElementById('settings-retry-attempts')?.value)
    };
    
    this.settings = { ...this.settings, ...settings };
    localStorage.setItem('netpilot-settings', JSON.stringify(this.settings));
    
    this.showNotification('⚙️ Settings saved successfully', 'success');
    this.closeModal(this.elements.settingsModal);
    this.addLog('INFO', 'Settings updated');
  }

  resetSettings() {
    this.settings = {
      autoSavePassword: true,
      autoReconnect: true,
      debugMode: false,
      cloudIp: '34.38.207.87',
      cloudPort: 22,
      cloudUser: 'netpilot-agent',
      timeout: 30,
      heartbeatInterval: 60,
      retryAttempts: 3
    };
    
    localStorage.removeItem('netpilot-settings');
    this.populateSettingsForm();
    this.showNotification('⚙️ Settings reset to defaults', 'info');
    this.addLog('INFO', 'Settings reset to defaults');
  }

  populateSettingsForm() {
    document.getElementById('settings-auto-save-password').checked = this.settings.autoSavePassword;
    document.getElementById('settings-auto-reconnect').checked = this.settings.autoReconnect;
    document.getElementById('settings-debug-mode').checked = this.settings.debugMode;
    document.getElementById('settings-cloud-ip').value = this.settings.cloudIp;
    document.getElementById('settings-cloud-port').value = this.settings.cloudPort;
    document.getElementById('settings-cloud-user').value = this.settings.cloudUser;
    document.getElementById('settings-timeout').value = this.settings.timeout;
    document.getElementById('settings-heartbeat-interval').value = this.settings.heartbeatInterval;
    document.getElementById('settings-retry-attempts').value = this.settings.retryAttempts;
  }

  // Modal Management
  openSettings() {
    this.populateSettingsForm();
    this.showModal(this.elements.settingsModal);
  }

  openLogViewer() {
    this.refreshLogs();
    this.showModal(this.elements.logsModal);
  }

  openHelp() {
    this.showModal(this.elements.helpModal);
  }

  showModal(modal) {
    if (modal) {
      modal.style.display = 'flex';
      document.body.style.overflow = 'hidden';
    }
  }

  closeModal(modal) {
    if (modal) {
      modal.style.display = 'none';
      document.body.style.overflow = 'auto';
    }
  }

  switchTab(tabName) {
    // Remove active class from all tabs and content
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // Add active class to selected tab and content
    document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('active');
    document.getElementById(`${tabName}-tab`)?.classList.add('active');
  }

  // Logging System
  addLog(level, message) {
    const timestamp = new Date().toLocaleString();
    const logEntry = {
      timestamp,
      level,
      message,
      id: Date.now() + Math.random()
    };
    
    this.logs.unshift(logEntry);
    
    // Keep only last 1000 logs
    if (this.logs.length > 1000) {
      this.logs = this.logs.slice(0, 1000);
    }
    
    if (this.settings.debugMode) {
      console.log(`[${timestamp}] ${level}: ${message}`);
    }
  }

  refreshLogs() {
    this.renderLogs();
  }

  renderLogs(filterLevel = 'all') {
    const logsContent = document.getElementById('logs-content');
    if (!logsContent) return;
    
    const filteredLogs = filterLevel === 'all' 
      ? this.logs 
      : this.logs.filter(log => log.level.toLowerCase() === filterLevel.toLowerCase());
    
    if (filteredLogs.length === 0) {
      logsContent.innerHTML = '<div class="log-entry info"><span class="log-message">No logs available</span></div>';
      return;
    }
    
    const logsHtml = filteredLogs.map(log => `
      <div class="log-entry ${log.level.toLowerCase()}">
        <span class="log-timestamp">[${log.timestamp}]</span>
        <span class="log-level">${log.level}</span>
        <span class="log-message">${log.message}</span>
      </div>
    `).join('');
    
    logsContent.innerHTML = logsHtml;
    logsContent.scrollTop = 0;
  }

  filterLogs(level) {
    // Update filter button states
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-level="${level}"]`)?.classList.add('active');
    
    this.renderLogs(level);
  }

  clearLogs() {
    this.logs = [];
    this.renderLogs();
    this.showNotification('📋 Logs cleared', 'info');
  }

  async exportLogs() {
    const logsText = this.logs.map(log => 
      `[${log.timestamp}] ${log.level}: ${log.message}`
    ).join('\n');
    
    try {
      await window.electronAPI.saveFile({
        title: 'Export NetPilot Logs',
        defaultPath: `netpilot-logs-${new Date().toISOString().split('T')[0]}.txt`,
        content: logsText
      });
      this.showNotification('📋 Logs exported successfully', 'success');
    } catch (error) {
      this.showNotification('❌ Failed to export logs', 'error');
    }
  }

  async resetAllData() {
    try {
      const button = this.elements.resetAllDataBtn;
      this.setButtonLoading(button, true); 
      
      const result = await window.electronAPI.resetAllData();
      
      if (result.success) {
        // Clear ALL cached user data from localStorage
        localStorage.removeItem('netpilot-router-config-state');
        localStorage.removeItem('netpilot-router-profiles'); 
        localStorage.removeItem('netpilot-settings');
        localStorage.removeItem('netpilot-cached-credentials');
        localStorage.removeItem('netpilot-last-connection');
        
        // Clear any other NetPilot related localStorage items
        Object.keys(localStorage).forEach(key => {
          if (key.startsWith('netpilot-')) {
            localStorage.removeItem(key);
          }
        });
        
        // Reset router configuration state in memory
        this.routerConfigured = false;
        this.currentRouterProfile = null;
        this.routerCredentials = null;
        
        // Reset settings to defaults in memory
        this.settings = {
          autoSavePassword: true,
          autoReconnect: true,
          debugMode: false,
          cloudIp: '34.38.207.87',
          cloudPort: 22,
          cloudUser: 'netpilot-agent',
          timeout: 30,
          heartbeatInterval: 60,
          retryAttempts: 3
        };
        
        // Update UI elements
        this.updateRouterConfigButtonsVisibility();
        
        // Reset is successful, app will restart automatically
        this.showNotification('✅ Cached data reset successfully - restarting...', 'success');
      } else if (!result.canceled) {
        // If there was an error (not user cancellation)
        this.showNotification('❌ Reset Failed: ' + (result.error || 'Failed to reset cached data'), 'error');
      }
    } catch (error) {
      this.showNotification('❌ Reset Failed: ' + (error.message || 'An unexpected error occurred'), 'error');
    } finally {
      const button = this.elements.resetAllDataBtn;
      this.setButtonLoading(button, false);
    }
  }

  async loadRouterConfigurationState() {
    try {
      const savedState = localStorage.getItem('netpilot-router-config-state');
      if (savedState) {
        const state = JSON.parse(savedState);
        this.routerConfigured = state.configured;
        
        // Update button visibility based on loaded state
        this.updateRouterConfigButtonsVisibility();
      }
    } catch (error) {
      console.error('Failed to load router configuration state:', error);
    }
  }

  // Save router configuration state to localStorage
  saveRouterConfigurationState() {
    try {
      const state = {
        configured: this.routerConfigured,
        profile: this.currentRouterProfile,
        timestamp: Date.now()
      };
      localStorage.setItem('netpilot-router-config-state', JSON.stringify(state));
      // Also save to IPC for potential main process access
      window.electronAPI.saveRouterConfigurationState(state);
      
      // Update button visibility based on configuration state
      this.updateRouterConfigButtonsVisibility();
    } catch (error) {
      console.error('Failed to save router configuration state:', error);
    }
  }
  
  // Update visibility of router configuration buttons based on state
  updateRouterConfigButtonsVisibility() {
    const configureBtn = this.elements.configureRouterBtn;
    const verifyBtn = this.elements.verifyConfigBtn;
    const uninstallBtn = this.elements.uninstallBtn;
    const statusSection = document.getElementById('connection-status-section');
    
    if (this.routerConfigured) {
      // Router is configured, show verify and uninstall buttons
      if (configureBtn) configureBtn.style.display = 'none';
      if (verifyBtn) verifyBtn.style.display = 'inline-block';
      if (uninstallBtn) uninstallBtn.style.display = 'inline-block';
      // Hide connection status section as requested
      if (statusSection) statusSection.style.display = 'none';
    } else {
      // Router is not configured, show configure button
      if (configureBtn) configureBtn.style.display = 'inline-block';
      if (verifyBtn) verifyBtn.style.display = 'none';
      if (uninstallBtn) uninstallBtn.style.display = 'none';
      // Show connection status section
      if (statusSection) statusSection.style.display = 'block';
    }
  }
  
  // Handle verify configuration button click
  async handleVerifyConfig(event) {
    event.preventDefault();
    
    if (this.isProcessing) return;
    
    const credentials = this.getFormCredentials();
    if (!this.validateCredentials(credentials)) return;
    
    this.isProcessing = true;
    const button = this.elements.verifyConfigBtn;
    this.setButtonLoading(button, true);
    
    try {
      this.showNotification('Verifying router configuration...', 'info');
      
      // Call the router verification API
      const result = await window.electronAPI.verifyRouterSetup(credentials);
      
      if (result.success) {
        const verification = result.data;
        
        if (verification.isConfigured) {
          this.showNotification('✅ Router configuration verified successfully', 'success');
          this.addLog('INFO', 'Router configuration verified successfully');
          
          // Update router profile with verification results
          if (this.currentRouterProfile) {
            this.currentRouterProfile.lastVerified = Date.now();
            this.currentRouterProfile.verificationResults = verification;
            this.saveRouterProfiles();
          }
        } else {
          this.showNotification('⚠️ Router configuration issues detected', 'warning');
          this.addLog('WARNING', 'Router configuration issues detected');
          
          // Show detailed issues
          if (verification.issues && verification.issues.length > 0) {
            const issuesText = verification.issues.join('\n- ');
            await window.electronAPI.showInfo({
              title: 'Configuration Issues',
              message: `The following issues were detected with your router configuration:\n\n- ${issuesText}\n\nWould you like to reconfigure the router?`
            });
          }
        }
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      this.showNotification(`❌ Verification failed: ${error.message}`, 'error');
      this.addLog('ERROR', `Router verification failed: ${error.message}`);
    } finally {
      this.isProcessing = false;
      this.setButtonLoading(button, false);
    }
  }

  // Validate router credentials
  validateCredentials(credentials) {
    if (!credentials) {
      this.showNotification('Please fill all required fields', 'error');
      return false;
    }
    
    // Validate IP format
    const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    if (!ipRegex.test(credentials.host)) {
      this.showNotification('Please enter a valid IP address', 'error');
      return false;
    }
    
    // Validate username
    if (!credentials.username || credentials.username.trim() === '') {
      this.showNotification('Username is required', 'error');
      return false;
    }
    
    return true;
  }
}

// Initialize the application
const app = new NetPilotAgentUI(); 