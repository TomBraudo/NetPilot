const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const PortManager = require('./services/PortManager');
const HealthMonitor = require('./services/HealthMonitor');

class CloudPortManagerServer {
  constructor() {
    this.app = express();
    this.port = process.env.PORT || 8080;
    this.portManager = new PortManager();
    this.healthMonitor = new HealthMonitor(this.portManager);
    
    // Admin token for secure operations
    this.adminToken = process.env.ADMIN_TOKEN || '93701c2ddd920ec71a215e2c59269d656334c9e490a9264e7f3ec0c0d2325b87';
    
    this.setupMiddleware();
    this.setupRoutes();
    this.setupErrorHandling();
  }

  setupMiddleware() {
    // Security middleware
    this.app.use(helmet());
    
    // CORS configuration
    this.app.use(cors({
      origin: '*', // In production, restrict to specific origins
      methods: ['GET', 'POST', 'PUT', 'DELETE'],
      allowedHeaders: ['Content-Type', 'Authorization']
    }));
    
    // Body parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));
    
    // Logging
    this.app.use(morgan('combined'));
  }

  setupRoutes() {
    // Health check endpoint
    this.app.get('/api/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        service: 'netpilot-cloud-port-manager',
        version: '1.0.0'
      });
    });

    // Port allocation endpoint
    this.app.post('/api/allocate-port', async (req, res) => {
      try {
        const { routerId, routerCredentials } = req.body;
        
        if (!routerId) {
          return res.status(400).json({
            success: false,
            error: 'Router ID is required'
          });
        }

        // Validate router credentials if provided
        if (routerCredentials && (!routerCredentials.username || !routerCredentials.password)) {
          return res.status(400).json({
            success: false,
            error: 'Router credentials must include both username and password'
          });
        }

        const allocation = await this.portManager.allocatePort(routerId, routerCredentials);
        
        res.json({
          success: true,
          data: allocation
        });
      } catch (error) {
        console.error('Port allocation error:', error);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Port release endpoint
    this.app.post('/api/release-port/:port', async (req, res) => {
      try {
        const { port } = req.params;
        const { routerId } = req.body;

        if (!routerId) {
          return res.status(400).json({
            success: false,
            error: 'Router ID is required'
          });
        }

        const released = await this.portManager.releasePort(parseInt(port), routerId);
        
        res.json({
          success: true,
          data: { released, port: parseInt(port) }
        });
      } catch (error) {
        console.error('Port release error:', error);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Port status endpoint
    this.app.get('/api/port-status', async (req, res) => {
      try {
        const { routerId, port } = req.query;
        
        if (port) {
          const status = await this.portManager.getPortStatus(parseInt(port));
          return res.json({
            success: true,
            data: status
          });
        }
        
        if (routerId) {
          const allocation = await this.portManager.getAllocationByRouterId(routerId);
          return res.json({
            success: true,
            data: allocation
          });
        }
        
        // Return all port allocations
        const allAllocations = await this.portManager.getAllAllocations();
        res.json({
          success: true,
          data: allAllocations
        });
      } catch (error) {
        console.error('Port status error:', error);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Router heartbeat endpoint
    this.app.post('/api/heartbeat/:port', async (req, res) => {
      try {
        const { port } = req.params;
        const { routerId } = req.body;

        await this.portManager.updateHeartbeat(parseInt(port), routerId);
        
        res.json({
          success: true,
          data: { port: parseInt(port), lastHeartbeat: new Date().toISOString() }
        });
      } catch (error) {
        console.error('Heartbeat error:', error);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Tunnel connectivity test endpoint - actually tests SSH through reverse tunnel
    this.app.post('/api/test-tunnel/:port', async (req, res) => {
      try {
        const { port } = req.params;
        const { testCommand = 'echo "tunnel_test_success"' } = req.body;
        const { exec } = require('child_process');
        const { promisify } = require('util');
        const execAsync = promisify(exec);
        
        const tunnelPort = parseInt(port);
        
        if (!tunnelPort || tunnelPort < 1024 || tunnelPort > 65535) {
          return res.status(400).json({
            success: false,
            error: 'Invalid port number'
          });
        }
        
        console.log(`Testing tunnel connectivity on port ${tunnelPort}...`);
        
        // Get router credentials for this port
        const credentials = await this.portManager.getRouterCredentialsByPort(tunnelPort);
        
        if (!credentials || !credentials.username || !credentials.password) {
          return res.status(400).json({
            success: false,
            error: 'No router credentials found for this port - cannot authenticate tunnel test'
          });
        }
        
        console.log(`Using router credentials: ${credentials.username} for tunnel test on port ${tunnelPort}`);
        
        // Test actual SSH connection through the tunnel with password authentication
        const sshTestCommand = `timeout 10 sshpass -p '${credentials.password}' ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o PasswordAuthentication=yes -o PubkeyAuthentication=no -p ${tunnelPort} ${credentials.username}@localhost "${testCommand}" 2>/dev/null`;        
        try {
          const { stdout, stderr } = await execAsync(sshTestCommand);
          
          // Check if we got expected output
          const isSuccess = stdout.includes('tunnel_test_success') || stdout.trim().length > 0;
          
          res.json({
            success: isSuccess,
            data: {
              port: tunnelPort,
              testCommand,
              output: stdout.trim(),
              stderr: stderr.trim(),
              timestamp: new Date().toISOString(),
              tunnelWorking: isSuccess
            }
          });
          
          console.log(`Tunnel test on port ${tunnelPort}: ${isSuccess ? 'SUCCESS' : 'FAILED'}`);
          
        } catch (execError) {
          // SSH connection failed - tunnel is not working
          console.log(`Tunnel test on port ${tunnelPort}: FAILED - ${execError.message}`);
          
          res.json({
            success: false,
            data: {
              port: tunnelPort,
              testCommand,
              error: execError.message,
              timestamp: new Date().toISOString(),
              tunnelWorking: false
            }
          });
        }
        
      } catch (error) {
        console.error('Tunnel test error:', error);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Admin endpoint - get all active allocations
    this.app.get('/api/admin/allocations', async (req, res) => {
      try {
        const allocations = await this.portManager.getAllAllocations();
        res.json({
          success: true,
          data: allocations
        });
      } catch (error) {
        console.error('Admin allocations error:', error);
        res.status(500).json({
          success: false,
          error: error.message
        });
      }
    });

    // Admin endpoint - reset all allocations (requires admin token)
    this.app.post('/api/admin/reset-all', async (req, res) => {
      try {
        const authHeader = req.headers['authorization'] || '';
        const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7) : authHeader;

        if (token !== this.adminToken) {
          return res.status(403).json({
            success: false,
            error: 'Forbidden: Invalid admin token'
          });
        }

        const deletedCount = await this.portManager.resetAllAllocations();

        res.json({
          success: true,
          data: {
            message: 'All port allocations have been reset',
            deletedRecords: deletedCount
          }
        });
      } catch (error) {
        console.error('Admin reset-all error:', error);
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
        error: 'Endpoint not found'
      });
    });
  }

  setupErrorHandling() {
    // Global error handler
    this.app.use((error, req, res, next) => {
      console.error('Unhandled error:', error);
      res.status(500).json({
        success: false,
        error: 'Internal server error'
      });
    });
  }

  async start() {
    try {
      console.log('Starting NetPilot Cloud Port Manager...');
      
      // Initialize port manager database
      console.log('Initializing database...');
      await this.portManager.initialize();
      console.log('Database initialized successfully');
      
      // Start server
      const server = this.app.listen(this.port, '0.0.0.0', () => {
        console.log(`NetPilot Cloud Port Manager running on port ${this.port}`);
        console.log(`Health check: http://localhost:${this.port}/api/health`);
        console.log(`Port allocation: POST http://localhost:${this.port}/api/allocate-port`);
        
        // Start health monitoring after server is listening
        console.log('Starting health monitor...');
        this.healthMonitor.start();
        console.log('Service startup completed successfully');
      });
      
      server.on('error', (error) => {
        console.error('Server error:', error);
        process.exit(1);
      });
      
    } catch (error) {
      console.error('Failed to start server:', error);
      process.exit(1);
    }
  }

  async stop() {
    try {
      this.healthMonitor.stop();
      await this.portManager.cleanup();
      console.log('Cloud Port Manager stopped gracefully');
    } catch (error) {
      console.error('Error during shutdown:', error);
    }
  }
}

// Handle graceful shutdown
const server = new CloudPortManagerServer();

process.on('SIGTERM', () => server.stop());
process.on('SIGINT', () => server.stop());

// Start the server
server.start();

module.exports = CloudPortManagerServer; 