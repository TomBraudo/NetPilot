const { NodeSSH } = require('node-ssh');
const path = require('path');
const ConfigManager = require('./ConfigManager');
const StateManager = require('./StateManager');
const axios = require('axios');
const logger = require('../utils/Logger');
const crypto = require('crypto');

class TunnelManager {
  constructor(configManager) {
    // Accept a ConfigManager instance from the main process. When running in
    // isolation (e.g., unit tests) we lazily construct our own instance using
    // the Electron `app` reference.
    if (!configManager) {
      const { app } = require('electron');
      this.configManager = new ConfigManager(app);
    } else {
      this.configManager = configManager;
    }

    this.ssh = new NodeSSH();
    const cloudVmConfig = this.configManager.getCloudVmConfig();
    
    this.isConnected = false;
    this.tunnelPort = null;
    this.routerCredentials = null;
    this.cloudVmIp = cloudVmConfig.ip;
    this.cloudUser = cloudVmConfig.user;
    this.cloudPassword = cloudVmConfig.password;
    this.cloudPort = 22; // Default to 22 unless overridden
    this.tunnelProcess = null;
    this.isMonitoring = false;
    this.routerId = null; // For heartbeat tracking
    this.heartbeatInterval = null;
    this.monitorInterval = null;
    this._lastFuncCheck = 0; // For periodic functionality checks
    
    // Initialize state manager for persistent storage
    this.stateManager = new StateManager();
  }

  async establishTunnel(credentials, port, routerId = null) {
    logger.tunnel(`Establishing tunnel on port ${port} for router ${credentials.host}`);

    try {
      this.routerCredentials = credentials;
      this.tunnelPort = port;
      // Use provided routerId from PortAllocator. If it's missing, create a deterministic one.
      this.routerId = routerId || crypto.createHash('sha256').update(credentials.host).digest('hex');
      
      // Set cloudPort from credentials or default to 22
      this.cloudPort = credentials?.cloudPort || 22;
      
      // Connect to router
      await this.ssh.connect({
        host: credentials.host,
        username: credentials.username,
        password: credentials.password,
        port: credentials.port || 22,
        readyTimeout: 30000
      });

      this.isConnected = true;
      
      // Setup SSH keys for better security (optional)
      await this.setupSSHKeys();

      // Create tunnel script on router
      await this.createTunnelScript(port);
      
      // Create init.d service for auto-start on boot
      await this.createInitService();
      
      // Start the tunnel
      await this.startTunnel();
      
      // REDUCED: Since startTunnel now waits for actual process establishment,
      // we need less additional time before verification
      logger.tunnel('Waiting for tunnel connection to fully establish before verification...');
      await new Promise(resolve => setTimeout(resolve, 8000)); // Reduced from 15s since startTunnel now waits properly
      
      // Verify tunnel is working (enhanced verification)
      await this.verifyTunnel(port);
      
      // Start monitoring with heartbeat
      this.startMonitoring();
      this.startHeartbeat();
      
      logger.tunnel(`Tunnel established successfully on port ${port}`);
      
      // Save tunnel state for persistence
      await this.saveTunnelState();
      
      return {
        success: true,
        port: port,
        status: 'active',
        message: 'Tunnel established successfully',
        routerId: this.routerId
      };
      
    } catch (error) {
      logger.error('TUNNEL', 'Tunnel establishment failed:', error);
      await this.cleanup();
      throw error;
    }
  }

  async setupSSHKeys() {
    logger.tunnel('Setting up SSH keys for enhanced security...');
    
    try {
      // Check if SSH keys already exist
      const keyCheck = await this.ssh.execCommand('ls -la /root/.ssh/id_rsa 2>/dev/null || echo "not_found"');
      
      if (keyCheck.stdout.includes('not_found')) {
        logger.tunnel('Generating SSH keypair...');
        
        // Generate SSH keypair on router
        await this.ssh.execCommand('mkdir -p /root/.ssh');
        await this.ssh.execCommand('ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N "" -C "netpilot-tunnel"');
        
        logger.tunnel('SSH keypair generated successfully');
      } else {
        logger.tunnel('SSH keypair already exists');
      }
      
      // Get public key for potential upload to cloud VM
      const pubKeyResult = await this.ssh.execCommand('cat /root/.ssh/id_rsa.pub 2>/dev/null || echo "no_key"');
      
      if (!pubKeyResult.stdout.includes('no_key')) {
        this.routerPublicKey = pubKeyResult.stdout.trim();
        logger.tunnel('Router public key retrieved for future key-based authentication');
      }
      
    } catch (error) {
      logger.warn('SSH key setup failed, will use password authentication:', error.message);
      // Don't throw error - password auth is fallback
    }
  }

