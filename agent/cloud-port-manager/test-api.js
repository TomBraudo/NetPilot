#!/usr/bin/env node

// Test script for NetPilot Cloud Port Manager API
// This script tests all the API endpoints to ensure they work correctly

const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

// Configuration
const API_BASE_URL = process.env.API_BASE_URL || `http://localhost:${process.env.PORT || 8080}`;

console.log(`Testing NetPilot Cloud Port Manager at: ${API_BASE_URL}`);

class PortManagerAPITest {
  constructor(baseUrl = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.testRouterId = uuidv4();
    this.allocatedPort = null;
  }

  async log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const colors = {
      info: '\x1b[34m[INFO]\x1b[0m',
      success: '\x1b[32m[SUCCESS]\x1b[0m',
      error: '\x1b[31m[ERROR]\x1b[0m',
      warning: '\x1b[33m[WARNING]\x1b[0m'
    };
    console.log(`${colors[type]} ${timestamp} ${message}`);
  }

  async makeRequest(method, endpoint, data = null) {
    try {
      const config = {
        method,
        url: `${this.baseUrl}${endpoint}`,
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 10000
      };

      if (data && (method === 'POST' || method === 'PUT')) {
        config.data = data;
      }

      const response = await axios(config);
      return response.data;
    } catch (error) {
      if (error.response) {
        throw new Error(`HTTP ${error.response.status}: ${error.response.statusText}`);
      } else {
        throw new Error(`Network error: ${error.message}`);
      }
    }
  }

  async testHealthCheck() {
    await this.log('Testing health check endpoint...');
    
    try {
      const response = await this.makeRequest('GET', '/api/health');
      
      if (response.status === 'healthy') {
        await this.log('Health check passed ✓', 'success');
        return true;
      } else {
        await this.log(`Health check failed: ${JSON.stringify(response)}`, 'error');
        return false;
      }
    } catch (error) {
      await this.log(`Health check failed: ${error.message}`, 'error');
      return false;
    }
  }

  async testPortAllocation() {
    await this.log(`Testing port allocation for router ${this.testRouterId}...`);
    
    try {
      const response = await this.makeRequest('POST', '/api/allocate-port', {
        routerId: this.testRouterId
      });
      
      if (response.success && response.data.port) {
        this.allocatedPort = response.data.port;
        await this.log(`Port ${this.allocatedPort} allocated successfully ✓`, 'success');
        return true;
      } else {
        await this.log(`Port allocation failed: ${JSON.stringify(response)}`, 'error');
        return false;
      }
    } catch (error) {
      await this.log(`Port allocation failed: ${error.message}`, 'error');
      return false;
    }
  }

  async testPortStatus() {
    if (!this.allocatedPort) {
      await this.log('No allocated port to check status', 'warning');
      return false;
    }

    await this.log(`Testing port status for port ${this.allocatedPort}...`);
    
    try {
      const response = await this.makeRequest('GET', `/api/port-status?port=${this.allocatedPort}`);
      
      if (response.success && response.data.port === this.allocatedPort) {
        await this.log(`Port status check passed ✓`, 'success');
        await this.log(`  Port: ${response.data.port}`, 'info');
        await this.log(`  Router ID: ${response.data.routerId}`, 'info');
        await this.log(`  Status: ${response.data.status}`, 'info');
        return true;
      } else {
        await this.log(`Port status check failed: ${JSON.stringify(response)}`, 'error');
        return false;
      }
    } catch (error) {
      await this.log(`Port status check failed: ${error.message}`, 'error');
      return false;
    }
  }

  async testHeartbeat() {
    if (!this.allocatedPort) {
      await this.log('No allocated port for heartbeat test', 'warning');
      return false;
    }

    await this.log(`Testing heartbeat for port ${this.allocatedPort}...`);
    
    try {
      const response = await this.makeRequest('POST', `/api/heartbeat/${this.allocatedPort}`, {
        routerId: this.testRouterId
      });
      
      if (response.success) {
        await this.log(`Heartbeat sent successfully ✓`, 'success');
        return true;
      } else {
        await this.log(`Heartbeat failed: ${JSON.stringify(response)}`, 'error');
        return false;
      }
    } catch (error) {
      await this.log(`Heartbeat failed: ${error.message}`, 'error');
      return false;
    }
  }

  async testGetAllAllocations() {
    await this.log('Testing get all allocations...');
    
    try {
      const response = await this.makeRequest('GET', '/api/admin/allocations');
      
      if (response.success && Array.isArray(response.data)) {
        await this.log(`Retrieved ${response.data.length} allocations ✓`, 'success');
        
        // Check if our allocation is in the list
        const ourAllocation = response.data.find(alloc => alloc.routerId === this.testRouterId);
        if (ourAllocation) {
          await this.log(`Our allocation found in list ✓`, 'success');
        } else {
          await this.log(`Our allocation not found in list`, 'warning');
        }
        
        return true;
      } else {
        await this.log(`Get allocations failed: ${JSON.stringify(response)}`, 'error');
        return false;
      }
    } catch (error) {
      await this.log(`Get allocations failed: ${error.message}`, 'error');
      return false;
    }
  }

  async testPortRelease() {
    if (!this.allocatedPort) {
      await this.log('No allocated port to release', 'warning');
      return false;
    }

    await this.log(`Testing port release for port ${this.allocatedPort}...`);
    
    try {
      const response = await this.makeRequest('POST', `/api/release-port/${this.allocatedPort}`, {
        routerId: this.testRouterId
      });
      
      if (response.success) {
        await this.log(`Port ${this.allocatedPort} released successfully ✓`, 'success');
        return true;
      } else {
        await this.log(`Port release failed: ${JSON.stringify(response)}`, 'error');
        return false;
      }
    } catch (error) {
      await this.log(`Port release failed: ${error.message}`, 'error');
      return false;
    }
  }

  async testDuplicateAllocation() {
    await this.log('Testing duplicate allocation prevention...');
    
    // First, allocate a port
    const firstResponse = await this.makeRequest('POST', '/api/allocate-port', {
      routerId: this.testRouterId
    });
    
    if (!firstResponse.success) {
      await this.log('Failed to allocate port for duplicate test', 'error');
      return false;
    }
    
    const firstPort = firstResponse.data.port;
    await this.log(`First allocation: port ${firstPort}`);
    
    // Try to allocate again with same router ID
    const secondResponse = await this.makeRequest('POST', '/api/allocate-port', {
      routerId: this.testRouterId
    });
    
    if (secondResponse.success && secondResponse.data.port === firstPort) {
      await this.log('Duplicate allocation handled correctly ✓', 'success');
      this.allocatedPort = firstPort; // Keep track for cleanup
      return true;
    } else {
      await this.log('Duplicate allocation not handled correctly', 'error');
      return false;
    }
  }

  async runAllTests() {
    await this.log('Starting NetPilot Cloud Port Manager API Tests', 'info');
    await this.log('=' .repeat(60), 'info');
    
    const tests = [
      { name: 'Health Check', fn: () => this.testHealthCheck() },
      { name: 'Port Allocation', fn: () => this.testPortAllocation() },
      { name: 'Port Status', fn: () => this.testPortStatus() },
      { name: 'Heartbeat', fn: () => this.testHeartbeat() },
      { name: 'Get All Allocations', fn: () => this.testGetAllAllocations() },
      { name: 'Port Release', fn: () => this.testPortRelease() },
      { name: 'Duplicate Allocation', fn: () => this.testDuplicateAllocation() }
    ];
    
    let passed = 0;
    let failed = 0;
    
    for (const test of tests) {
      await this.log(`\nRunning test: ${test.name}`, 'info');
      await this.log('-'.repeat(40), 'info');
      
      try {
        const result = await test.fn();
        if (result) {
          passed++;
        } else {
          failed++;
        }
      } catch (error) {
        await this.log(`Test ${test.name} threw error: ${error.message}`, 'error');
        failed++;
      }
      
      // Small delay between tests
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    // Cleanup
    if (this.allocatedPort) {
      await this.log('\nCleaning up...', 'info');
      try {
        await this.testPortRelease();
      } catch (error) {
        await this.log(`Cleanup failed: ${error.message}`, 'warning');
      }
    }
    
    // Final results
    await this.log('\n' + '='.repeat(60), 'info');
    await this.log('TEST RESULTS:', 'info');
    await this.log(`Passed: ${passed}`, passed > 0 ? 'success' : 'info');
    await this.log(`Failed: ${failed}`, failed > 0 ? 'error' : 'info');
    await this.log(`Total: ${passed + failed}`, 'info');
    
    if (failed === 0) {
      await this.log('\nAll tests passed! 🎉', 'success');
      return true;
    } else {
      await this.log(`\n${failed} test(s) failed. Please check the logs above.`, 'error');
      return false;
    }
  }
}

// Main execution
async function main() {
  const args = process.argv.slice(2);
  let baseUrl = API_BASE_URL;
  
  // Allow custom base URL
  if (args.length > 0) {
    baseUrl = args[0];
  }
  
  console.log(`Testing NetPilot Cloud Port Manager at: ${baseUrl}`);
  
  const tester = new PortManagerAPITest(baseUrl);
  const success = await tester.runAllTests();
  
  process.exit(success ? 0 : 1);
}

// Run if called directly
if (require.main === module) {
  main().catch(error => {
    console.error('Test runner failed:', error);
    process.exit(1);
  });
}

module.exports = PortManagerAPITest; 