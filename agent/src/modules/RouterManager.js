const { NodeSSH } = require('node-ssh');
const path = require('path');
const fs = require('fs');
const logger = require('../utils/Logger');

class RouterManager {
  constructor(configManager) {
    this.ssh = new NodeSSH();
    this.isConnected = false;
    this.currentConnection = null;
    this.configManager = configManager;
  }

  async testConnection(credentials) {
    if (!credentials || !credentials.host || !credentials.username || !credentials.password) {
      throw new Error('Invalid credentials: host, username, and password are required');
    }

    logger.router(`Testing connection to ${credentials.host}`);
    
    try {
      await this.ssh.connect({
        host: credentials.host,
        username: credentials.username,
        password: credentials.password,
        port: credentials.port || 22,
        readyTimeout: 30000
      });

      this.isConnected = true;
      
      // Test basic command execution
      const result = await this.ssh.execCommand('echo "connection_test"');
      
      if (result.stdout.includes('connection_test')) {
        return {
          success: true,
          message: 'Connection successful',
          host: credentials.host
        };
      } else {
        throw new Error('Command execution test failed');
      }
    } catch (error) {
      this.isConnected = false;
      throw new Error(`Connection failed: ${error.message}`);
    } finally {
      // Keep connection open for further operations if successful
    }
  }

  async installPackages(credentials) {
    logger.router(`Installing packages on router... ${credentials.host}`);
    
    try {
      // Connect to router
      await this.ssh.connect({
        host: credentials.host,
        username: credentials.username,
        password: credentials.password,
        port: credentials.port || 22,
        readyTimeout: 30000
      });

      this.isConnected = true;
      this.currentConnection = credentials;

      // Define MINIMAL required packages (updated for nft-qos and AGH installer support)
      const packages = [
        // CRITICAL for tunnel establishment
        'openssh-client',    // SSH client for reverse tunnels
        'autossh',           // Persistent SSH tunnels
        'sshpass',           // Password authentication for SSH tunnels
        'coreutils-nohup',   // Proper process detachment for autossh

        // Networking/tools used by agent and scripts
        'ip-full',           // Provides full ip/arp tooling
        'curl',              // Needed by AGH installer/verification scripts

        // Bandwidth monitoring (CLI only)
        'nlbwmon',           // Per-device bandwidth monitoring

        // New QoS method (CLI only)
        'nft-qos'            // nftables-based QoS (no LuCI app)
      ];

      // Update package lists
      logger.router('Updating package lists...');
      await this.executeCommand('opkg update');

      // Install packages one by one, checking if they exist first
      const installResults = [];
      let packagesInstalled = false;
      
      for (const pkg of packages) {
        try {
          // Check if package is already installed (use non-throwing command)
          logger.router(`Checking for ${pkg}...`);
          const isInstalled = await this.checkPackageInstalled(pkg);

          if (isInstalled) {
            logger.router(`${pkg} is already installed`);
            installResults.push({ package: pkg, success: true, message: 'Already installed' });
            continue; // Move to the next package
          }

          // If not installed, proceed with installation
          logger.router(`Installing ${pkg}...`);
          const installResult = await this.executeCommand(`opkg install ${pkg}`);
          installResults.push({ package: pkg, success: true, output: installResult.stdout });
          logger.router(`${pkg} installed successfully`);
          packagesInstalled = true; // Mark that we actually installed something

        } catch (error) {
          logger.warn(`Failed to install ${pkg}:`, error.message);
          installResults.push({ package: pkg, success: false, error: error.message });
        }
      }

      // Verify critical packages are installed
      logger.router('Verifying critical packages...');
      const criticalPackages = ['openssh-client', 'autossh', 'coreutils-nohup', 'nlbwmon', 'nft-qos', 'curl'];
      for (const pkg of criticalPackages) {
        const isInstalled = await this.checkPackageInstalled(pkg);
        if (!isInstalled) {
          throw new Error(`Critical package ${pkg} failed to install`);
        }
      }

      // Configure router for NetPilot functionality
      logger.router('Configuring router for NetPilot...');
      await this.configureRouterForNetPilot();

      // Only restart services if packages were actually installed
      if (packagesInstalled) {
        logger.router('Restarting services (packages were installed)...');
        await this.executeCommand('/etc/init.d/network restart');
        await this.executeCommand('/etc/init.d/firewall restart');
        
        // Restart nlbwmon if it was installed
        try {
          await this.executeCommand('/etc/init.d/nlbwmon restart');
          logger.router('nlbwmon service restarted');
        } catch (error) {
          logger.warn('nlbwmon restart failed (might not be installed yet):', error.message);
        }
        
        // Check if WiFi exists before restarting
        try {
          await this.executeCommand('wifi reload');
        } catch (error) {
          logger.warn('WiFi reload failed (might not have wireless):', error.message);
        }
      } else {
        logger.router('Skipping service restart (no packages were installed)');
      }

      return {
        success: true,
        message: 'Packages installed successfully',
        packagesInstalled: packagesInstalled,
        installResults: installResults.filter(r => r.success),
        warnings: installResults.filter(r => !r.success)
      };

    } catch (error) {
      logger.error('Package installation failed:', error);
      await this.disconnect();
      throw new Error(`Package installation failed: ${error.message}`);
    }
  }