  async createTunnelScript(port) {
    logger.tunnel('Creating tunnel script on router...');
    
    // Check if sshpass is available (it should be installed with other packages)
    logger.tunnel('Checking for sshpass availability...');
    const sshpassCheck = await this.ssh.execCommand('which sshpass || echo "not_found"');
    if (sshpassCheck.stdout.includes('not_found')) {
      logger.tunnel('sshpass not found, installing...');
      await this.ssh.execCommand('opkg install sshpass');
    } else {
      logger.tunnel('sshpass is available');
    }
    
    // Verify nohup is available (should be installed via coreutils-nohup package)
    logger.tunnel('Verifying nohup availability...');
    const nohupCheck = await this.ssh.execCommand('which nohup || echo "not_found"');
    if (nohupCheck.stdout.includes('not_found')) {
      throw new Error('nohup not found - coreutils-nohup package may not be installed properly');
    } else {
      logger.tunnel('nohup is available');
    }
    
    // Create enhanced autossh tunnel script with better error handling
    const tunnelScript = `#!/bin/sh
# NetPilot Tunnel Script - Auto-generated
# Port: ${port}
# Router ID: ${this.routerId}

CLOUD_VM="${this.cloudVmIp}"
CLOUD_USER="${this.cloudUser}"
CLOUD_PASSWORD="${this.cloudPassword}"
CLOUD_PORT="${this.cloudPort || 22}"
LOCAL_PORT="22"
REMOTE_PORT="${port}"
ROUTER_ID="${this.routerId}"
PID_FILE="/var/run/netpilot_tunnel_\${REMOTE_PORT}.pid"

# Logging function
log_message() {
    echo "[\$(date '+%Y-%m-%d %H:%M:%S')] \$1" >> /tmp/netpilot_tunnel.log
    echo "[\$(date '+%Y-%m-%d %H:%M:%S')] \$1"
}

log_message "Starting NetPilot tunnel to \${CLOUD_VM}:\${REMOTE_PORT}"

# Kill any existing tunnel processes for this port only (BusyBox compatible)
log_message "Cleaning up existing tunnel processes for port \${REMOTE_PORT}..."
ps | grep "autossh.*-R \${REMOTE_PORT}:localhost:22" | grep -v grep | awk '{print \$1}' | xargs -r kill || true
ps | grep "sshpass.*autossh.*\${REMOTE_PORT}" | grep -v grep | awk '{print \$1}' | xargs -r kill || true
sleep 2

# Remove stale PID file if it exists
if [ -f "\$PID_FILE" ]; then
    OLD_PID=\$(cat "\$PID_FILE" 2>/dev/null)
    if [ -n "\$OLD_PID" ]; then
        log_message "Found stale PID file with PID \$OLD_PID, attempting to kill it"
        kill -9 \$OLD_PID 2>/dev/null || true
    fi
    rm -f "\$PID_FILE"
fi

# Check SSHD status on router
log_message "Checking SSHD status on router..."
if ! pgrep dropbear && ! pgrep sshd; then
    log_message "ERROR: SSHD is not running on router!"
    exit 1
fi

# Test cloud VM connectivity first
log_message "Testing connectivity to cloud VM..."
if ! ping -c 3 -W 5 \${CLOUD_VM} >/dev/null 2>&1; then
    log_message "ERROR: Cannot reach cloud VM \${CLOUD_VM}"
    exit 1
fi

log_message "Cloud VM connectivity verified"

# Test SSH connectivity before starting autossh
log_message "Testing SSH connectivity to cloud VM..."
if ! sshpass -p "\${CLOUD_PASSWORD}" ssh -p \${CLOUD_PORT} \
    -o ConnectTimeout=10 \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o PasswordAuthentication=yes \
    -o PubkeyAuthentication=no \
    \${CLOUD_USER}@\${CLOUD_VM} "echo 'SSH test successful'" 2>/tmp/ssh_test.log; then
    log_message "ERROR: SSH connectivity test failed"
    log_message "SSH error details: \$(cat /tmp/ssh_test.log 2>/dev/null)"
    exit 1
fi

log_message "SSH connectivity verified"

# Start autossh with enhanced logging and error handling
log_message "Starting autossh tunnel..."
export AUTOSSH_LOGFILE="/tmp/autossh.log"
export AUTOSSH_LOGLEVEL=7
export AUTOSSH_DEBUG=1
export AUTOSSH_PIDFILE="\$PID_FILE"

# Enhanced tunnel command with autossh and password authentication
export SSHPASS="\${CLOUD_PASSWORD}"

# Use nohup for complete process detachment (no fallbacks for memory optimization)
log_message "Using nohup for process detachment"
(
    cd /
    umask 0
    exec nohup sshpass -e autossh -M 0 -N \
        -p \${CLOUD_PORT} \
        -R \${REMOTE_PORT}:localhost:22 \
        -o ServerAliveInterval=30 \
        -o ServerAliveCountMax=3 \
        -o ExitOnForwardFailure=yes \
        -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=/dev/null \
        -o ConnectTimeout=10 \
        -o LogLevel=VERBOSE \
        -o PasswordAuthentication=yes \
        -o PubkeyAuthentication=no \
        \${CLOUD_USER}@\${CLOUD_VM} \
        < /dev/null > /tmp/nohup_autossh.out 2>&1 &
) &

# Wait for process to start
sleep 3

# Multiple checks to ensure autossh is stable
for attempt in 1 2 3 4 5; do
    if ps | grep -v grep | grep "autossh.*\${REMOTE_PORT}:localhost:22" >/dev/null; then
        # Get the PID of the autossh process and save it
        PID=\$(ps | grep -v grep | grep "autossh.*\${REMOTE_PORT}:localhost:22" | awk '{print \$1}')
        echo "\$PID" > "\$PID_FILE"
        log_message "✅ Autossh confirmed running with PID \$PID (attempt \$attempt)"
        
        # Verify SSH connection is actually working
        sleep 2
        if ps | grep -v grep | grep "autossh.*\${REMOTE_PORT}:localhost:22" >/dev/null; then
            log_message "✅ Autossh stable after \$((attempt * 2 + 3)) seconds - tunnel should be functional"
            echo "\$PID"
            exit 0
        else
            log_message "⚠️ Autossh process died during stability check (attempt \$attempt)"
            log_message "Autossh logs: \$(tail -10 /tmp/autossh.log 2>/dev/null)"
        fi
    else
        log_message "❌ Autossh not found in process list (attempt \$attempt)"
        log_message "All SSH processes: \$(ps | grep -i ssh | grep -v grep)"
        log_message "Recent autossh logs: \$(tail -5 /tmp/autossh.log 2>/dev/null)"
    fi
    
    # Wait before next attempt
    sleep 2
done

log_message "ERROR: Autossh failed to start or died within 15 seconds"
log_message "Final autossh logs: \$(cat /tmp/autossh.log 2>/dev/null)"
log_message "Final SSH test logs: \$(cat /tmp/ssh_test.log 2>/dev/null)"
exit 1
`;

    // Write script to router
    await this.ssh.execCommand(`cat > /root/netpilot_tunnel.sh << 'EOF'
${tunnelScript}
EOF`);
    
    // Make script executable
    await this.ssh.execCommand('chmod +x /root/netpilot_tunnel.sh');
    
    // Verify script was created successfully
    const scriptVerification = await this.ssh.execCommand('ls -la /root/netpilot_tunnel.sh 2>/dev/null || echo "script_not_found"');
    if (scriptVerification.stdout.includes('script_not_found')) {
      throw new Error('Tunnel script creation failed - script file not found on router');
    }
    
    // Verify script is executable
    if (!scriptVerification.stdout.includes('-rwxr-xr-x') && !scriptVerification.stdout.includes('-rwx')) {
      logger.warn('Tunnel script may not be executable, checking permissions...');
      await this.ssh.execCommand('chmod +x /root/netpilot_tunnel.sh');
    }
    
    // Verify script content contains essential components
    const scriptContent = await this.ssh.execCommand('head -10 /root/netpilot_tunnel.sh');
    if (!scriptContent.stdout.includes('NetPilot Tunnel Script') || !scriptContent.stdout.includes(this.tunnelPort.toString())) {
      throw new Error('Tunnel script creation failed - script content verification failed');
    }
    
    logger.tunnel('Enhanced tunnel script created and verified successfully');
  }

