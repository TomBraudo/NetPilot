const path = require('path');
const fs = require('fs');
const logger = require('../utils/Logger');
const dotenv = require('dotenv');
const { app } = require('electron');

class ConfigManager {
    constructor(app) {
        if (!app) {
            throw new Error('ConfigManager requires an Electron app instance.');
        }

        try {
            // Attempt to load .env from several possible locations
            const candidatePaths = [];

            // 0. Portable executable directory (electron-builder portable mode)
            if (process.env.PORTABLE_EXECUTABLE_DIR) {
                candidatePaths.push(path.join(process.env.PORTABLE_EXECUTABLE_DIR, '.env'));
            }

            // Packaged app path (most important) - .env next to .exe
            if (app.isPackaged) {
                candidatePaths.push(path.join(path.dirname(app.getPath('exe')), '.env'));
            }

            // 1. External .env next to executable / cwd
            candidatePaths.push(path.join(process.cwd(), '.env'));
            
            // 2. User data directory (writable per-user location)
            candidatePaths.push(path.join(app.getPath('userData'), '.env'));

            // 3. Bundled .env beside this file (development time)
            candidatePaths.push(path.join(__dirname, '../../.env'));

            let envLoaded = false;
            for (const p of candidatePaths) {
                if (fs.existsSync(p)) {
                    dotenv.config({ path: p });
                    logger.config(`[ENV] .env loaded from ${p}`);
                    envLoaded = true;
                    break;
                }
            }

            if (!envLoaded) {
                // Not fatal – we'll fall back to defaults and warn
                logger.warn('[ENV]', '.env file not found; using built-in defaults');
            }
            
            this.config = {
                cloudVmIp: process.env.CLOUD_VM_IP || 'localhost',
                cloudUser: process.env.CLOUD_VM_USER || 'netpilot-agent',
                cloudPassword: process.env.CLOUD_VM_PASSWORD || '',
                autosshCleanupToken: process.env.AUTOSSH_CLEANUP_TOKEN || '',
                portRange: {
                    start: parseInt(process.env.PORT_RANGE_START) || 2200,
                    end: parseInt(process.env.PORT_RANGE_END) || 2299
                },
                router: {
                    defaultUser: 'root',
                    defaultIp: '192.168.1.1',
                    defaultPassword: null
                },
                app: {
                    name: 'NetPilot Router Agent',
                    version: '1.0.0',
                    statusPort: 3030
                }
            };

            this.validateConfig();
            this.configLoaded = true;

            const tokenFound = !!this.config.autosshCleanupToken;
            logger.info('[MAIN] [ENV]', `AUTOSSH_CLEANUP_TOKEN loaded: ${tokenFound ? 'FOUND' : 'NOT FOUND'}`);
            
        } catch (error) {
            logger.error(`[MAIN] [ENV] Configuration loading failed: ${error.message}`);
            // Exit gracefully if config fails
            return false;
        }
    }

    validateConfig() {
        if (!this.config?.cloudVmIp) {
            throw new Error('Cloud VM IP is required');
        }

        if (!this.config?.cloudUser) {
            throw new Error('Cloud VM user is required');
        }

        if (!this.config?.cloudPassword) {
            logger.warn('[ENV]', 'CLOUD_VM_PASSWORD is not set; using blank password');
        }

        if (this.config.portRange.start >= this.config.portRange.end) {
            throw new Error('Invalid port range configuration');
        }

        // Only log configuration once when first validated
        if (!this.configLogged) {
            this.logConfig();
            this.configLogged = true;
        }
    }

    logConfig() {
        const { cloudUser, cloudVmIp } = this.config;
        const portRange = `${this.config.portRange.start}-${this.config.portRange.end}`;
        logger.config(`NetPilot Agent: ${cloudUser}@${cloudVmIp} (ports: ${portRange})`);
    }

    getConfig() {
        return this.config;
    }

    getCloudVmConfig() {
        return this.config?.cloudVmIp ? {
            ip: this.config.cloudVmIp,
            user: this.config.cloudUser,
            password: this.config.cloudPassword,
            portRange: this.config.portRange
        } : null;
    }

    getRouterConfig() {
        return this.config?.router || null;
    }

    getAppConfig() {
        return this.config?.app || null;
    }

    // Generic get method for accessing config values with dot notation or aliases
    get(key) {
        return this.config[key];
    }

    updateCloudVmConfig(updates) {
        if (!this.config) {
            throw new Error('Configuration not loaded');
        }

        this.config.cloudVmIp = updates.ip || this.config.cloudVmIp;
        this.config.cloudUser = updates.user || this.config.cloudUser;
        this.config.cloudPassword = updates.password || this.config.cloudPassword;
        this.config.portRange = { ...this.config.portRange, ...updates.portRange };
        logger.config(`Cloud VM configuration updated: ${this.config.cloudUser}@${this.config.cloudVmIp}`);
        return this.config;
    }

    getLogsPath() {
        return path.join(__dirname, '../../logs');
    }

    resetToDefaults() {
        try {
            logger.config('Resetting configuration to defaults...');
            
            // Load defaults from env.example
            const exampleEnvPath = path.join(__dirname, '../../env.example');
            let defaultConfig = {};
            
            if (fs.existsSync(exampleEnvPath)) {
                // Read from env.example for defaults
                const exampleEnv = dotenv.parse(fs.readFileSync(exampleEnvPath));
                
                defaultConfig = {
                    cloudVmIp: exampleEnv.CLOUD_VM_IP || 'localhost',
                    cloudUser: exampleEnv.CLOUD_VM_USER || 'netpilot-agent',
                    cloudPassword: this.config.cloudPassword, // PRESERVE existing password
                    autosshCleanupToken: this.config.autosshCleanupToken, // PRESERVE existing token
                    portRange: {
                        start: parseInt(exampleEnv.PORT_RANGE_START) || 2200,
                        end: parseInt(exampleEnv.PORT_RANGE_END) || 2299
                    }
                };
            } else {
                // Hardcoded defaults if env.example doesn't exist
                defaultConfig = {
                    cloudVmIp: '34.38.207.87',
                    cloudUser: 'netpilot-agent',
                    cloudPassword: this.config.cloudPassword, // PRESERVE existing password
                    autosshCleanupToken: this.config.autosshCleanupToken, // PRESERVE existing token
                    portRange: {
                        start: 2200,
                        end: 2299
                    }
                };
            }
            
            // Keep router and app configs intact
            defaultConfig.router = this.config.router;
            defaultConfig.app = this.config.app;
            
            // Apply defaults to memory only - DO NOT OVERWRITE .env FILE
            this.config = defaultConfig;
            
            logger.config('Configuration reset to defaults (in memory only - .env file preserved)');
            return true;
        } catch (error) {
            logger.error('Failed to reset configuration:', error);
            return false;
        }
    }
}

module.exports = ConfigManager; 