  async checkPackageInstalled(packageName) {
    try {
      // Get list of installed packages
      const listResult = await this.ssh.execCommand('opkg list-installed');
      
      if (!listResult.stdout) {
        return false;
      }
      
      const installedPackages = listResult.stdout;
      
      // Define package aliases/variants
      const packageVariants = {
        'iptables': ['iptables', 'iptables-nft'],
        'tc': ['tc', 'tc-bpf'],
        'openssh-client': ['openssh-client'],
        // Add other variants as needed
      };
      
      // Get the list of possible package names to check
      const possibleNames = packageVariants[packageName] || [packageName];
      
      // Check if any variant is installed
      for (const variant of possibleNames) {
        // Use a more flexible pattern - check if the variant name appears at the start of any line
        const pattern = new RegExp(`^${variant.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s+`, 'm');
        if (pattern.test(installedPackages)) {
          logger.router(`   Found variant: ${variant}`);
          return true;
        }
      }
      
      return false;
    } catch (error) {
      logger.warn(`Error checking package ${packageName}:`, error.message);
      return false;
    }
  }

  async configureRouterForNetPilot() {
    logger.router('Configuring router for NetPilot functionality...');
    
    try {
      // Ensure SSH service is enabled and configured
      logger.router('Configuring SSH service...');
      await this.executeCommand('/etc/init.d/dropbear enable');
      await this.executeCommand('/etc/init.d/dropbear start');
      await this.executeCommand('uci set dropbear.@dropbear[0].PasswordAuth="1"');
      await this.executeCommand('uci set dropbear.@dropbear[0].Port="22"');
      await this.executeCommand('uci commit dropbear');
      logger.router('Dropbear SSH service enabled and started.');

      // Configure firewall defaults (retain permissive defaults as before)
      logger.router('Configuring firewall defaults...');
      await this.executeCommand('uci set firewall.@defaults[0].input="ACCEPT"');
      await this.executeCommand('uci set firewall.@defaults[0].output="ACCEPT"');
      await this.executeCommand('uci set firewall.@defaults[0].forward="ACCEPT"');
      await this.executeCommand('uci commit firewall');

      // Ensure essential services are enabled
      logger.router('Enabling essential services...');
      await this.executeCommand('/etc/init.d/network enable');
      await this.executeCommand('/etc/init.d/firewall enable');
      await this.executeCommand('/etc/init.d/dnsmasq enable');

      // Create NetPilot directory for scripts and configuration
      logger.router('Creating NetPilot directories...');
      await this.executeCommand('mkdir -p /root/netpilot');
      await this.executeCommand('mkdir -p /tmp/netpilot');

      // Verify pkill is available for process management
      logger.router('Verifying process management tools...');
      try {
        const pkillCheck = await this.executeCommand('which pkill || echo "not_found"');
        if (pkillCheck.stdout.includes('not_found')) {
          logger.router('WARNING: pkill not available - will use BusyBox alternatives');
        } else {
          logger.router('pkill available for enhanced process management');
        }
      } catch (error) {
        logger.router('Process management check failed - will use BusyBox alternatives');
      }

        // Configure nlbwmon for 30-day bandwidth monitoring (router preparation only)
        logger.router('Configuring nlbwmon for 30-day bandwidth retention...');
        try {
          // Set kernel buffer sizes for nlbwmon (multiple approaches)
          await this.executeCommand('echo "net.core.rmem_max = 1048576" >> /etc/sysctl.conf');
          await this.executeCommand('echo "net.core.rmem_default = 524288" >> /etc/sysctl.conf');
          await this.executeCommand('echo "net.core.netdev_max_backlog = 5000" >> /etc/sysctl.conf');
          await this.executeCommand('sysctl -p');
          
          // Clear any existing nlbwmon configuration to avoid conflicts
          await this.executeCommand('uci del nlbwmon.@nlbwmon[0].local_network 2>/dev/null || true');
          
          // Set nlbwmon configuration for 30-day retention (ready for NetPilot app queries)
          await this.executeCommand('uci set nlbwmon.@nlbwmon[0].database_directory="/tmp/nlbwmon"');
          await this.executeCommand('uci set nlbwmon.@nlbwmon[0].database_generations="35"'); // 35 days for safety margin
          await this.executeCommand('uci set nlbwmon.@nlbwmon[0].commit_interval="24h"'); // Daily commits for day-level queries
          await this.executeCommand('uci set nlbwmon.@nlbwmon[0].refresh_interval="30s"'); // Real-time updates for "today"
          await this.executeCommand('uci set nlbwmon.@nlbwmon[0].database_limit="50000"'); // Increased for 30-day retention
          await this.executeCommand('uci set nlbwmon.@nlbwmon[0].netlink_buffer_size="524288"');
          
          // Configure database_interval for daily midnight resets (accounting periods)
          const today = new Date().toISOString().split('T')[0]; // Format: YYYY-MM-DD
          await this.executeCommand(`uci set nlbwmon.@nlbwmon[0].database_interval="${today}/1"`); // Reset daily at midnight
          
          // Set local networks for home OpenWrt networks (192.168.1.x range only)
          await this.executeCommand('uci add_list nlbwmon.@nlbwmon[0].local_network="192.168.1.0/24"');
          await this.executeCommand('uci add_list nlbwmon.@nlbwmon[0].local_network="lan"');
          await this.executeCommand('uci commit nlbwmon');
          
          // Create persistent storage directory (survives reboots if possible)
          await this.executeCommand('mkdir -p /etc/nlbwmon_backup');
          
          // Enable and start nlbwmon service
          await this.executeCommand('/etc/init.d/nlbwmon enable');
          await this.executeCommand('/etc/init.d/nlbwmon start');
          logger.router('nlbwmon configured for 30-day retention - ready for NetPilot app queries');
        } catch (error) {
          logger.warn('nlbwmon configuration failed:', error.message);
          // Don't fail the entire process for nlbwmon configuration issues
        }      logger.router('Router configuration for NetPilot completed successfully');
      
    } catch (error) {
      logger.warn('Some router configuration steps failed:', error.message);
      // Don't fail the entire process for configuration warnings
    }
  }