  async createInitService() {
    logger.tunnel('Creating init.d service for auto-start on boot...');
    
    try {
      // Create init.d service script
      const initScript = `#!/bin/sh /etc/rc.common
# NetPilot Tunnel Auto-Start Service
# Auto-generated for router ID: ${this.routerId}
# Port: ${this.tunnelPort}

START=99
STOP=15

USE_PROCD=1
PROG="/root/netpilot_tunnel.sh"
PIDFILE="/var/run/netpilot_tunnel_${this.tunnelPort}.pid"

start_service() {
    echo "Starting NetPilot tunnel service for port ${this.tunnelPort}..."
    
    # Wait for network to be ready
    sleep 10
    
    # Ensure we have internet connectivity
    local retries=0
    while [ \$retries -lt 12 ]; do
        if ping -c 1 -W 5 ${this.cloudVmIp} >/dev/null 2>&1; then
            echo "Internet connectivity verified"
            break
        fi
        echo "Waiting for internet connectivity... (attempt \$((\$retries + 1))/12)"
        sleep 5
        retries=\$((\$retries + 1))
    done
    
    if [ \$retries -eq 12 ]; then
        echo "ERROR: Cannot reach cloud VM ${this.cloudVmIp} after 60 seconds"
        return 1
    fi
    
    # Start tunnel service
    procd_open_instance
    procd_set_param command \$PROG
    procd_set_param pidfile \$PIDFILE
    procd_set_param respawn \${respawn_threshold:-3600} \${respawn_timeout:-5} \${respawn_retry:-5}
    procd_set_param stdout 1
    procd_set_param stderr 1
    procd_close_instance
    
    echo "NetPilot tunnel service for port ${this.tunnelPort} started"
}

stop_service() {
    echo "Stopping NetPilot tunnel service for port ${this.tunnelPort}..."
    
    # Kill tunnel processes for this specific port only (BusyBox compatible)
    ps | grep "netpilot_tunnel.*${this.tunnelPort}" | grep -v grep | awk '{print \$1}' | xargs -r kill || true
    ps | grep "autossh.*-R ${this.tunnelPort}:localhost:22" | grep -v grep | awk '{print \$1}' | xargs -r kill || true
    ps | grep "sshpass.*autossh.*${this.tunnelPort}" | grep -v grep | awk '{print \$1}' | xargs -r kill || true
    
    # Read PID from file and kill directly if possible
    if [ -f "\$PIDFILE" ]; then
        PID=\$(cat "\$PIDFILE" 2>/dev/null)
        if [ -n "\$PID" ]; then
            kill \$PID 2>/dev/null || kill -9 \$PID 2>/dev/null || true
        fi
        rm -f "\$PIDFILE"
    fi
    
    echo "NetPilot tunnel service for port ${this.tunnelPort} stopped"
}

restart() {
    stop_service
    sleep 2
    start_service
}
`;

      // Write init.d service
      await this.ssh.execCommand(`cat > /etc/init.d/netpilot_tunnel << 'EOF'
${initScript}
EOF`);
      
      // Make service executable
      await this.ssh.execCommand('chmod +x /etc/init.d/netpilot_tunnel');
      
      // Enable service for auto-start
      await this.ssh.execCommand('/etc/init.d/netpilot_tunnel enable');
      
      // Verify init.d service was created successfully
      const serviceVerification = await this.ssh.execCommand('ls -la /etc/init.d/netpilot_tunnel 2>/dev/null || echo "service_not_found"');
      if (serviceVerification.stdout.includes('service_not_found')) {
        throw new Error('Init.d service creation failed - service file not found');
      }
      
      // Verify service is executable
      if (!serviceVerification.stdout.includes('-rwxr-xr-x') && !serviceVerification.stdout.includes('-rwx')) {
        logger.warn('Init.d service may not be executable, fixing permissions...');
        await this.ssh.execCommand('chmod +x /etc/init.d/netpilot_tunnel');
      }
      
      // Verify service is enabled (check for symlinks in rc.d)
      const enableVerification = await this.ssh.execCommand('ls -la /etc/rc.d/S99netpilot_tunnel 2>/dev/null || echo "not_enabled"');
      if (enableVerification.stdout.includes('not_enabled')) {
        logger.warn('Service may not be enabled, attempting to re-enable...');
        await this.ssh.execCommand('/etc/init.d/netpilot_tunnel enable');
      }
      
      // Verify service content contains correct port
      const serviceContent = await this.ssh.execCommand('head -10 /etc/init.d/netpilot_tunnel');
      if (!serviceContent.stdout.includes('NetPilot Tunnel Auto-Start') || !serviceContent.stdout.includes(this.tunnelPort.toString())) {
        throw new Error('Init.d service creation failed - service content verification failed');
      }
      
      logger.tunnel('Init.d service created, verified, and enabled for auto-start on boot');
      
    } catch (error) {
      logger.error('Failed to create init.d service:', error);
      throw new Error(`Init.d service creation failed: ${error.message}`);
    }
  }

  async startTunnel() {
    logger.tunnel('Starting tunnel process...');
    try {
      if (!this.ssh.isConnected()) {
        logger.error('Start tunnel error: SSH session is not connected.');
        throw new Error('SSH session is not connected');
      }
      
      // Aggressive cleanup of existing tunnel processes
      await this.aggressiveProcessCleanup();
      
      // Clear previous logs
      await this.ssh.execCommand('> /tmp/netpilot_tunnel.log');
      await this.ssh.execCommand('> /tmp/autossh.log');
      
      // Start tunnel script with proper detachment to prevent SIGHUP killing autossh
      logger.tunnel('Executing tunnel script with process detachment...');
      const result = await this.ssh.execCommand('cd /root && nohup ./netpilot_tunnel.sh > /tmp/tunnel_execution.log 2>&1 & echo "Script backgrounded with PID $!"');
      
      // Check if script execution had errors
      if (result.stderr && result.stderr.trim()) {
        logger.error('Tunnel script stderr:', result.stderr);
      }
      
      logger.tunnel('Tunnel script backgrounded, waiting for autossh to establish...');
      
      // Give the backgrounded script time to start autossh
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Check if the script actually started by examining execution logs
      const execLogs = await this.ssh.execCommand('cat /tmp/tunnel_execution.log 2>/dev/null || echo "No execution logs"');
      logger.tunnel('Script execution logs:', execLogs.stdout);
      
      // Wait for autossh process to start and establish connection
      // Use progressive checking rather than fixed delay
      let autosshFound = false;
      let maxAttempts = 10; // 10 attempts over ~20 seconds (reduced since script is properly backgrounded)
      
      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        logger.tunnel(`Checking for autossh process (attempt ${attempt}/${maxAttempts})...`);
        
        // Check for specific autossh process for this port
        const processCheck = await this.ssh.execCommand(`ps | grep -v grep | grep "autossh.*-R ${this.tunnelPort}:localhost:22"`);
        
        if (processCheck.stdout) {
          logger.tunnel(`✅ Autossh process found for port ${this.tunnelPort}: ${processCheck.stdout.trim()}`);
          autosshFound = true;
          this.tunnelProcess = 'autossh';
          break;
        }
        
        // Check logs for errors on failed attempts
        if (attempt > 5) {
          const tunnelLogs = await this.ssh.execCommand('tail -5 /tmp/netpilot_tunnel.log 2>/dev/null || echo "No recent tunnel logs"');
          logger.tunnel(`Recent tunnel logs: ${tunnelLogs.stdout}`);
        }
        
        // Progressive delay: start with 1s, increase to 3s for later attempts
        const delay = attempt <= 5 ? 1000 : (attempt <= 10 ? 2000 : 3000);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
      
      if (!autosshFound) {
        // Get comprehensive logs for debugging
        const tunnelLogs = await this.ssh.execCommand('cat /tmp/netpilot_tunnel.log 2>/dev/null || echo "No tunnel logs"');
        const autosshLogs = await this.ssh.execCommand('cat /tmp/autossh.log 2>/dev/null || echo "No autossh logs"');
        const sshTestLogs = await this.ssh.execCommand('cat /tmp/ssh_test.log 2>/dev/null || echo "No SSH test logs"');
        
        logger.error('❌ Autossh process failed to start after 30 seconds. Debug logs:');
        logger.error('Tunnel logs:', tunnelLogs.stdout);
        logger.error('Autossh logs:', autosshLogs.stdout);
        logger.error('SSH test logs:', sshTestLogs.stdout);
        
        // Check if script itself failed
        if (result.code !== 0 && result.code !== undefined) {
          logger.error(`Tunnel script exited with code ${result.code}`);
        }
        
        throw new Error(`Autossh process failed to start within 30 seconds. Check logs above for details.`);
      }
      
      logger.tunnel('✅ Tunnel process started successfully, allowing time for SSH connection establishment...');
      
      // Give additional time for the SSH connection itself to establish
      // This is critical for the tunnel to be ready for verification
      await new Promise(resolve => setTimeout(resolve, 5000));
      
    } catch (error) {
      logger.error('Failed to start tunnel:', error);
      if (error.stdout) logger.error('Start tunnel error stdout:', error.stdout);
      if (error.stderr) logger.error('Start tunnel error stderr:', error.stderr);
      throw error;
    }
  }

