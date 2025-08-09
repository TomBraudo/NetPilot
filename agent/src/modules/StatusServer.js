const express = require('express');
const cors = require('cors');
const logger = require('../utils/Logger');

/**
 * StatusServer - HTTP API for NetPilot Agent Status
 * Phase 7.3: Status API Implementation
 * 
 * Provides REST endpoints for monitoring agent status,
 * tunnel connectivity, and troubleshooting information.
 */
class StatusServer {
  constructor(routerManager, tunnelManager, portAllocator) {
    this.routerManager = routerManager;
    this.tunnelManager = tunnelManager;
    this.portAllocator = portAllocator;
    
    this.app = express();
    this.server = null;
    this.port = process.env.AGENT_API_PORT || 3030;
    this.isRunning = false;
    this.logs = [];
    this.maxLogs = 1000;
    
    this.setupMiddleware();
    this.setupRoutes();
  }

  setupMiddleware() {
    // CORS for cross-origin requests
    this.app.use(cors({
      origin: ['http://localhost:3000', 'http://127.0.0.1:3000'],
      credentials: true
    }));
    
    // JSON parsing
    this.app.use(express.json());
    
    // Request logging
    this.app.use((req, res, next) => {
      this.addLog('INFO', `${req.method} ${req.path} - ${req.ip}`);
      next();
    });
  }