  async verifyNetPilotCompatibility() {
    logger.router('Verifying NetPilot compatibility...');
    
    const compatibilityResults = {
      packages: {},
      services: {},
      configuration: {},
      overall: true
    };

    try {
      // Check critical packages (updated to nft-qos and no LuCI GUI)
      const criticalPackages = [
        'openssh-client',   // SSH client for reverse tunnels
        'autossh',          // Persistent SSH tunnels  
        'sshpass',          // Password authentication
        'coreutils-nohup',  // Process detachment
        'ip-full',          // Provides 'arp' command
        'nlbwmon',          // Per-device bandwidth monitoring
        'nft-qos',          // nftables-based QoS
        'curl'              // For AGH installer validation/API checks
      ];
      for (const pkg of criticalPackages) {
        try {
          compatibilityResults.packages[pkg] = await this.checkPackageInstalled(pkg);
          if (!compatibilityResults.packages[pkg]) {
            compatibilityResults.overall = false;
          }
        } catch (error) {
          compatibilityResults.packages[pkg] = false;
          compatibilityResults.overall = false;
        }
      }

      // Check essential services
      const services = ['dropbear', 'network', 'firewall'];
      for (const service of services) {
        try {
          const result = await this.executeCommand(`/etc/init.d/${service} enabled && echo "enabled" || echo "disabled"`);
          compatibilityResults.services[service] = result.stdout.includes('enabled');
        } catch (error) {
          compatibilityResults.services[service] = false;
        }
      }

      // Check UCI configuration access
      try {
        await this.executeCommand('uci show system.@system[0].hostname');
        compatibilityResults.configuration.uci = true;
      } catch (error) {
        compatibilityResults.configuration.uci = false;
        compatibilityResults.overall = false;
      }

      // Check network interface access
      try {
        await this.executeCommand('ip link show');
        compatibilityResults.configuration.network = true;
      } catch (error) {
        compatibilityResults.configuration.network = false;
        compatibilityResults.overall = false;
      }

      logger.router('NetPilot compatibility check completed:', compatibilityResults);
      return compatibilityResults;

    } catch (error) {
      logger.error('NetPilot compatibility check failed:', error);
      return {
        packages: {},
        services: {},
        configuration: {},
        overall: false,
        error: error.message
      };
    }
  }