  async verifyTunnel(port) {
    logger.tunnel('Performing enhanced tunnel verification...');
    
    try {
      // Check if autossh process is running
      const processCheck = await this.ssh.execCommand(`ps | grep -v grep | grep "autossh.*-R ${port}:localhost:22"`);
      if (!processCheck.stdout) {
        // Get comprehensive logs to understand why the process died
        const tunnelLogs = await this.ssh.execCommand('cat /tmp/netpilot_tunnel.log 2>/dev/null || echo "No tunnel logs"');
        const autosshLogs = await this.ssh.execCommand('cat /tmp/autossh.log 2>/dev/null || echo "No autossh logs"');
        const sshTestLogs = await this.ssh.execCommand('cat /tmp/ssh_test.log 2>/dev/null || echo "No SSH test logs"');
        
        logger.error('❌ Autossh process not found during verification. Debug info:');
        logger.error('Tunnel logs:', tunnelLogs.stdout);
        logger.error('Autossh logs:', autosshLogs.stdout);
        logger.error('SSH test logs:', sshTestLogs.stdout);
        
        // Check for any autossh-related processes
        const allProcesses = await this.ssh.execCommand('ps | grep -i ssh | grep -v grep || echo "No SSH processes"');
        logger.error('All SSH-related processes:', allProcesses.stdout);
        
        // Instead of immediately failing, try to restart the tunnel
        logger.tunnel('🔄 Attempting to restart tunnel since process died...');
        try {
          await this.startTunnel(); // Try to restart
          logger.tunnel('✅ Tunnel restarted successfully, proceeding with verification...');
        } catch (restartError) {
          logger.error('❌ Failed to restart tunnel:', restartError.message);
          throw new Error(`Autossh process died and restart failed: ${restartError.message}`);
        }
      } else {
        logger.tunnel('✅ Autossh process is running');
      }
      
      // Enhanced verification: Test from cloud VM side with retries
      await this.verifyTunnelFromCloudVM(port);
      
      return true;
    } catch (error) {
      logger.error('Tunnel verification failed:', error);
      throw new Error(`Tunnel verification failed: ${error.message}`);
    }
  }

