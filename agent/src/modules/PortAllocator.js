const axios = require('axios');
const { v4: uuidv4 } = require('uuid');
const ConfigManager = require('./ConfigManager');
const logger = require('../utils/Logger');

class PortAllocator {
  constructor() {
    const config = new ConfigManager();
    const cloudVmConfig = config.getCloudVmConfig();
    
    this.cloudVmIp = cloudVmConfig.ip;
    this.cloudApiPort = 8080; // Port for the cloud port management API
    this.portRange = {
      min: cloudVmConfig.portRange.start,
      max: cloudVmConfig.portRange.end
    };
    this.allocatedPort = null;
    this.routerId = null;
    this.heartbeatInterval = null;
  }

  async allocatePort(routerCredentials = null) {
    logger.port('Allocating port from cloud VM');
    
    // Add debug logging for credentials
    if (routerCredentials) {
      logger.port(`Received router credentials for user: ${routerCredentials.username}`);
    } else {
      logger.port('No router credentials provided for port allocation');
    }
    
    try {
      // Generate unique router ID if not exists
      if (!this.routerId) {
        this.routerId = uuidv4();
      }
      
      // Test cloud VM connectivity first
      const isCloudAvailable = await this.testCloudVmConnectivity();
      if (!isCloudAvailable) {
        logger.warn('Cloud VM not available, falling back to local allocation');
        return await this.allocatePortTemporary();
      }

      // Call cloud VM port allocation API
      const port = await this.callCloudVmPortAllocation(routerCredentials);
      this.allocatedPort = port;
      
      // Start heartbeat to maintain allocation
      this.startHeartbeat();
      
      logger.port(`Port ${port} allocated for router ${this.routerId}`);
      
      return port;
    } catch (error) {
      logger.error('Port allocation failed:', error);
      
      // Fallback to temporary allocation if cloud fails
      logger.warn('Falling back to temporary port allocation');
      return await this.allocatePortTemporary();
    }
  }

  async callCloudVmPortAllocation(routerCredentials = null) {
    const requestData = {
      routerId: this.routerId
    };
    
    // Include router credentials if provided
    if (routerCredentials) {
      requestData.routerCredentials = routerCredentials;
      logger.port(`Sending router credentials for user: ${routerCredentials.username} to cloud VM`);
      logger.port(`Request data: ${JSON.stringify({ routerId: this.routerId, routerCredentials: { username: routerCredentials.username, password: '[REDACTED]' } })}`);
    } else {
      logger.port('No router credentials to send to cloud VM');
    }
    
    const response = await this.callCloudVmAPI('POST', '/api/allocate-port', requestData);

    if (!response.success) {
      throw new Error(response.error || 'Port allocation failed');
    }

    logger.port(`Cloud VM port allocation successful: ${JSON.stringify(response.data)}`);
    return response.data.port;
  }

  async allocatePortTemporary() {
    // Fallback implementation when cloud VM is not available
    logger.port('Using temporary port allocation (cloud VM unavailable)');
    
    // Use router ID hash to make port selection more deterministic
    const routerHash = this.routerId ? this.hashString(this.routerId) : Math.random();
    const portOffset = Math.floor(routerHash * (this.portRange.max - this.portRange.min + 1));
    
    // Try ports starting from the hashed position
    for (let i = 0; i < (this.portRange.max - this.portRange.min + 1); i++) {
      const port = this.portRange.min + ((portOffset + i) % (this.portRange.max - this.portRange.min + 1));
      
      try {
        const isAvailable = await this.testPortAvailabilityLocally(port);
        if (isAvailable) {
          logger.port(`Temporary port ${port} allocated for router ${this.routerId}`);
          return port;
        }
      } catch (error) {
        logger.warn(`Port ${port} test failed:`, error.message);
        continue;
      }
    }
    
    throw new Error('No available ports in range 2200-2299');
  }