  /**
   * Copy the AdGuard Home installer script to the router and ensure AGH is installed and configured.
   * If verification fails, run the script with FORCE=1 and re-verify.
   */
  async ensureAdGuardHome(credentials) {
    logger.router('Ensuring AdGuard Home is installed and configured...');
    try {
      // Ensure connection
      if (!this.isConnected) {
        await this.ssh.connect({
          host: credentials.host,
          username: credentials.username,
          password: credentials.password,
          port: credentials.port || 22,
          readyTimeout: 30000
        });
        this.isConnected = true;
      }

      // Copy installer script
      await this.copyInstallScriptToRouter();

      // Verify current AGH setup
      let status = await this.verifyAdGuardHomeStatus();
      const allOk = status.processRunning && status.logsAndStatsDisabled && status.guiBoundLocal && status.port53Listening && status.dnsWorking;

      if (!allOk) {
        logger.router('AdGuard Home not in desired state, running installer with FORCE=1...');
        await this.executeCommand('FORCE=1 sh /root/netpilot_install_agh.sh');

        // Give service a moment to settle
        await new Promise(r => setTimeout(r, 3000));

        // Re-verify
        status = await this.verifyAdGuardHomeStatus();
      }

      return {
        success: status.processRunning && status.logsAndStatsDisabled && status.guiBoundLocal && status.port53Listening && status.dnsWorking,
        status
      };

    } catch (error) {
      logger.error('Failed to ensure AdGuard Home:', error);
      throw new Error(`AdGuard Home ensure failed: ${error.message}`);
    }
  }

  async copyInstallScriptToRouter() {
    // Resolve installer path both in dev and packaged modes
    // 1) Packaged portable exe: script is copied to resources under portable EXE dir
    //    Use process.resourcesPath if available; otherwise, fall back to relative paths.
    const candidatePaths = [];
    if (process.resourcesPath) {
      candidatePaths.push(path.join(process.resourcesPath, 'scripts', 'install.sh'));
    }
    candidatePaths.push(path.join(__dirname, '../../scripts/install.sh'));
    candidatePaths.push(path.join(process.cwd(), 'scripts', 'install.sh'));

    let localPath = null;
    for (const p of candidatePaths) {
      try { if (fs.existsSync(p)) { localPath = p; break; } } catch (_) {}
    }
    if (!localPath) {
      throw new Error('Could not locate install.sh in packaged resources or project scripts directory');
    }
    const remotePath = '/root/netpilot_install_agh.sh';

    logger.router(`Copying installer to router: ${remotePath}`);
    await this.ssh.putFile(localPath, remotePath);
    await this.executeCommand(`chmod +x ${remotePath}`);
  }