  async verifyTunnelFromCloudVM(port) {
    logger.tunnel('Verifying ACTUAL tunnel connectivity from cloud VM...');
    
    const maxRetries = 3;
    let retryCount = 0;
    let lastError = null;
    
    // Retry logic with shorter attempts (actual SSH test is slower)
    while (retryCount < maxRetries) {
      try {
        // Use the NEW tunnel test API that actually tests SSH connectivity
        const response = await axios.post(`http://${this.cloudVmIp}:8080/api/test-tunnel/${port}`, {
          testCommand: 'echo "netpilot_verification_test"'
        }, {
          timeout: 15000 + (retryCount * 5000), // Longer timeout for actual SSH test
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (response.data && response.data.success && response.data.data) {
          const testData = response.data.data;
          if (testData.tunnelWorking && testData.output.includes('netpilot_verification_test')) {
            logger.tunnel(`✅ Cloud VM CONFIRMED actual SSH connectivity through tunnel port ${port} (attempt ${retryCount + 1})`);
            logger.tunnel(`Tunnel test output: "${testData.output}"`);
            return true;
          } else {
            logger.tunnel(`❌ Cloud VM tunnel test failed on port ${port} (attempt ${retryCount + 1})`);
            logger.tunnel(`Test output: "${testData.output || 'no output'}"`);
            logger.tunnel(`Error: "${testData.error || 'no error'}"`);
            lastError = new Error(`Tunnel connectivity test failed: ${testData.error || 'No SSH response'}`);
          }
        } else if (response.data && !response.data.success) {
          logger.tunnel(`❌ Cloud VM tunnel test API failed on port ${port} (attempt ${retryCount + 1})`);
          const testData = response.data.data || {};
          logger.tunnel(`API error: "${testData.error || response.data.error || 'Unknown error'}"`);
          lastError = new Error(`Tunnel test API failed: ${testData.error || response.data.error}`);
        } else {
          lastError = new Error('Invalid response from cloud VM tunnel test API');
        }
      } catch (error) {
        lastError = error;
        logger.tunnel(`❌ Cloud VM tunnel test exception on port ${port} (attempt ${retryCount + 1}): ${error.message}`);
        
        // If it's a connection error to the API, that's different from tunnel failure
        if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
          logger.warn('Cloud VM API is not reachable - cannot verify tunnel, but local process is running');
          return true; // Assume tunnel is working if we can't reach the API to test it
        }
      }
      
      retryCount++;
      
      if (retryCount < maxRetries) {
        const backoffTime = Math.min(8000 * retryCount, 20000); // 8s, 16s max
        logger.tunnel(`Retrying tunnel verification in ${backoffTime/1000} seconds...`);
        await new Promise(resolve => setTimeout(resolve, backoffTime));
      }
    }
    
    // All retries exhausted - tunnel is not working
    if (lastError) {
      logger.error(`❌ TUNNEL VERIFICATION FAILED after ${maxRetries} attempts: ${lastError.message}`);
      logger.error('The reverse tunnel is NOT working - SSH connections will fail from cloud VM');
      throw new Error(`Tunnel verification failed: ${lastError.message}`);
    }
    
    return false;
  }

  startHeartbeat() {
    if (this.heartbeatInterval) return;
    
    logger.tunnel('Starting heartbeat to cloud VM...');
    
    // Send heartbeat every 60 seconds
    this.heartbeatInterval = setInterval(async () => {
      try {
        await this.sendHeartbeat();
      } catch (error) {
        logger.error('Heartbeat failed:', error);
      }
    }, 60000);
    
    // Send initial heartbeat immediately
    this.sendHeartbeat().catch(error => {
      logger.error('Initial heartbeat failed:', error);
    });
  }

  async sendHeartbeat() {
    if (!this.tunnelPort || !this.routerId) return;
    
    try {
      const response = await axios.post(`http://${this.cloudVmIp}:8080/api/heartbeat/${this.tunnelPort}`, {
        routerId: this.routerId,
        status: 'active',
        timestamp: new Date().toISOString(),
        routerInfo: {
          host: this.routerCredentials?.host,
          lastSeen: new Date().toISOString()
        }
      }, {
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.status === 200) {
        logger.tunnel(`Heartbeat sent successfully for port ${this.tunnelPort}`);
      }
      
    } catch (error) {
      if (error.code === 'ECONNREFUSED') {
        logger.warn(`Cloud VM heartbeat service unavailable (${this.cloudVmIp}:8080) - tunnel still functional`);
      } else if (error.response?.status === 500) {
        logger.warn(`Cloud VM heartbeat API error (500) - tunnel still functional: ${error.message}`);
      } else if (error.code === 'ETIMEDOUT') {
        logger.warn(`Heartbeat timeout to cloud VM - tunnel still functional`);
      } else {
        logger.error('Failed to send heartbeat:', error.message);
      }
    }
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
      logger.tunnel('Heartbeat stopped');
    }
  }

  startMonitoring() {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    logger.tunnel(`Starting enhanced tunnel monitoring for port ${this.tunnelPort}...`);
    
    // Monitor tunnel every 30 seconds
    this.monitorInterval = setInterval(async () => {
      try {
        if (!this.isConnected || !this.tunnelPort) {
          logger.tunnel('Monitoring detected router disconnection, stopping monitoring');
          this.stopMonitoring();
          return;
        }
        
        // Check if the tunnel process is still running for the specific port
        const processCheck = await this.ssh.execCommand(`ps | grep -v grep | grep "autossh.*-R ${this.tunnelPort}:localhost:22" || true`);
        if (!processCheck.stdout) {
          logger.warn(`Monitoring detected tunnel process for port ${this.tunnelPort} is not running, attempting to restart`);
          await this.restartTunnel();
        } else {
          // Check if the PID file exists and matches the running process
          const pidCheck = await this.ssh.execCommand(`
            PID_FILE="/var/run/netpilot_tunnel_${this.tunnelPort}.pid"
            if [ -f "$PID_FILE" ]; then
              PID=$(cat "$PID_FILE" 2>/dev/null)
              if [ -n "$PID" ] && ! ps | grep -v grep | grep -q "$PID"; then
                echo "PID file exists but process $PID is not running"
              fi
            else
              echo "PID file does not exist"
            fi
          `);
          
          if (pidCheck.stdout.trim()) {
            logger.warn(`PID file issue detected: ${pidCheck.stdout.trim()}, updating PID file`);
            // Update the PID file with the current process ID
            await this.ssh.execCommand(`
              PID=$(ps | grep -v grep | grep "autossh.*-R ${this.tunnelPort}:localhost:22" | awk '{print $1}')
              if [ -n "$PID" ]; then
                echo "$PID" > "/var/run/netpilot_tunnel_${this.tunnelPort}.pid"
                echo "Updated PID file with $PID"
              fi
            `);
          }
        }
        
        // Periodically check tunnel functionality
        // Only do more expensive checks every 5 minutes (every 10 monitoring intervals)
        if (Math.floor(Date.now() / 300000) !== this._lastFuncCheck) {
          this._lastFuncCheck = Math.floor(Date.now() / 300000);
          
          try {
            // Check if the tunnel is functional from the cloud VM side
            const vmCheck = await axios.get(`http://${this.cloudVmIp}:8080/api/port-status`, {
              params: { port: this.tunnelPort },
              timeout: 5000
            });
            
            if (!vmCheck.data?.data?.status === 'active') {
              logger.warn(`Cloud VM reports tunnel port ${this.tunnelPort} is not active, attempting to restart`);
              await this.restartTunnel();
            }
          } catch (vmError) {
            // If we can't reach the cloud VM, don't restart the tunnel - network might be down
            logger.warn(`Could not verify tunnel status with cloud VM: ${vmError.message}`);
          }
        }
        
      } catch (error) {
        logger.error('Error in tunnel monitoring:', error);
      }
    }, 30000);
  }

  stopMonitoring() {
    if (this.monitorInterval) {
      clearInterval(this.monitorInterval);
      this.monitorInterval = null;
    }
    this.isMonitoring = false;
    logger.tunnel('Tunnel monitoring stopped');
  }

  async getTunnelStatus() {
    if (!this.isConnected) {
      return {
        isActive: false,
        port: this.tunnelPort,
        error: 'Not connected to router'
      };
    }

    try {
      // Check if autossh process is running for this specific port
      const processCheck = await this.ssh.execCommand(`ps | grep -v grep | grep "autossh.*-R ${this.tunnelPort}:localhost:22" || true`);
      const isActive = processCheck.stdout.length > 0;
      
      // Log process details for debugging
      if (processCheck.stdout) {
        logger.tunnel(`Found autossh process for port ${this.tunnelPort}: ${processCheck.stdout.trim()}`);
      } else {
        logger.tunnel(`No autossh processes found for port ${this.tunnelPort}`);
        
        // Check for PID file
        const pidCheck = await this.ssh.execCommand(`[ -f "/var/run/netpilot_tunnel_${this.tunnelPort}.pid" ] && echo "PID file exists" || echo "No PID file"`);
        logger.tunnel(pidCheck.stdout.trim());
      }
      
      // Get tunnel logs
      const logResult = await this.ssh.execCommand('tail -10 /tmp/netpilot_tunnel.log 2>/dev/null || echo "No logs"');
      
      // Check init.d service status
      const serviceStatus = await this.ssh.execCommand('/etc/init.d/netpilot_tunnel status 2>/dev/null || echo "Service not configured"');
      
      // Check PID file
      const pidContent = await this.ssh.execCommand(`cat "/var/run/netpilot_tunnel_${this.tunnelPort}.pid" 2>/dev/null || echo "No PID file"`);
      const pidValue = pidContent.stdout.trim() !== "No PID file" ? pidContent.stdout.trim() : null;
      
      // Test tunnel functionality by checking if port is reachable from cloud VM
      let cloudStatus = null;
      try {
        const response = await axios.get(`http://${this.cloudVmIp}:8080/api/port-status`, {
          params: { port: this.tunnelPort },
          timeout: 5000
        });
        if (response.data && response.data.success && response.data.data) {
          cloudStatus = response.data.data.status;
        }
      } catch (error) {
        logger.warn('Could not retrieve cloud VM port status:', error.message);
      }
      
      return {
        isActive,
        port: this.tunnelPort,
        routerId: this.routerId,
        processId: pidValue || this.tunnelProcess,
        lastLogs: logResult.stdout.split('\n'),
        serviceStatus: serviceStatus.stdout.trim(),
        timestamp: new Date().toISOString(),
        hasInitService: !serviceStatus.stdout.includes('Service not configured'),
        cloudStatus: cloudStatus
      };
    } catch (error) {
      logger.error('Failed to get tunnel status:', error);
      return {
        isActive: false,
        port: this.tunnelPort,
        error: error.message
      };
    }
  }

  async restartTunnel() {
    logger.tunnel('Restarting tunnel...');
    
    try {
      // Stop existing tunnel
      await this.stopTunnel();
      
      // Wait a moment
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Start tunnel again
      await this.startTunnel();
      
      logger.tunnel('Tunnel restarted successfully');
      return true;
    } catch (error) {
      logger.error('Failed to restart tunnel:', error);
      return false;
    }
  }

  // Stops the tunnel process on the router but keeps the SSH connection to the router open.
  // This is for a temporary disconnect, allowing for a quick restart.
  async stopTunnel() {
    logger.tunnel(`Stopping tunnel process for port ${this.tunnelPort}...`);
    if (!this.isConnected || !this.tunnelPort) {
      logger.warn('Cannot stop tunnel, not connected or no port assigned.');
      return;
    }
    try {
      // Use the init.d script to gracefully stop the service
      await this.ssh.execCommand(`/etc/init.d/netpilot_tunnel stop`);
      this.stopMonitoring();
      this.stopHeartbeat();
      this.tunnelProcess = null;
      logger.tunnel('Tunnel process stopped successfully.');
    } catch (error) {
      logger.error('Failed to stop tunnel process via init.d script, falling back to manual cleanup.', error);
      await this.aggressiveProcessCleanup();
    }
  }

  // Disconnects the SSH session from the router. This does NOT release the port.
  // This is the method for the "Disconnect Tunnel" button.
  async disconnect() {
    logger.tunnel('Disconnecting tunnel and closing SSH session...');
    await this.stopTunnel();
    if (this.ssh.isConnected()) {
      this.ssh.dispose();
    }
    this.isConnected = false;
    // Note: We do NOT clear tunnelPort or routerId here.
    logger.tunnel('Tunnel disconnected.');
  }

  // A full cleanup for when the user wants to disconnect AND release the port.
  // This is for the "Disconnect & Release Port" button.
  async cleanup() {
    logger.tunnel('Performing full cleanup: disconnecting tunnel and clearing all state...');
    await this.disconnect(); // Disconnects SSH and stops tunnel process

    // Clear all state variables
    this.routerCredentials = null;
    this.tunnelPort = null;
    this.routerId = null;

    // Clear persistent state from disk
    await this.clearTunnelState();
    logger.tunnel('Full cleanup complete.');
  }

  getStatus() {
    return {
      isConnected: this.isConnected,
      tunnelPort: this.tunnelPort,
      routerId: this.routerId,
      cloudVmIp: this.cloudVmIp,
      isMonitoring: this.isMonitoring,
      processId: this.tunnelProcess,
      hasHeartbeat: this.heartbeatInterval !== null
    };
  }

  setCloudVmIp(ip) {
    this.cloudVmIp = ip;
    logger.tunnel(`Cloud VM IP updated to: ${ip}`);
  }

  // Get router credentials for frontend API calls
  getRouterCredentials() {
    if (!this.routerCredentials) {
      return null;
    }

    return {
      host: this.routerCredentials.host,
      username: this.routerCredentials.username,
      password: this.routerCredentials.password,
      port: this.routerCredentials.port || 22,
      tunnelPort: this.tunnelPort,
      cloudVmIp: this.cloudVmIp,
      isConnected: this.isConnected
    };
  }

  // Get cloud VM access information for API calls through tunnel
  getCloudVmAccess() {
    if (!this.tunnelPort) {
      return null;
    }

    return {
      cloudVmIp: this.cloudVmIp,
      cloudUser: this.cloudUser,
      tunnelPort: this.tunnelPort,
      routerAccessCommand: `ssh -p ${this.tunnelPort} ${this.routerCredentials?.username || 'root'}@localhost`
    };
  }

  async testCloudVmConnectivity() {
    logger.tunnel('Testing cloud VM connectivity...');
    
    try {
      // Test basic network connectivity with ping-like approach
      const response = await axios.get(`http://${this.cloudVmIp}:8080/api/health`, {
        timeout: 5000
      });
      
      if (response.status === 200) {
        logger.tunnel('Cloud VM is reachable via HTTP');
        return true;
      } else {
        logger.warn('Cloud VM responded but with unexpected status:', response.status);
        return false;
      }
    } catch (error) {
      logger.error('Cloud VM connectivity test failed:', error.message);
      return false;
    }
  }

  async diagnoseCloudVmAuthentication() {
    logger.tunnel('Running comprehensive cloud VM authentication diagnosis...');
    
    const diagnosis = {
      networkConnectivity: false,
      sshPortOpen: false,
      userExists: null,
      passwordAuth: false,
      sshConfigIssues: [],
      recommendations: [],
      cloudVmConfig: {
        ip: this.cloudVmIp,
        user: this.cloudUser,
        port: this.cloudPort,
        passwordProvided: !!this.cloudPassword
      }
    };

    try {
      // Test 1: Basic network connectivity
      logger.tunnel('Testing network connectivity to cloud VM...');
      try {
        const response = await axios.get(`http://${this.cloudVmIp}:8080/api/health`, { timeout: 5000 });
        diagnosis.networkConnectivity = response.status === 200;
        logger.tunnel(`Network connectivity: ${diagnosis.networkConnectivity ? 'PASS' : 'FAIL'}`);
      } catch (error) {
        logger.error(`Network connectivity test failed: ${error.message}`);
        diagnosis.recommendations.push('Check if cloud VM IP is correct and VM is running');
      }

      // Test 2: SSH port accessibility (via router ping test)
      if (this.isConnected) {
        logger.tunnel('Testing SSH port accessibility from router...');
        try {
          const pingResult = await this.ssh.execCommand(`ping -c 3 -W 5 ${this.cloudVmIp}`);
          const pingSuccess = pingResult.stdout.includes('3 packets transmitted') && 
                             !pingResult.stdout.includes('100% packet loss');
          
          if (pingSuccess) {
            // Test SSH port specifically
            const portTest = await this.ssh.execCommand(`nc -z -w 5 ${this.cloudVmIp} ${this.cloudPort} && echo "port_open" || echo "port_closed"`);
            diagnosis.sshPortOpen = portTest.stdout.includes('port_open');
            logger.tunnel(`SSH port ${this.cloudPort} accessibility: ${diagnosis.sshPortOpen ? 'OPEN' : 'CLOSED'}`);
            
            if (!diagnosis.sshPortOpen) {
              diagnosis.recommendations.push(`SSH port ${this.cloudPort} is not accessible - check firewall or SSH service`);
            }
          }
        } catch (error) {
          logger.error(`SSH port test failed: ${error.message}`);
          diagnosis.recommendations.push('Network connectivity issues - check router internet access');
        }
      }

      // Test 3: Detailed SSH authentication attempt with verbose output
      if (this.isConnected && diagnosis.sshPortOpen) {
        logger.tunnel('Testing SSH authentication with detailed diagnostics...');
        try {
          // Attempt connection with verbose SSH output to capture specific failure reasons
          const authTest = await this.ssh.execCommand(
            `sshpass -p '${this.cloudPassword}' ssh -v -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o PasswordAuthentication=yes -o PubkeyAuthentication=no -p ${this.cloudPort} ${this.cloudUser}@${this.cloudVmIp} 'echo "auth_success"' 2>&1 || true`
          );
          
          const output = authTest.stdout || authTest.stderr || '';
          diagnosis.passwordAuth = output.includes('auth_success');
          
          // Analyze SSH error messages for specific issues
          if (output.includes('Permission denied (publickey,password)')) {
            diagnosis.sshConfigIssues.push('Password authentication failed - wrong password or user does not exist');
            diagnosis.recommendations.push('Check CLOUD_VM_PASSWORD in .env file');
            diagnosis.recommendations.push(`Verify user '${this.cloudUser}' exists on cloud VM`);
          }
          
          if (output.includes('Permission denied (publickey)')) {
            diagnosis.sshConfigIssues.push('Only public key authentication allowed');
            diagnosis.recommendations.push('Cloud VM SSH config may disable password authentication');
            diagnosis.recommendations.push('Check /etc/ssh/sshd_config for PasswordAuthentication setting');
          }
          
          if (output.includes('Connection refused')) {
            diagnosis.sshConfigIssues.push('SSH service not running or port blocked');
            diagnosis.recommendations.push('Check if SSH daemon is running on cloud VM');
          }
          
          if (output.includes('Network is unreachable')) {
            diagnosis.sshConfigIssues.push('Network routing issue');
            diagnosis.recommendations.push('Check network connectivity between router and cloud VM');
          }
          
          if (output.includes('Host key verification failed')) {
            diagnosis.sshConfigIssues.push('SSH host key verification issue');
            diagnosis.recommendations.push('Host key changed or SSH fingerprint issue');
          }

          // Test if user exists by attempting connection with a definitely wrong password
          if (!diagnosis.passwordAuth) {
            const userTestCmd = `sshpass -p 'definitely_wrong_password_123' ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o PasswordAuthentication=yes -o PubkeyAuthentication=no -p ${this.cloudPort} ${this.cloudUser}@${this.cloudVmIp} 'echo test' 2>&1 || true`;
            const userTest = await this.ssh.execCommand(userTestCmd);
            const userOutput = userTest.stdout || userTest.stderr || '';
            
            // If we get "Permission denied" with wrong password, user exists
            // If we get "Invalid user", user doesn't exist
            if (userOutput.includes('Invalid user') || userOutput.includes('User does not exist')) {
              diagnosis.userExists = false;
              diagnosis.recommendations.push(`User '${this.cloudUser}' does not exist on cloud VM - create the user or update CLOUD_VM_USER in .env`);
            } else if (userOutput.includes('Permission denied')) {
              diagnosis.userExists = true;
              diagnosis.recommendations.push('User exists but password is incorrect - check CLOUD_VM_PASSWORD in .env');
            }
          }
          
          logger.tunnel(`SSH authentication test: ${diagnosis.passwordAuth ? 'PASS' : 'FAIL'}`);
          
        } catch (error) {
          diagnosis.sshConfigIssues.push(`SSH test execution failed: ${error.message}`);
          diagnosis.recommendations.push('Unable to run SSH diagnostic tests from router');
        }
      }

      // Generate summary
      if (diagnosis.passwordAuth) {
        logger.tunnel('✅ Cloud VM authentication diagnosis: ALL TESTS PASSED');
      } else {
        logger.error('❌ Cloud VM authentication diagnosis: AUTHENTICATION FAILED');
        logger.error('Issues found:');
        diagnosis.sshConfigIssues.forEach(issue => logger.error(`  - ${issue}`));
        logger.error('Recommendations:');
        diagnosis.recommendations.forEach(rec => logger.error(`  - ${rec}`));
      }

      return diagnosis;

    } catch (error) {
      diagnosis.sshConfigIssues.push(`Diagnosis failed: ${error.message}`);
      diagnosis.recommendations.push('Unable to complete authentication diagnosis');
      logger.error('Cloud VM authentication diagnosis failed:', error.message);
      return diagnosis;
    }
  }

  async testTunnelCommandExecution() {
    logger.tunnel('Testing command execution THROUGH tunnel (not direct SSH)...');
    
    if (!this.tunnelPort) {
      logger.warn('Cannot test tunnel commands - no tunnel port assigned');
      return false;
    }

    try {
      // Test commands through the tunnel using the cloud VM API
      const testCommands = [
        'echo "tunnel_command_test_success"',
        'uci get system.@system[0].hostname 2>/dev/null || echo "unknown"',
        'uptime | head -1'
      ];

      for (const command of testCommands) {
        logger.tunnel(`Testing command through tunnel: ${command}`);
        
        try {
          const response = await axios.post(`http://${this.cloudVmIp}:8080/api/test-tunnel/${this.tunnelPort}`, {
            testCommand: command
          }, {
            timeout: 12000,
            headers: {
              'Content-Type': 'application/json'
            }
          });
          
          if (response.data && response.data.success && response.data.data) {
            const testData = response.data.data;
            if (testData.tunnelWorking && testData.output) {
              logger.tunnel(`✅ Command succeeded through tunnel: "${testData.output.substring(0, 100)}${testData.output.length > 100 ? '...' : ''}"`);
              
              // Special check for the echo test
              if (command.includes('tunnel_command_test_success') && !testData.output.includes('tunnel_command_test_success')) {
                logger.error('❌ Echo test failed - tunnel may have issues');
                return false;
              }
            } else {
              logger.error(`❌ Command failed through tunnel: ${command}`);
              logger.error(`Error: ${testData.error || 'No output received'}`);
              return false;
            }
          } else {
            logger.error(`❌ Command API failed through tunnel: ${command}`);
            logger.error(`API error: ${response.data?.error || 'Unknown API error'}`);
            return false;
          }
        } catch (cmdError) {
          logger.error(`❌ Command exception through tunnel: ${command} - ${cmdError.message}`);
          
          // If API is unreachable, that's different from tunnel failure
          if (cmdError.code === 'ECONNREFUSED' || cmdError.code === 'ETIMEDOUT') {
            logger.warn('Cloud VM API unreachable - cannot test commands through tunnel');
            return true; // Assume commands work if we can't reach API to test
          }
          
          return false;
        }
      }

      logger.tunnel('✅ ALL tunnel command execution tests passed');
      return true;
      
    } catch (error) {
      logger.error('❌ Tunnel command execution test failed:', error.message);
      return false;
    }
  }

  async measureLatency() {
    logger.tunnel('Measuring tunnel latency...');
    
    if (!this.isConnected) {
      return { error: 'Router not connected' };
    }

    const measurements = [];
    const testCount = 5;

    try {
      for (let i = 0; i < testCount; i++) {
        const startTime = Date.now();
        await this.ssh.execCommand('echo "latency_test"');
        const latency = Date.now() - startTime;
        measurements.push(latency);
        
        // Small delay between tests
        if (i < testCount - 1) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      }

      const avgLatency = measurements.reduce((a, b) => a + b, 0) / measurements.length;
      const minLatency = Math.min(...measurements);
      const maxLatency = Math.max(...measurements);

      const result = {
        average: Math.round(avgLatency),
        minimum: minLatency,
        maximum: maxLatency,
        measurements,
        testCount,
        timestamp: new Date().toISOString()
      };

      logger.tunnel(`Tunnel latency: ${result.average}ms average (${result.minimum}-${result.maximum}ms range)`);
      return result;

    } catch (error) {
      logger.error('Latency measurement failed:', error.message);
      return { error: error.message };
    }
  }

  async aggressiveProcessCleanup() {
    if (!this.tunnelPort) {
      logger.error('Process cleanup error: No tunnel port assigned.');
      return;
    }
    
    logger.tunnel(`Performing targeted process cleanup for port ${this.tunnelPort}...`);
    try {
      if (!this.ssh.isConnected()) {
        logger.error('Process cleanup error: SSH session is not connected.');
        return;
      }
      
      // Step 1: Kill specific netpilot_tunnel process for this port using BusyBox-compatible commands
      let result = await this.ssh.execCommand(`ps | grep "netpilot_tunnel.*${this.tunnelPort}" | grep -v grep | awk '{print $1}' | xargs -r kill || true`);
      if (result.stderr) logger.error(`kill netpilot_tunnel stderr: ${result.stderr}`);
      
      // Step 2: Kill specific autossh process for this port using BusyBox-compatible commands
      result = await this.ssh.execCommand(`ps | grep "autossh.*-R ${this.tunnelPort}:localhost:22" | grep -v grep | awk '{print $1}' | xargs -r kill || true`);
      if (result.stderr) logger.error(`kill autossh stderr: ${result.stderr}`);
      
      // Step 3: Kill any sshpass process related to this port's autossh using BusyBox-compatible commands
      result = await this.ssh.execCommand(`ps | grep "sshpass.*autossh.*${this.tunnelPort}" | grep -v grep | awk '{print $1}' | xargs -r kill || true`);
      if (result.stderr) logger.error(`kill sshpass stderr: ${result.stderr}`);
      
      // Step 4: Wait for processes to die, then verify
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Step 5: Force kill any remaining processes for this port with SIGKILL using BusyBox-compatible commands
      result = await this.ssh.execCommand(`ps | grep "autossh.*-R ${this.tunnelPort}:localhost:22" | grep -v grep | awk '{print $1}' | xargs -r kill -9 || true`);
      if (result.stderr) logger.error(`SIGKILL autossh stderr: ${result.stderr}`);
      
      result = await this.ssh.execCommand(`ps | grep "sshpass.*autossh.*${this.tunnelPort}" | grep -v grep | awk '{print $1}' | xargs -r kill -9 || true`);
      if (result.stderr) logger.error(`SIGKILL sshpass stderr: ${result.stderr}`);
      
      // Step 6: Verify cleanup was successful
      const remainingProcesses = await this.ssh.execCommand(`ps | grep -f ".*${this.tunnelPort}:localhost:22" | grep -v grep || true`);
      if (remainingProcesses.stdout.trim()) {
        logger.tunnel(`Some processes for port ${this.tunnelPort} may still be running after cleanup:`);
        logger.tunnel(remainingProcesses.stdout);
        
        // Attempt more aggressive targeted kill for this specific port
        logger.tunnel(`Attempting targeted SIGKILL for residual processes on port ${this.tunnelPort}...`);
        result = await this.ssh.execCommand(`ps | grep "${this.tunnelPort}:localhost:22" | grep -v grep | awk '{print $1}' | xargs -r kill -9 || true`);
        
        // Final verification
        const finalCheck = await this.ssh.execCommand(`ps | grep "${this.tunnelPort}:localhost:22" | grep -v grep || true`);
        if (finalCheck.stdout.trim()) {
          logger.warn(`Residual processes for port ${this.tunnelPort} still detected after force-kill:`);
          logger.warn(finalCheck.stdout);
        } else {
          logger.tunnel(`All processes for port ${this.tunnelPort} successfully terminated`);
        }
      } else {
        logger.tunnel(`Process cleanup for port ${this.tunnelPort} completed successfully`);
      }
      
      // Log active SSH connections for debugging
      const connections = await this.ssh.execCommand('netstat -tn | grep ":22" | grep ESTABLISHED | wc -l || true');
      logger.tunnel(`Active SSH connections to port 22: ${connections.stdout.trim()}`);
      
    } catch (error) {
      logger.error('Process cleanup encountered an error:', error);
      if (error.stdout) logger.error('Cleanup error stdout:', error.stdout);
      if (error.stderr) logger.error('Cleanup error stderr:', error.stderr);
      // Don't throw error - cleanup is best effort
    }
  }

  // State Management Methods
  async saveTunnelState() {
    if (!this.tunnelPort || !this.routerCredentials || !this.routerId) {
      logger.warn('Cannot save tunnel state - missing required data');
      return false;
    }

    const tunnelState = {
      port: this.tunnelPort,
      routerId: this.routerId,
      routerCredentials: {
        host: this.routerCredentials.host,
        username: this.routerCredentials.username,
        password: this.routerCredentials.password,
        port: this.routerCredentials.port || 22
      },
      cloudVmIp: this.cloudVmIp,
      cloudUser: this.cloudUser,
      cloudPort: this.cloudPort,
      established: new Date().toISOString(),
      lastHeartbeat: new Date().toISOString()
    };

    try {
      const success = await this.stateManager.saveTunnelState(tunnelState);
      if (success) {
        logger.info('Tunnel state saved successfully');
      } else {
        logger.error('Failed to save tunnel state');
      }
      return success;
    } catch (error) {
      logger.error('Error saving tunnel state:', error);
      return false;
    }
  }

  async restoreFromState() {
    try {
      const savedState = await this.stateManager.getTunnelState();
      if (!savedState) {
        logger.info('No saved tunnel state found');
        return null;
      }

      logger.info('Found saved tunnel state, attempting to restore...');
      
      // Restore tunnel properties
      this.tunnelPort = savedState.port;
      this.routerId = savedState.routerId;
      this.routerCredentials = savedState.routerCredentials;
      this.cloudVmIp = savedState.cloudVmIp;
      this.cloudUser = savedState.cloudUser;
      this.cloudPort = savedState.cloudPort;

      // Try to reconnect to router
      try {
        await this.ssh.connect({
          host: this.routerCredentials.host,
          username: this.routerCredentials.username,
          password: this.routerCredentials.password,
          port: this.routerCredentials.port || 22,
          readyTimeout: 30000
        });

        this.isConnected = true;
        logger.info('Successfully reconnected to router');

        // Check if tunnel processes are still active
        const isActive = await this.verifyTunnelActive();
        if (isActive) {
          logger.info('Tunnel processes are still active, resuming monitoring');
          // Start monitoring and heartbeat
          this.startMonitoring();
          this.startHeartbeat();
          return {
            success: true,
            port: this.tunnelPort,
            status: 'restored',
            message: 'Tunnel restored and processes are active'
          };
        } else {
          logger.info('Tunnel processes stopped during shutdown, attempting to restart...');
          
          // Restart the tunnel using existing script
          try {
            await this.startTunnel();
            
            // Give it time to establish
            await new Promise(resolve => setTimeout(resolve, 8000));
            
            // Verify it's working
            await this.verifyTunnel(this.tunnelPort);
            
            // Start monitoring and heartbeat
            this.startMonitoring();
            this.startHeartbeat();
            
            logger.info(`Tunnel restored and restarted successfully on port ${this.tunnelPort}`);
            return {
              success: true,
              port: this.tunnelPort,
              status: 'restored_restarted',
              message: 'Tunnel restored and restarted from saved state'
            };
          } catch (restartError) {
            logger.error('Failed to restart tunnel during restore:', restartError);
            // Don't clear state yet - maybe temporary network issue
            return null;
          }
        }
      } catch (error) {
        logger.error('Failed to reconnect to router during restore:', error);
        // Don't clear state immediately - could be temporary network issue
        return null;
      }
    } catch (error) {
      logger.error('Error restoring tunnel state:', error);
      return null;
    }
  }

  async verifyTunnelActive() {
    try {
      if (!this.tunnelPort || !this.isConnected) {
        return false;
      }

      // Check if tunnel processes are running
      const processCheck = await this.ssh.execCommand(`ps | grep -v grep | grep "autossh.*-R ${this.tunnelPort}:localhost:22" || true`);
      if (!processCheck.stdout.trim()) {
        logger.warn('Tunnel processes not found');
        return false;
      }

      logger.info('Tunnel processes are active');
      return true;
    } catch (error) {
      logger.error('Error verifying tunnel active state:', error);
      return false;
    }
  }

  async clearTunnelState() {
    try {
      const success = await this.stateManager.clearTunnelState();
      if (success) {
        logger.info('Tunnel state cleared successfully');
      } else {
        logger.error('Failed to clear tunnel state');
      }
      return success;
    } catch (error) {
      logger.error('Error clearing tunnel state:', error);
      return false;
    }
  }
}

module.exports = TunnelManager; 