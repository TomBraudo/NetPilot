#!/usr/bin/env node

const RouterManager = require('./src/modules/RouterManager');
const TunnelManager = require('./src/modules/TunnelManager');
const PortAllocator = require('./src/modules/PortAllocator');

async function testComprehensiveFixes() {
  console.log('🔧 Testing Comprehensive Fixes for NetPilot Agent');
  console.log('='.repeat(50));
  
  // Test credentials
  const credentials = {
    host: '192.168.1.1',
    username: 'root',
    password: 'YOUR_ROUTER_PASSWORD_HERE',
    port: 22
  };

  let routerManager, tunnelManager, portAllocator;
  
  try {
    // Initialize managers (they will load config from .env automatically)
    routerManager = new RouterManager();
    tunnelManager = new TunnelManager();
    portAllocator = new PortAllocator();
    
    console.log('\n📋 Test 1: Package Installation with Proper Detection');
    console.log('-'.repeat(50));
    
    // Test improved package installation
    const packageResult = await routerManager.installPackages(credentials);
    console.log('✅ Package installation result:', {
      success: packageResult.success,
      packagesInstalled: packageResult.packagesInstalled,
      installed: packageResult.installResults.length,
      warnings: packageResult.warnings.length
    });
    
    if (!packageResult.packagesInstalled) {
      console.log('✅ No packages were installed - service restart was skipped (as expected)');
    } else {
      console.log('ℹ️  Packages were installed - services were restarted');
    }
    
    console.log('\n📋 Test 2: Port Allocation');
    console.log('-'.repeat(50));
    
    // Test port allocation (PortAllocator generates its own router ID)
    const allocatedPort = await portAllocator.allocatePort();
    const portInfo = portAllocator.getPortInfo();
    console.log('✅ Port allocation result:', {
      port: allocatedPort,
      routerId: portInfo.routerId,
      cloudVmIp: portInfo.cloudVmIp
    });
    
    console.log('\n📋 Test 3: Enhanced Tunnel Establishment');
    console.log('-'.repeat(50));
    
    try {
      // Test tunnel establishment with enhanced error handling
      await tunnelManager.establishTunnel(credentials, allocatedPort);
      console.log('✅ Tunnel establishment completed successfully');
      
      // Get detailed tunnel status
      const status = await tunnelManager.getTunnelStatus();
      console.log('📊 Tunnel status:', {
        isActive: status.isActive,
        port: status.port,
        hasLogs: status.lastLogs && status.lastLogs.length > 0,
        hasInitService: status.hasInitService
      });
      
      if (!status.isActive) {
        console.log('⚠️  Tunnel is not active. Recent logs:');
        if (status.lastLogs) {
          status.lastLogs.slice(-5).forEach(log => {
            if (log.trim()) console.log(`   ${log}`);
          });
        }
      }
      
    } catch (tunnelError) {
      console.error('❌ Tunnel establishment failed:', tunnelError.message);
      
      // Try to get debug information
      try {
        const status = await tunnelManager.getTunnelStatus();
        console.log('🔍 Debug information:');
        console.log('   - Tunnel logs:', status.lastLogs ? status.lastLogs.slice(-3) : 'No logs');
        console.log('   - Service status:', status.serviceStatus || 'Unknown');
      } catch (debugError) {
        console.log('🔍 Could not retrieve debug information:', debugError.message);
      }
    }
    
    console.log('\n📋 Test 4: Cloud VM Connectivity');
    console.log('-'.repeat(50));
    
    try {
      const cloudTest = await tunnelManager.testCloudVmConnectivity();
      console.log('✅ Cloud VM connectivity test:', cloudTest);
    } catch (cloudError) {
      console.error('❌ Cloud VM connectivity failed:', cloudError.message);
    }
    
    console.log('\n📋 Test 5: Router Information Gathering');
    console.log('-'.repeat(50));
    
    try {
      const routerInfo = await routerManager.getRouterInfo();
      console.log('✅ Router information:', routerInfo);
    } catch (infoError) {
      console.error('❌ Failed to get router info:', infoError.message);
    }
    
    console.log('\n📋 Test 6: NetPilot Compatibility Check');
    console.log('-'.repeat(50));
    
    try {
      const compatibility = await routerManager.verifyNetPilotCompatibility();
      console.log('✅ Compatibility check result:', {
        overall: compatibility.overall,
        packagesOk: Object.values(compatibility.packages).every(v => v),
        servicesOk: Object.values(compatibility.services).every(v => v),
        configOk: Object.values(compatibility.configuration).every(v => v)
      });
    } catch (compatError) {
      console.error('❌ Compatibility check failed:', compatError.message);
    }
    
    console.log('\n🔧 Cleanup');
    console.log('-'.repeat(50));
    
    // Cleanup
    try {
      await tunnelManager.cleanup();
      console.log('✅ Tunnel manager cleaned up');
    } catch (cleanupError) {
      console.log('⚠️  Cleanup warning:', cleanupError.message);
    }
    
    try {
      await routerManager.disconnect();
      console.log('✅ Router manager disconnected');
    } catch (disconnectError) {
      console.log('⚠️  Disconnect warning:', disconnectError.message);
    }
    
    // Release port (no parameters needed)
    try {
      await portAllocator.releasePort();
      console.log('✅ Port released');
    } catch (releaseError) {
      console.log('⚠️  Port release warning:', releaseError.message);
    }
    
    console.log('\n✅ Comprehensive test completed');
    console.log('='.repeat(50));
    
  } catch (error) {
    console.error('\n❌ Test failed:', error);
    console.error('Stack trace:', error.stack);
    
    // Attempt cleanup even on failure
    try {
      if (tunnelManager) await tunnelManager.cleanup();
      if (routerManager) await routerManager.disconnect();
      if (portAllocator) await portAllocator.cleanup();
    } catch (cleanupError) {
      console.error('Cleanup after failure also failed:', cleanupError.message);
    }
    
    process.exit(1);
  }
}

// Handle process termination gracefully
process.on('SIGINT', () => {
  console.log('\n🛑 Test interrupted by user');
  process.exit(0);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

// Run the test
testComprehensiveFixes().catch(error => {
  console.error('Test runner failed:', error);
  process.exit(1);
}); 