  setupRoutes() {
    // Health check endpoint
    this.app.get('/api/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        version: require('../../package.json').version || '1.0.0'
      });
    });

    // Comprehensive status endpoint
    this.app.get('/api/status', async (req, res) => {
      try {
        const status = await this.getComprehensiveStatus();
        res.json({
          success: true,
          timestamp: new Date().toISOString(),
          data: status
        });
      } catch (error) {
        this.addLog('ERROR', `Status endpoint error: ${error.message}`);
        res.status(500).json({
          success: false,
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    });

    // Logs endpoint for troubleshooting
    this.app.get('/api/logs', (req, res) => {
      const level = req.query.level;
      const limit = parseInt(req.query.limit) || 100;
      
      let filteredLogs = this.logs;
      if (level) {
        filteredLogs = this.logs.filter(log => log.level === level.toUpperCase());
      }
      
      // Get most recent logs
      const recentLogs = filteredLogs.slice(-limit);
      
      res.json({
        success: true,
        timestamp: new Date().toISOString(),
        totalLogs: this.logs.length,
        filteredCount: filteredLogs.length,
        returnedCount: recentLogs.length,
        logs: recentLogs
      });
    });

    // Router verification endpoint
    this.app.post('/api/verify/router', async (req, res) => {
      try {
        const { credentials } = req.body;
        if (!credentials) {
          return res.status(400).json({
            success: false,
            error: 'Router credentials required'
          });
        }

        const verification = await this.verifyRouterSetup(credentials);
        res.json({
          success: true,
          timestamp: new Date().toISOString(),
          data: verification
        });
      } catch (error) {
        this.addLog('ERROR', `Router verification error: ${error.message}`);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Ensure AdGuard Home endpoint (optional HTTP access)
    this.app.post('/api/ensure/adguard', async (req, res) => {
      try {
        const { credentials } = req.body || {};
        if (!credentials) {
          return res.status(400).json({ success: false, error: 'Router credentials required' });
        }
        const result = await this.routerManager.ensureAdGuardHome(credentials);
        res.json({ success: true, data: result });
      } catch (error) {
        this.addLog('ERROR', `Ensure AdGuard Home error: ${error.message}`);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Tunnel verification endpoint
    this.app.get('/api/verify/tunnel', async (req, res) => {
      try {
        const verification = await this.verifyTunnelConnectivity();
        res.json({
          success: true,
          timestamp: new Date().toISOString(),
          data: verification
        });
      } catch (error) {
        this.addLog('ERROR', `Tunnel verification error: ${error.message}`);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Command execution test endpoint
    this.app.post('/api/test/command', async (req, res) => {
      try {
        const { command } = req.body;
        if (!command) {
          return res.status(400).json({
            success: false,
            error: 'Command required'
          });
        }

        const result = await this.testCommandExecution(command);
        res.json({
          success: true,
          timestamp: new Date().toISOString(),
          data: result
        });
      } catch (error) {
        this.addLog('ERROR', `Command test error: ${error.message}`);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Latency measurement endpoint
    this.app.get('/api/test/latency', async (req, res) => {
      try {
        const latency = await this.measureTunnelLatency();
        res.json({
          success: true,
          timestamp: new Date().toISOString(),
          data: latency
        });
      } catch (error) {
        this.addLog('ERROR', `Latency test error: ${error.message}`);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

        // Admin endpoint - manual autossh cleanup
        this.app.post('/api/admin/autossh-cleanup', async (req, res) => {
          try {
            // Token validation (Authorization: Bearer <token>)
            const authHeader = req.headers['authorization'] || '';
            const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7) : authHeader;
    
            // Get token from ConfigManager, NOT process.env
            const cleanupToken = this.routerManager.configManager.get('autosshCleanupToken');
            
            this.addLog('INFO', `[CLEANUP] Admin cleanup triggered. Token provided: ${token ? '******' : 'NONE'}. Token expected: ${cleanupToken ? '******' : 'NOT FOUND'}`);
    
            if (!cleanupToken || token !== cleanupToken) {
              return res.status(403).json({
                success: false,
                error: 'Forbidden: Invalid cleanup token'
              });
            }
    
            // Perform cleanup via TunnelManager
            if (typeof this.tunnelManager.aggressiveProcessCleanup === 'function') {
              await this.tunnelManager.aggressiveProcessCleanup();
            } else {
              this.addLog('WARN', 'aggressiveProcessCleanup function not found on TunnelManager');
            }
    
            res.json({
              success: true,
              message: 'Autossh cleanup executed'
            });
          } catch (error) {
            this.addLog('ERROR', `Autossh cleanup error: ${error.message}`);
            res.status(500).json({
              success: false,
              error: error.message
            });
          }
        });

    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        success: false,
        error: 'Endpoint not found',
        available_endpoints: [
          'GET /api/health',
          'GET /api/status', 
          'GET /api/logs',
          'POST /api/verify/router',
          'GET /api/verify/tunnel',
          'POST /api/test/command',
          'GET /api/test/latency',
          'POST /api/admin/autossh-cleanup'
        ]
      });
    });
  }

  async getComprehensiveStatus() {
    const router = this.routerManager.getConnectionStatus();
    const tunnel = this.tunnelManager.getStatus();
    const port = this.portAllocator.getPortInfo();

    return {
      agent: {
        version: require('../../package.json').version || '1.0.0',
        uptime: process.uptime(),
        apiPort: this.port,
        isApiRunning: this.isRunning
      },
      router: {
        ...router,
        lastVerification: await this.getLastVerificationStatus()
      },
      tunnel: {
        ...tunnel,
        lastLatencyTest: await this.getLastLatencyTest()
      },
      portAllocation: port,
      systemHealth: {
        memoryUsage: process.memoryUsage(),
        cpuUsage: process.cpuUsage(),
        timestamp: new Date().toISOString()
      }
    };
  }

  async verifyRouterSetup(credentials) {
    this.addLog('INFO', 'Starting comprehensive router verification');
    
    try {
      // Connect to router for verification
      await this.routerManager.ssh.connect({
        host: credentials.host,
        username: credentials.username,
        password: credentials.password,
        port: credentials.port || 22,
        readyTimeout: 10000
      });
      this.routerManager.isConnected = true;

      // Run compatibility check
      const compatibility = await this.routerManager.verifyNetPilotCompatibility();
      
      // Test sample NetPilot commands
      const sampleCommands = await this.testSampleNetPilotCommands();
      
      // Get router info
      const routerInfo = await this.routerManager.getRouterInfo();
      
      await this.routerManager.disconnect();
      
      const verification = {
        compatibility,
        sampleCommands,
        routerInfo,
        timestamp: new Date().toISOString(),
        overallStatus: compatibility.overall && sampleCommands.overall ? 'PASS' : 'FAIL'
      };

      this.addLog('INFO', `Router verification completed: ${verification.overallStatus}`);
      return verification;
      
    } catch (error) {
      await this.routerManager.disconnect();
      this.addLog('ERROR', `Router verification failed: ${error.message}`);
      throw error;
    }
  }

  async testSampleNetPilotCommands() {
    this.addLog('INFO', 'Testing sample NetPilot commands');
    
    const tests = {
      uci_access: false,
      nft_qos_available: false,
      network_interfaces: false,
      nohup_available: false,
      sshpass_available: false,
      autossh_available: false,
      ssh_client_available: false,
      overall: false
    };

    try {
      // Test UCI access (configuration interface)
      const uciTest = await this.routerManager.executeCommand('uci show system.@system[0].hostname');
      tests.uci_access = uciTest.stdout.length > 0;

      // Test nft-qos availability (CLI/service presence)
      const nftQosTest = await this.routerManager.executeCommand('[ -x /etc/init.d/nft-qos ] && echo found || (opkg list-installed | grep -q "^nft-qos\\s" && echo found || echo not_found)');
      tests.nft_qos_available = nftQosTest.stdout.includes('found');

      // Test network interface access
      const ifTest = await this.routerManager.executeCommand('ip link show');
      tests.network_interfaces = ifTest.stdout.includes('link/ether');

      // NEW: Test tunnel-specific commands
      // Test nohup availability (critical for process detachment)
      const nohupTest = await this.routerManager.executeCommand('which nohup || echo "not_found"');
      tests.nohup_available = !nohupTest.stdout.includes('not_found');

      // Test sshpass availability (critical for password auth)
      const sshpassTest = await this.routerManager.executeCommand('which sshpass || echo "not_found"');
      tests.sshpass_available = !sshpassTest.stdout.includes('not_found');

      // Test autossh availability (critical for persistent tunnels)
      const autosshTest = await this.routerManager.executeCommand('which autossh || echo "not_found"');
      tests.autossh_available = !autosshTest.stdout.includes('not_found');

      // Test SSH client availability (critical for tunnel connections)
      const sshTest = await this.routerManager.executeCommand('which ssh || echo "not_found"');
      tests.ssh_client_available = !sshTest.stdout.includes('not_found');

      // Overall requires config + tunnel tooling + nft-qos present
      tests.overall = tests.uci_access && tests.network_interfaces && tests.nohup_available && 
                      tests.sshpass_available && tests.autossh_available && tests.ssh_client_available &&
                      tests.nft_qos_available;
      
      this.addLog('INFO', `Sample command tests: ${tests.overall ? 'PASS' : 'FAIL'}`);
      this.addLog('INFO', `Tunnel commands: nohup=${tests.nohup_available}, sshpass=${tests.sshpass_available}, autossh=${tests.autossh_available}, ssh=${tests.ssh_client_available}, nft-qos=${tests.nft_qos_available}`);
      return tests;
      
    } catch (error) {
      this.addLog('ERROR', `Sample command test failed: ${error.message}`);
      return tests;
    }
  }

  async verifyTunnelConnectivity() {
    this.addLog('INFO', 'Starting tunnel connectivity verification');
    
    const verification = {
      cloudVmConnectivity: false,
      cloudVmAuthentication: false,
      tunnelProcessCapability: false,
      routerToCloudLatency: null,
      cloudVmInfo: null,
      overall: false,
      error: null
    };

    try {
      // Test if we have tunnel manager and cloud VM config
      if (!this.tunnelManager) {
        throw new Error('Tunnel manager not available');
      }

      // Get cloud VM configuration
      const cloudVmIp = this.tunnelManager.cloudVmIp;
      const cloudUser = this.tunnelManager.cloudUser;
      const cloudPort = this.tunnelManager.cloudPort;
      const cloudPassword = this.tunnelManager.cloudPassword;

      if (!cloudVmIp || !cloudUser || !cloudPassword) {
        throw new Error('Cloud VM configuration incomplete - missing IP, user, or password');
      }

      verification.cloudVmInfo = {
        ip: cloudVmIp,
        user: cloudUser,
        port: cloudPort,
        passwordConfigured: !!cloudPassword
      };

      // Test 1: Basic connectivity to cloud VM (ping test from router)
      if (this.routerManager.isConnected) {
        try {
          const pingResult = await this.routerManager.executeCommand(`ping -c 3 -W 5 ${cloudVmIp}`);
          verification.cloudVmConnectivity = pingResult.stdout.includes('3 packets transmitted') && 
                                           !pingResult.stdout.includes('100% packet loss');
          
          // Extract latency if available
          const latencyMatch = pingResult.stdout.match(/avg = ([0-9.]+)/);
          if (latencyMatch) {
            verification.routerToCloudLatency = parseFloat(latencyMatch[1]);
          }
        } catch (pingError) {
          this.addLog('ERROR', `Cloud VM ping test failed: ${pingError.message}`);
          verification.cloudVmConnectivity = false;
        }
      } else {
        this.addLog('WARNING', 'Router not connected - skipping ping test');
        verification.cloudVmConnectivity = null; // Unknown
      }

      // Test 2: SSH authentication to cloud VM (from router)
      if (this.routerManager.isConnected && verification.cloudVmConnectivity) {
        try {
          const authTestCommand = `sshpass -p '${cloudPassword}' ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -p ${cloudPort} ${cloudUser}@${cloudVmIp} 'echo "auth_test_success"'`;
          const authResult = await this.routerManager.executeCommand(authTestCommand);
          verification.cloudVmAuthentication = authResult.stdout.includes('auth_test_success');
        } catch (authError) {
          this.addLog('ERROR', `Cloud VM authentication test failed: ${authError.message}`);
          verification.cloudVmAuthentication = false;
        }
      }

      // Test 3: Process detachment capability (nohup test)
      if (this.routerManager.isConnected) {
        try {
          const nohupTestCommand = 'nohup echo "process_detachment_test" > /tmp/detach_test 2>&1 && sleep 1 && cat /tmp/detach_test && rm -f /tmp/detach_test';
          const nohupResult = await this.routerManager.executeCommand(nohupTestCommand);
          verification.tunnelProcessCapability = nohupResult.stdout.includes('process_detachment_test');
        } catch (nohupError) {
          this.addLog('ERROR', `Process detachment test failed: ${nohupError.message}`);
          verification.tunnelProcessCapability = false;
        }
      }

      // If authentication failed, run comprehensive diagnosis
      if (!verification.cloudVmAuthentication && this.routerManager.isConnected) {
        this.addLog('INFO', 'Running comprehensive cloud VM authentication diagnosis...');
        try {
          const diagnosis = await this.tunnelManager.diagnoseCloudVmAuthentication();
          verification.authenticationDiagnosis = diagnosis;
          
          // Log detailed diagnostic information
          this.addLog('INFO', `Authentication diagnosis completed - Issues: ${diagnosis.sshConfigIssues.length}, Recommendations: ${diagnosis.recommendations.length}`);
        } catch (diagError) {
          this.addLog('ERROR', `Authentication diagnosis failed: ${diagError.message}`);
          verification.authenticationDiagnosis = { error: diagError.message };
        }
      }

      // Overall verification requires all critical components
      verification.overall = verification.cloudVmConnectivity && 
                            verification.cloudVmAuthentication && 
                            verification.tunnelProcessCapability;

      this.addLog('INFO', `Tunnel connectivity verification: ${verification.overall ? 'PASS' : 'FAIL'}`);
      this.addLog('INFO', `Cloud VM: connectivity=${verification.cloudVmConnectivity}, auth=${verification.cloudVmAuthentication}, processes=${verification.tunnelProcessCapability}`);
      
      return verification;

    } catch (error) {
      verification.error = error.message;
      this.addLog('ERROR', `Tunnel connectivity verification failed: ${error.message}`);
      return verification;
    }
  }

  async testTunnelCommandExecution() {
    // Test if commands can be executed through the tunnel
    try {
      if (!this.tunnelManager.isConnected || !this.tunnelManager.tunnelPort) {
        this.addLog('ERROR', 'Tunnel command execution test failed: Not connected to router');
        return false;
      }
      
      // Test basic command execution through tunnel SSH connection
      const testResult = await this.tunnelManager.testTunnelCommandExecution();
      
      if (testResult) {
        this.addLog('INFO', 'Tunnel command execution test passed');
        return true;
      } else {
        this.addLog('ERROR', 'Tunnel command execution test failed: Commands not working through tunnel');
        return false;
      }
      
    } catch (error) {
      this.addLog('ERROR', `Tunnel command execution test failed: ${error.message}`);
      return false;
    }
  }

  async testCommandExecution(command) {
    this.addLog('INFO', `Testing command execution: ${command}`);
    
    if (!this.routerManager.isConnected) {
      throw new Error('Router not connected');
    }
    
    const startTime = Date.now();
    const result = await this.routerManager.executeCommand(command);
    const executionTime = Date.now() - startTime;
    
    return {
      command,
      stdout: result.stdout,
      stderr: result.stderr,
      executionTime,
      success: result.code === 0 || result.code === undefined
    };
  }

  async measureTunnelLatency() {
    this.addLog('INFO', 'Measuring tunnel latency');
    
    if (!this.routerManager.isConnected) {
      return { error: 'Router not connected' };
    }
    
    const measurements = [];
    const testCount = 5;
    
    try {
      for (let i = 0; i < testCount; i++) {
        const startTime = Date.now();
        await this.routerManager.executeCommand('echo "latency_test"');
        const latency = Date.now() - startTime;
        measurements.push(latency);
        
        // Small delay between tests
        await new Promise(resolve => setTimeout(resolve, 100));
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
      
      this.addLog('INFO', `Tunnel latency: ${result.average}ms avg`);
      return result;
      
    } catch (error) {
      this.addLog('ERROR', `Latency measurement failed: ${error.message}`);
      return { error: error.message };
    }
  }

  async getLastVerificationStatus() {
    // Return cached verification status if available
    return { status: 'Not verified yet' };
  }

  async getLastLatencyTest() {
    // Return cached latency test if available
    return { status: 'Not tested yet' };
  }

  addLog(level, message) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      level: level.toUpperCase(),
      message
    };
    
    this.logs.push(logEntry);
    
    // Trim logs if too many
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }
    
    // Use custom logger for consistent formatting
    logger.log(level, 'STATUS', message);
  }

  async start() {
    return new Promise((resolve, reject) => {
      try {
        this.server = this.app.listen(this.port, '127.0.0.1', () => {
          this.isRunning = true;
          this.addLog('INFO', `Status API server started on http://127.0.0.1:${this.port}`);
          resolve();
        });
        
        this.server.on('error', (error) => {
          this.addLog('ERROR', `Status API server error: ${error.message}`);
          reject(error);
        });
        
      } catch (error) {
        this.addLog('ERROR', `Failed to start status API server: ${error.message}`);
        reject(error);
      }
    });
  }

  async stop() {
    return new Promise((resolve) => {
      if (this.server) {
        this.server.close(() => {
          this.isRunning = false;
          this.addLog('INFO', 'Status API server stopped');
          resolve();
        });
      } else {
        resolve();
      }
    });
  }

  getServerInfo() {
    return {
      isRunning: this.isRunning,
      port: this.port,
      endpoints: [
        'GET /api/health',
        'GET /api/status', 
        'GET /api/logs',
        'POST /api/verify/router',
        'GET /api/verify/tunnel',
        'POST /api/test/command',
        'GET /api/test/latency',
        'POST /api/ensure/adguard'
      ]
    };
  }
}

module.exports = StatusServer;