  async verifyAdGuardHomeStatus() {
    logger.router('Verifying AdGuard Home status on router...');
    const checks = {
      processRunning: false,
      logsAndStatsDisabled: false,
      guiBoundLocal: false,
      port53Listening: false,
      dnsWorking: false
    };

    // Detect service name
    const svc = await this.ssh.execCommand('[ -x /etc/init.d/AdGuardHome ] && echo "/etc/init.d/AdGuardHome" || ([ -x /etc/init.d/adguardhome ] && echo "/etc/init.d/adguardhome" || echo "")');
    const servicePath = (svc.stdout || '').trim();

    // 1) Process running
    const proc = await this.ssh.execCommand('pgrep -fa AdGuardHome 2>/dev/null || true');
    let running = !!proc.stdout.trim();
    if (!running && servicePath) {
      const st = await this.ssh.execCommand(`${servicePath} status 2>/dev/null || true`);
      running = /running/i.test(st.stdout || '');
    }
    checks.processRunning = running;

    // 2) querylogs/statistics off, GUI off (bind 127.0.0.1:3000)
    const cfgPath = '/opt/AdGuardHome/AdGuardHome.yaml';
    const cfg = await this.ssh.execCommand(`[ -f ${cfgPath} ] && cat ${cfgPath} || echo ''`);
    const yaml = cfg.stdout || '';
    checks.logsAndStatsDisabled = /\bquerylog:\b[\s\S]*?\benabled:\s*false/i.test(yaml) && /\bstatistics:\b[\s\S]*?\benabled:\s*false/i.test(yaml);
    checks.guiBoundLocal = /\bhttp:\b[\s\S]*?\baddress:\s*127\.0\.0\.1:3000/i.test(yaml);

    // 3) port 53 listening
    const port53 = await this.ssh.execCommand('command -v ss >/dev/null 2>&1 && ss -lntu | grep -E ":53[[:space:]]" || netstat -lntu 2>/dev/null | grep -E ":53[[:space:]]" || true');
    checks.port53Listening = !!port53.stdout.trim();

    // 4) DNS working
    let dns = await this.ssh.execCommand('command -v nslookup >/dev/null 2>&1 && nslookup openwrt.org 127.0.0.1 >/dev/null 2>&1 && echo ok || echo no');
    if (!/ok/.test(dns.stdout || '')) {
      // Fallback: ping which relies on resolver if nslookup missing
      dns = await this.ssh.execCommand('ping -c 1 -W 3 openwrt.org >/dev/null 2>&1 && echo ok || echo fail');
    }
    checks.dnsWorking = /ok/.test(dns.stdout || '');

    logger.router(`AGH status: ${JSON.stringify(checks)}`);
    return checks;
  }

  async getRouterInfo(sshConnection = null) {
    const ssh = sshConnection || this.ssh;
    
    try {
      const results = await Promise.allSettled([
        ssh.execCommand('uci get system.@system[0].hostname 2>/dev/null || echo "unknown"'),
        ssh.execCommand('uci get network.lan.ipaddr 2>/dev/null || echo "unknown"'),
        ssh.execCommand('cat /proc/version | head -1'),
        ssh.execCommand('uptime'),
        ssh.execCommand('free | grep Mem | awk \'{print $3"/"$2}\'')
      ]);

      return {
        hostname: results[0].status === 'fulfilled' ? results[0].value.stdout.trim() : 'unknown',
        lanIp: results[1].status === 'fulfilled' ? results[1].value.stdout.trim() : 'unknown',
        version: results[2].status === 'fulfilled' ? results[2].value.stdout.trim() : 'unknown',
        uptime: results[3].status === 'fulfilled' ? results[3].value.stdout.trim() : 'unknown',
        memory: results[4].status === 'fulfilled' ? results[4].value.stdout.trim() : 'unknown'
      };
    } catch (error) {
      logger.warn('Failed to get router info:', error);
      return {
        hostname: 'unknown',
        lanIp: 'unknown',
        version: 'unknown',
        uptime: 'unknown',
        memory: 'unknown'
      };
    }
  }