  hashString(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash) / 2147483647; // Normalize to 0-1
  }

  async testPortAvailabilityLocally(port) {
    // Test if the port is likely available by checking if it's being used
    // This is a simplified test - in production you might want to test actual connectivity
    try {
      // For temporary allocation, we'll use a simple strategy:
      // Avoid common SSH ports and assume most ports in our range are available
      const commonPorts = [22, 80, 443, 8080, 3000, 3030];
      if (commonPorts.includes(port)) {
        return false;
      }

      // Simple availability test - in a real implementation you might test actual binding
      return true;
    } catch (error) {
      return false;
    }
  }

  async testPortAvailability(port) {
    // Legacy method - now calls the improved local test
    return await this.testPortAvailabilityLocally(port);
  }

  async testCloudVmConnectivity() {
    try {
      const response = await axios.get(`http://${this.cloudVmIp}:${this.cloudApiPort}/api/health`, { 
        timeout: 5000
      });
      
      logger.port('Cloud VM connectivity test successful:', response.data);
      return response.data.status === 'healthy';
    } catch (error) {
      logger.warn('Cloud VM connectivity test failed:', error.message);
      return false;
    }
  }

  startHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }

    // Send heartbeat every 5 minutes
    this.heartbeatInterval = setInterval(async () => {
      try {
        await this.sendHeartbeat();
      } catch (error) {
        logger.error('Heartbeat failed:', error.message);
      }
    }, 5 * 60 * 1000); // 5 minutes

    logger.port('Heartbeat started for port', this.allocatedPort);
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
      logger.port('Heartbeat stopped');
    }
  }

  async sendHeartbeat() {
    if (!this.allocatedPort || !this.routerId) {
      logger.warn('No allocated port or router ID for heartbeat');
      return;
    }

    try {
      const response = await this.callCloudVmAPI('POST', `/api/heartbeat/${this.allocatedPort}`, {
        routerId: this.routerId
      });

      if (response.success) {
        logger.port(`Heartbeat sent for port ${this.allocatedPort}`);
      } else {
        logger.warn('Heartbeat failed:', response.error);
      }
    } catch (error) {
      logger.error('Heartbeat error:', error.message);
      throw error;
    }
  }

  async releasePort() {
    if (this.allocatedPort && this.routerId) {
      logger.port(`Releasing port ${this.allocatedPort} for router ${this.routerId}`);
      
      // Stop heartbeat
      this.stopHeartbeat();
      
      try {
        // Call cloud VM API to release port
        const response = await this.callCloudVmAPI('POST', `/api/release-port/${this.allocatedPort}`, { 
          routerId: this.routerId 
        });
        
        if (response.success) {
          logger.port(`Port ${this.allocatedPort} released successfully`);
        } else {
          logger.warn('Port release failed:', response.error);
        }
        
        this.allocatedPort = null;
        this.routerId = null;
        
        return true;
      } catch (error) {
        logger.error('Failed to release port:', error);
        return false;
      }
    }
    
    return true;
  }

  async getPortStatus() {
    if (!this.allocatedPort) {
      return null;
    }

    try {
      const response = await this.callCloudVmAPI('GET', `/api/port-status?port=${this.allocatedPort}`);
      
      if (response.success) {
        return response.data;
      } else {
        logger.warn('Failed to get port status:', response.error);
        return null;
      }
    } catch (error) {
      logger.error('Port status check failed:', error);
      return null;
    }
  }

  async getAllAllocations() {
    try {
      const response = await this.callCloudVmAPI('GET', '/api/admin/allocations');
      
      if (response.success) {
        return response.data;
      } else {
        logger.warn('Failed to get allocations:', response.error);
        return [];
      }
    } catch (error) {
      logger.error('Failed to get allocations:', error);
      return [];
    }
  }

  async callCloudVmAPI(method, endpoint, data = null) {
    const url = `http://${this.cloudVmIp}:${this.cloudApiPort}${endpoint}`;
    
    const config = {
      method,
      url,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
      config.data = data;
    }
    
    try {
      const response = await axios(config);
      return response.data;
    } catch (error) {
      logger.error('Cloud VM API call failed:', error.message);
      
      // If it's a network error, the cloud VM might be down
      if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
        throw new Error('Cloud VM port management service unavailable');
      }
      
      throw new Error(`Cloud VM API error: ${error.message}`);
    }
  }

  getPortInfo() {
    return {
      cloudVmIp: this.cloudVmIp,
      cloudApiPort: this.cloudApiPort,
      allocatedPort: this.allocatedPort,
      routerId: this.routerId,
      portRange: this.portRange,
      hasHeartbeat: !!this.heartbeatInterval
    };
  }

  setCloudVmIp(ip) {
    this.cloudVmIp = ip;
    logger.port(`Cloud VM IP updated to: ${ip}`);
  }

  generateRouterId() {
    this.routerId = uuidv4();
    return this.routerId;
  }

  // Cleanup method to be called when agent shuts down
  async cleanup() {
    this.stopHeartbeat();
    await this.releasePort();
  }
}

module.exports = PortAllocator; 