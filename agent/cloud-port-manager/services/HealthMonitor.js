const { spawn } = require('child_process');

class HealthMonitor {
  constructor(portManager) {
    this.portManager = portManager;
    this.checkInterval = 5 * 60 * 1000; // 5 minutes
    this.cleanupInterval = 60 * 60 * 1000; // 1 hour
    this.monitorTimer = null;
    this.cleanupTimer = null;
    this.isRunning = false;
  }

  start() {
    if (this.isRunning) {
      console.log('Health monitor is already running');
      return;
    }

    console.log('Starting health monitor...');
    this.isRunning = true;

    // Start periodic health checks
    this.monitorTimer = setInterval(() => {
      this.performHealthChecks().catch(error => {
        console.error('Health check failed:', error);
      });
    }, this.checkInterval);

    // Start periodic cleanup
    this.cleanupTimer = setInterval(() => {
      this.performCleanup().catch(error => {
        console.error('Cleanup failed:', error);
      });
    }, this.cleanupInterval);

    // Perform initial checks
    setTimeout(() => {
      this.performHealthChecks().catch(error => {
        console.error('Initial health check failed:', error);
      });
    }, 5000); // Wait 5 seconds after startup
  }

  stop() {
    if (!this.isRunning) {
      return;
    }

    console.log('Stopping health monitor...');
    this.isRunning = false;

    if (this.monitorTimer) {
      clearInterval(this.monitorTimer);
      this.monitorTimer = null;
    }

    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }
  }

  async performHealthChecks() {
    try {
      console.log('Performing health checks...');
      
      const allocations = await this.portManager.getAllAllocations();
      
      if (allocations.length === 0) {
        console.log('No active allocations to check');
        return;
      }

      console.log(`Checking health of ${allocations.length} active tunnel(s)`);
      
      const healthResults = await Promise.allSettled(
        allocations.map(allocation => this.checkTunnelHealth(allocation))
      );

      let healthyCount = 0;
      let unhealthyCount = 0;

      healthResults.forEach((result, index) => {
        if (result.status === 'fulfilled' && result.value) {
          healthyCount++;
        } else {
          unhealthyCount++;
          const allocation = allocations[index];
          console.warn(`Tunnel health check failed for port ${allocation.port} (router: ${allocation.routerId})`);
        }
      });

      console.log(`Health check results: ${healthyCount} healthy, ${unhealthyCount} unhealthy`);
      
    } catch (error) {
      console.error('Error during health checks:', error);
    }
  }

  async checkTunnelHealth(allocation) {
    return new Promise((resolve) => {
      const { port, routerId } = allocation;
      
      // Test if we can connect to the tunnel port
      const timeout = setTimeout(() => {
        resolve(false);
      }, 10000); // 10 second timeout

      try {
        // Use netstat to check if port is listening
        const netstat = spawn('netstat', ['-tuln']);
        let output = '';

        netstat.stdout.on('data', (data) => {
          output += data.toString();
        });

        netstat.on('close', (code) => {
          clearTimeout(timeout);
          
          if (code !== 0) {
            console.warn(`netstat command failed with code ${code}`);
            resolve(false);
            return;
          }

          // Check if our port is listening
          const portPattern = new RegExp(`:${port}\\s`);
          const isListening = portPattern.test(output);
          
          if (isListening) {
            console.log(`Port ${port} is healthy (listening)`);
            resolve(true);
          } else {
            console.warn(`Port ${port} is not listening`);
            resolve(false);
          }
        });

        netstat.on('error', (error) => {
          clearTimeout(timeout);
          console.warn(`netstat command error:`, error.message);
          resolve(false);
        });

      } catch (error) {
        clearTimeout(timeout);
        console.warn(`Health check error for port ${port}:`, error.message);
        resolve(false);
      }
    });
  }

  async testSSHConnection(port) {
    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        resolve(false);
      }, 5000); // 5 second timeout

      try {
        // Test SSH connection to the tunnel
        const ssh = spawn('ssh', [
          '-o', 'ConnectTimeout=5',
          '-o', 'StrictHostKeyChecking=no',
          '-o', 'UserKnownHostsFile=/dev/null',
          '-o', 'LogLevel=ERROR',
          '-p', port.toString(),
          'root@localhost',
          'echo', 'tunnel-test'
        ]);

        let success = false;

        ssh.stdout.on('data', (data) => {
          if (data.toString().trim() === 'tunnel-test') {
            success = true;
          }
        });

        ssh.on('close', (code) => {
          clearTimeout(timeout);
          resolve(success);
        });

        ssh.on('error', (error) => {
          clearTimeout(timeout);
          resolve(false);
        });

      } catch (error) {
        clearTimeout(timeout);
        resolve(false);
      }
    });
  }

  async performCleanup() {
    try {
      console.log('Performing cleanup of inactive allocations...');
      
      const cleanedCount = await this.portManager.cleanupInactiveAllocations();
      
      if (cleanedCount > 0) {
        console.log(`Cleaned up ${cleanedCount} inactive allocations`);
      }

      // Log current stats
      const stats = await this.portManager.getStats();
      console.log('Port allocation stats:', stats);
      
    } catch (error) {
      console.error('Error during cleanup:', error);
    }
  }

  getStatus() {
    return {
      isRunning: this.isRunning,
      checkInterval: this.checkInterval,
      cleanupInterval: this.cleanupInterval,
      lastCheck: this.lastCheckTime,
      lastCleanup: this.lastCleanupTime
    };
  }
}

module.exports = HealthMonitor; 