  async getRouterMacAddress(credentials) {
    logger.router(`Getting MAC address from ${credentials.host}`);
    const ssh = new NodeSSH();
    try {
      await ssh.connect({
        host: credentials.host,
        username: credentials.username,
        password: credentials.password,
        port: credentials.port || 22,
        readyTimeout: 20000
      });

      // Command to get MAC address from the main LAN bridge interface
      const result = await ssh.execCommand('cat /sys/class/net/br-lan/address');
      
      if (result.stderr) {
        // Fallback for devices that might not have br-lan (e.g., eth0)
        logger.warn(`Could not get MAC from br-lan, trying eth0. Error: ${result.stderr}`);
        const fallbackResult = await ssh.execCommand('cat /sys/class/net/eth0/address');
        if (fallbackResult.stderr) {
            throw new Error(`Failed to get MAC address from br-lan and eth0: ${fallbackResult.stderr}`);
        }
        return fallbackResult.stdout.trim();
      }

      return result.stdout.trim();
    } catch (error) {
      logger.error(`Failed to get MAC address: ${error.message}`);
      throw error;
    } finally {
      if (ssh.isConnected()) {
        ssh.dispose();
      }
    }
  }

  async executeCommand(command) {
    if (!this.isConnected) {
      throw new Error('Not connected to router');
    }

    logger.router(`Executing: ${command}`);
    const result = await this.ssh.execCommand(command);
    
    if (result.code !== 0 && result.stderr) {
      logger.error(`Command failed: ${command}`);
      logger.error(`Error: ${result.stderr}`);
      throw new Error(result.stderr || `Command failed with code ${result.code}`);
    }

    return result;
  }

  async disconnect() {
    if (this.isConnected && this.ssh) {
      await this.ssh.dispose();
      this.isConnected = false;
      this.currentConnection = null;
      logger.router('Disconnected from router');
    }
  }

