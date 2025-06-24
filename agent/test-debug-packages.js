#!/usr/bin/env node

const RouterManager = require('./src/modules/RouterManager');

async function debugPackageDetection() {
  console.log('🔍 Debug Package Detection');
  console.log('='.repeat(40));
  
  const credentials = {
    host: '192.168.1.1',
    username: 'root',
    password: 'YOUR_ROUTER_PASSWORD_HERE',
    port: 22
  };

  let routerManager;
  
  try {
    routerManager = new RouterManager();
    await routerManager.ssh.connect({
      host: credentials.host,
      username: credentials.username,
      password: credentials.password,
      port: credentials.port || 22,
      readyTimeout: 10000
    });
    routerManager.isConnected = true;
    
    // Get raw package list
    const listResult = await routerManager.ssh.execCommand('opkg list-installed');
    const installedPackages = listResult.stdout;
    
    console.log('\n📋 Raw Package List (first few lines):');
    console.log(installedPackages.split('\n').slice(0, 10).join('\n'));
    
    console.log('\n📋 Looking for specific packages:');
    const targetPackages = ['iptables-nft', 'tc-bpf', 'openssh-client', 'autossh'];
    
    for (const pkg of targetPackages) {
      const pattern = new RegExp(`^${pkg.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s+`);
      const found = pattern.test(installedPackages);
      console.log(`   ${pkg}: ${found ? '✅' : '❌'} (pattern: ${pattern})`);
      
      if (found) {
        const match = installedPackages.match(pattern);
        console.log(`     Match: "${match ? match[0] : 'none'}"`);
      }
    }
    
    console.log('\n📋 Testing the checkPackageInstalled method:');
    const packagesToTest = ['iptables', 'tc', 'openssh-client', 'autossh'];
    
    for (const pkg of packagesToTest) {
      const isInstalled = await routerManager.checkPackageInstalled(pkg);
      console.log(`   ${pkg}: ${isInstalled ? '✅ FOUND' : '❌ NOT FOUND'}`);
    }
    
    console.log('\n📋 Manual string search:');
    for (const pkg of targetPackages) {
      const found = installedPackages.includes(pkg);
      console.log(`   ${pkg}: ${found ? '✅' : '❌'} (simple includes)`);
    }
    
  } catch (error) {
    console.error('Debug failed:', error.message);
    throw error;
    
  } finally {
    if (routerManager) {
      await routerManager.disconnect();
    }
  }
}

// Run the debug
debugPackageDetection().catch(error => {
  console.error('Debug failed:', error);
  process.exit(1);
}); 