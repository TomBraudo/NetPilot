#!/usr/bin/env node

const RouterManager = require('./src/modules/RouterManager');
const TunnelManager = require('./src/modules/TunnelManager');

async function testFixesValidation() {
  console.log('🔧 Testing Fixes Validation');
  console.log('='.repeat(40));
  
  const credentials = {
    host: '192.168.1.1',
    username: 'root',
    password: 'YOUR_ROUTER_PASSWORD_HERE',
    port: 22
  };

  let routerManager, tunnelManager;
  
  try {
    console.log('\n📋 Test 1: Cloud VM Configuration from .env');
    console.log('-'.repeat(40));
    
    tunnelManager = new TunnelManager();
    console.log('✅ Cloud VM config loaded:');
    console.log(`   - IP: ${tunnelManager.cloudVmIp}`);
    console.log(`   - User: ${tunnelManager.cloudUser}`);
    console.log(`   - Port: ${tunnelManager.cloudPort}`);
    console.log(`   - Password: ${tunnelManager.cloudPassword ? '***SET***' : 'NOT SET'}`);
    
    console.log('\n📋 Test 2: Package Detection Improvements');
    console.log('-'.repeat(40));
    
    routerManager = new RouterManager();
    await routerManager.ssh.connect({
      host: credentials.host,
      username: credentials.username,
      password: credentials.password,
      port: credentials.port || 22,
      readyTimeout: 10000
    });
    routerManager.isConnected = true;
    
    // Test the improved package detection
    const packagesToTest = ['iptables', 'tc', 'openssh-client', 'autossh'];
    
    for (const pkg of packagesToTest) {
      const isInstalled = await routerManager.checkPackageInstalled(pkg);
      console.log(`   ${pkg}: ${isInstalled ? '✅ FOUND' : '❌ NOT FOUND'}`);
    }
    
    console.log('\n📋 Test 3: Package Installation (Dry Run)');
    console.log('-'.repeat(40));
    
    // Test that packages already detected as installed won't be reinstalled
    console.log('Checking if packages would be reinstalled...');
    
    // Get installed package list to check detection
    const listResult = await routerManager.ssh.execCommand('opkg list-installed');
    const installedPackages = listResult.stdout;
    
    console.log('Installed package variants found:');
    const variants = ['iptables-nft', 'tc-bpf', 'openssh-client', 'autossh'];
    for (const variant of variants) {
      const pattern = new RegExp(`^${variant}\\s`);
      if (pattern.test(installedPackages)) {
        console.log(`   ✅ ${variant}`);
      }
    }
    
    console.log('\n✅ Fixes validation completed successfully');
    
  } catch (error) {
    console.error('\n❌ Fixes validation failed:', error.message);
    throw error;
    
  } finally {
    if (routerManager) {
      await routerManager.disconnect();
      console.log('🔧 Router disconnected');
    }
  }
}

// Run the test
testFixesValidation().catch(error => {
  console.error('Test failed:', error);
  process.exit(1);
}); 