  async uninstallNetPilot(credentials) {
    logger.router(`Uninstalling NetPilot from router... ${credentials.host}`);
    
    try {
      // Connect to router
      await this.ssh.connect({
        host: credentials.host,
        username: credentials.username,
        password: credentials.password,
        port: credentials.port || 22,
        readyTimeout: 30000
      });

      this.isConnected = true;
      logger.router('Connected to router for uninstallation');

      const uninstallSteps = [];

      // Step 1: Stop tunnel service
      try {
        await this.executeCommand('/etc/init.d/netpilot_tunnel stop 2>/dev/null || true');
        await this.executeCommand('/etc/init.d/netpilot_tunnel disable 2>/dev/null || true');
        uninstallSteps.push({ step: 'Stop tunnel service', success: true });
      } catch (error) {
        uninstallSteps.push({ step: 'Stop tunnel service', success: false, error: error.message });
      }

      // Step 2: Kill any running tunnel processes (BusyBox compatible)
      try {
        await this.executeCommand('ps | grep "netpilot_tunnel" | grep -v grep | awk \'{print $1}\' | xargs -r kill 2>/dev/null || true');
        await this.executeCommand('ps | grep "autossh.*netpilot-agent" | grep -v grep | awk \'{print $1}\' | xargs -r kill 2>/dev/null || true');
        uninstallSteps.push({ step: 'Kill tunnel processes', success: true });
      } catch (error) {
        uninstallSteps.push({ step: 'Kill tunnel processes', success: false, error: error.message });
      }

      // Step 3: Remove init.d service
      try {
        await this.executeCommand('rm -f /etc/init.d/netpilot_tunnel');
        uninstallSteps.push({ step: 'Remove init.d service', success: true });
      } catch (error) {
        uninstallSteps.push({ step: 'Remove init.d service', success: false, error: error.message });
      }

      // Step 4: Remove NetPilot directory and files
      try {
        await this.executeCommand('rm -rf /root/netpilot');
        await this.executeCommand('rm -f /root/netpilot_tunnel.sh');
        await this.executeCommand('rm -f /tmp/netpilot_tunnel.log');
        uninstallSteps.push({ step: 'Remove NetPilot files', success: true });
      } catch (error) {
        uninstallSteps.push({ step: 'Remove NetPilot files', success: false, error: error.message });
      }

      // Step 5: Clean up nlbwmon data and configuration
      try {
        await this.executeCommand('/etc/init.d/nlbwmon stop 2>/dev/null || true');
        await this.executeCommand('rm -rf /tmp/nlbwmon 2>/dev/null || true');
        await this.executeCommand('rm -rf /var/lib/nlbwmon 2>/dev/null || true');
        uninstallSteps.push({ step: 'Clean nlbwmon data', success: true });
      } catch (error) {
        uninstallSteps.push({ step: 'Clean nlbwmon data', success: false, error: error.message });
      }

      // Step 6: Remove SSH keys if they exist
      try {
        await this.executeCommand('rm -f /root/.ssh/netpilot_rsa*');
        uninstallSteps.push({ step: 'Remove SSH keys', success: true });
      } catch (error) {
        uninstallSteps.push({ step: 'Remove SSH keys', success: false, error: error.message });
      }

      // Step 7: Clean up any netpilot-related cron jobs
      try {
        await this.executeCommand('crontab -l 2>/dev/null | grep -v netpilot | crontab - 2>/dev/null || true');
        uninstallSteps.push({ step: 'Clean cron jobs', success: true });
      } catch (error) {
        uninstallSteps.push({ step: 'Clean cron jobs', success: false, error: error.message });
      }

      await this.disconnect();

      const successCount = uninstallSteps.filter(step => step.success).length;
      const totalSteps = uninstallSteps.length;

      logger.router(`NetPilot uninstallation completed: ${successCount}/${totalSteps} steps successful`);

      return {
        success: true,
        message: `NetPilot uninstalled successfully (${successCount}/${totalSteps} steps completed)`,
        steps: uninstallSteps,
        warnings: uninstallSteps.filter(step => !step.success)
      };

    } catch (error) {
      logger.error('NetPilot uninstallation failed:', error);
      await this.disconnect();
      throw new Error(`NetPilot uninstallation failed: ${error.message}`);
    }
  }

  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      connection: this.currentConnection
    };
  }

  async enableWifi(credentials) {
    logger.router(`Attempting to enable WiFi on router... ${credentials.host}`);
    const testSSH = new NodeSSH();
    
    try {
      await testSSH.connect({
        host: credentials.host,
        username: credentials.username,
        password: credentials.password,
        port: credentials.port || 22,
        readyTimeout: 10000,
      });

      logger.router('Checking current WiFi status...');
      
      // Get comprehensive WiFi information
      const [disabledStatus, interfaceInfo, ssidInfo, channelInfo] = await Promise.allSettled([
        testSSH.execCommand('uci get wireless.@wifi-device[0].disabled 2>/dev/null || echo "1"'),
        testSSH.execCommand('uci get wireless.@wifi-device[0].hwmode 2>/dev/null || echo "unknown"'),
        testSSH.execCommand('uci get wireless.@wifi-iface[0].ssid 2>/dev/null || echo "OpenWrt"'),
        testSSH.execCommand('uci get wireless.radio0.channel 2>/dev/null || echo "auto"')
      ]);
      
      const isDisabled = disabledStatus.status === 'fulfilled' ? disabledStatus.value.stdout.trim() === '1' : true;
      const hwMode = interfaceInfo.status === 'fulfilled' ? interfaceInfo.value.stdout.trim() : 'unknown';
      const ssid = ssidInfo.status === 'fulfilled' ? ssidInfo.value.stdout.trim() : 'OpenWrt';
      const channel = channelInfo.status === 'fulfilled' ? channelInfo.value.stdout.trim() : 'auto';
      
      const wifiStatus = {
        isEnabled: !isDisabled,
        ssid: ssid,
        hwMode: hwMode,
        channel: channel,
        interfaceCount: 1
      };
      
      if (!isDisabled) {
        logger.router('WiFi is already enabled.');
        return { 
          success: true, 
          message: `WiFi is already enabled. SSID: ${ssid}`,
          status: wifiStatus
        };
      }

      logger.router('WiFi is disabled, enabling it now...');
      await testSSH.execCommand("uci set wireless.@wifi-device[0].disabled='0'");
      await testSSH.execCommand("uci set wireless.@wifi-iface[0].disabled='0'");
      await testSSH.execCommand('uci commit wireless');
      await testSSH.execCommand('wifi reload');
      
      logger.router('WiFi enabled. Waiting for it to initialize...');
      await new Promise(resolve => setTimeout(resolve, 3000)); // Wait for wifi to come up

      // Update status after enabling
      wifiStatus.isEnabled = true;
      
      return { 
        success: true, 
        message: `WiFi enabled successfully! SSID: ${ssid}`,
        status: wifiStatus
      };
    } catch (error) {
      logger.error('Failed to enable WiFi:', error);
      throw new Error(`Failed to enable WiFi: ${error.message}`);
    } finally {
      if (testSSH.isConnected) {
        await testSSH.dispose();
      }
    }
  }

  async getWifiStatus(credentials) {
    if (!this.ssh || !this.isConnected) {
      throw new Error('Not connected to router');
    }

    logger.router(`Getting WiFi status from ${credentials.host}`);

    const testSSH = new NodeSSH();
    
    try {
      await testSSH.connect({
        host: credentials.host,
        username: credentials.username,
        password: credentials.password,
        port: credentials.port || 22,
        readyTimeout: 10000,
      });

      // Get comprehensive WiFi information
      const [disabledStatus, interfaceInfo, ssidInfo, channelInfo, encryptionInfo] = await Promise.allSettled([
        testSSH.execCommand('uci get wireless.@wifi-device[0].disabled 2>/dev/null || echo "1"'),
        testSSH.execCommand('uci get wireless.@wifi-device[0].hwmode 2>/dev/null || echo "unknown"'),
        testSSH.execCommand('uci get wireless.@wifi-iface[0].ssid 2>/dev/null || echo "OpenWrt"'),
        testSSH.execCommand('uci get wireless.radio0.channel 2>/dev/null || echo "auto"'),
        testSSH.execCommand('uci get wireless.@wifi-iface[0].encryption 2>/dev/null || echo "none"')
      ]);
      
      const isDisabled = disabledStatus.status === 'fulfilled' ? disabledStatus.value.stdout.trim() === '1' : true;
      const hwMode = interfaceInfo.status === 'fulfilled' ? interfaceInfo.value.stdout.trim() : 'unknown';
      const ssid = ssidInfo.status === 'fulfilled' ? ssidInfo.value.stdout.trim() : 'OpenWrt';
      const channel = channelInfo.status === 'fulfilled' ? channelInfo.value.stdout.trim() : 'auto';
      const encryption = encryptionInfo.status === 'fulfilled' ? encryptionInfo.value.stdout.trim() : 'none';
      
      return {
        success: true,
        status: {
          isEnabled: !isDisabled,
          ssid: ssid,
          hwMode: hwMode,
          channel: channel,
          encryption: encryption,
          interfaceCount: 1
        }
      };
    } catch (error) {
      logger.error('Failed to get WiFi status:', error);
      return {
        success: false,
        error: error.message
      };
    } finally {
      if (testSSH.isConnected) {
        await testSSH.dispose();
      }
    }
  }
}

module.exports = RouterManager; 