const { ipcRenderer } = require('electron');
const logger = require('../utils/Logger');
const fs = require('fs');
const path = require('path');
const os = require('os');

class StateManager {
    constructor() {
        if (StateManager.instance) {
            return StateManager.instance;
        }

        // Check if we're in the main process or renderer process
        this.isMainProcess = !ipcRenderer;
        
        // Set up file-based storage path
        this.stateDir = path.join(os.homedir(), 'AppData', 'Roaming', 'netpilot-router-agent', 'netpilot-state');
        this.ensureStateDirExists();
        
        StateManager.instance = this;
    }

    // Ensure the netpilot-state directory exists
    ensureStateDirExists() {
        try {
            if (!fs.existsSync(this.stateDir)) {
                fs.mkdirSync(this.stateDir, { recursive: true });
                logger.info(`Created state directory: ${this.stateDir}`);
            }
        } catch (error) {
            logger.error('Failed to create state directory:', error);
        }
    }

    // File-based storage methods
    async saveStateToFile(filename, data) {
        try {
            const filePath = path.join(this.stateDir, `${filename}.json`);
            fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
            logger.info(`State saved to file: ${filePath}`);
            return true;
        } catch (error) {
            logger.error(`Failed to save state to file ${filename}:`, error);
            return false;
        }
    }

    async loadStateFromFile(filename) {
        try {
            const filePath = path.join(this.stateDir, `${filename}.json`);
            if (!fs.existsSync(filePath)) {
                logger.info(`State file ${filename}.json does not exist, returning null`);
                return null;
            }

            const data = fs.readFileSync(filePath, 'utf8');
            const parsed = JSON.parse(data);
            logger.info(`State loaded from file: ${filePath}`);
            return parsed;
        } catch (error) {
            logger.error(`Failed to load state from file ${filename}:`, error);
            return null;
        }
    }

    async deleteStateFile(filename) {
        try {
            const filePath = path.join(this.stateDir, `${filename}.json`);
            if (fs.existsSync(filePath)) {
                fs.unlinkSync(filePath);
                logger.info(`State file deleted: ${filePath}`);
            }
            return true;
        } catch (error) {
            logger.error(`Failed to delete state file ${filename}:`, error);
            return false;
        }
    }

    // localStorage-based state management for Electron renderer process
    async saveState(filename, data) {
        try {
            if (this.isMainProcess) {
                // In main process, use IPC to save to renderer's localStorage
                const { BrowserWindow } = require('electron');
                const mainWindow = BrowserWindow.getFocusedWindow() || BrowserWindow.getAllWindows()[0];
                if (mainWindow) {
                    await mainWindow.webContents.executeJavaScript(`
                        localStorage.setItem('netpilot_${filename}', '${JSON.stringify(data).replace(/'/g, "\\'")}');
                    `);
                }
            } else {
                // In renderer process, use localStorage directly
                localStorage.setItem(`netpilot_${filename}`, JSON.stringify(data));
            }
            
            logger.info(`State saved to localStorage ${filename}`);
            return true;
        } catch (error) {
            logger.error(`Failed to save state to localStorage ${filename}:`, error);
            return false;
        }
    }

    async loadState(filename) {
        try {
            let dataStr = null;
            
            if (this.isMainProcess) {
                // In main process, use IPC to read from renderer's localStorage
                const { BrowserWindow } = require('electron');
                const mainWindow = BrowserWindow.getFocusedWindow() || BrowserWindow.getAllWindows()[0];
                if (mainWindow) {
                    dataStr = await mainWindow.webContents.executeJavaScript(`
                        localStorage.getItem('netpilot_${filename}');
                    `);
                }
            } else {
                // In renderer process, use localStorage directly
                dataStr = localStorage.getItem(`netpilot_${filename}`);
            }

            if (!dataStr) {
                logger.info(`State file ${filename} does not exist in localStorage, returning null`);
                return null;
            }

            const parsed = JSON.parse(dataStr);
            logger.info(`State loaded from localStorage ${filename}`);
            return parsed;
        } catch (error) {
            logger.error(`Failed to load state from localStorage ${filename}:`, error);
            return null;
        }
    }

    async deleteState(filename) {
        try {
            if (this.isMainProcess) {
                // In main process, use IPC to delete from renderer's localStorage
                const { BrowserWindow } = require('electron');
                const mainWindow = BrowserWindow.getFocusedWindow() || BrowserWindow.getAllWindows()[0];
                if (mainWindow) {
                    await mainWindow.webContents.executeJavaScript(`
                        localStorage.removeItem('netpilot_${filename}');
                    `);
                }
            } else {
                // In renderer process, use localStorage directly
                localStorage.removeItem(`netpilot_${filename}`);
            }
            
            logger.info(`State file deleted from localStorage: ${filename}`);
            return true;
        } catch (error) {
            logger.error(`Failed to delete state file from localStorage ${filename}:`, error);
            return false;
        }
    }

    // Tunnel State Management - now using file-based storage for reliability
    async saveTunnelState(tunnelState) {
        const stateData = {
            activeTunnel: tunnelState,
            lastUpdated: new Date().toISOString(),
            version: '1.0'
        };
        
        // Save to both file and localStorage for redundancy
        const fileSuccess = await this.saveStateToFile('tunnel-state', stateData);
        const localStorageSuccess = await this.saveState('tunnelState', stateData);
        
        if (fileSuccess) {
            logger.info('Tunnel state saved to file successfully (includes PIDs for cleanup)');
        }
        
        return fileSuccess || localStorageSuccess; // Success if either works
    }

    async getTunnelState() {
        // Try file-based storage first (more reliable), then fall back to localStorage
        let data = await this.loadStateFromFile('tunnel-state');
        if (!data) {
            data = await this.loadState('tunnelState');
        }
        return data ? data.activeTunnel : null;
    }

    async clearTunnelState() {
        // Clear from both file and localStorage
        const fileSuccess = await this.deleteStateFile('tunnel-state');
        const localStorageSuccess = await this.deleteState('tunnelState');
        
        return fileSuccess || localStorageSuccess; // Success if either works
    }

    // Port Allocation Management - now using file-based storage for reliability
    async savePortAllocation(portData) {
        // Try to load existing allocations from file first, then localStorage
        let existingAllocations = await this.loadStateFromFile('port-allocations');
        if (!existingAllocations) {
            existingAllocations = await this.loadState('portAllocations') || { allocations: [] };
        }
        if (!existingAllocations.allocations) {
            existingAllocations = { allocations: [] };
        }
        
        // Remove any existing allocation for the same router ID
        existingAllocations.allocations = existingAllocations.allocations.filter(
            allocation => allocation.routerId !== portData.routerId
        );
        
        // Add the new allocation
        existingAllocations.allocations.push({
            ...portData,
            allocated: new Date().toISOString()
        });
        
        existingAllocations.lastUpdated = new Date().toISOString();
        existingAllocations.version = '1.0';
        
        // Save to both file and localStorage for redundancy
        const fileSuccess = await this.saveStateToFile('port-allocations', existingAllocations);
        const localStorageSuccess = await this.saveState('portAllocations', existingAllocations);
        
        return fileSuccess || localStorageSuccess; // Success if either works
    }

    async getPortAllocations() {
        // Try file-based storage first, then fall back to localStorage
        let data = await this.loadStateFromFile('port-allocations');
        if (!data) {
            data = await this.loadState('portAllocations');
        }
        return data ? data.allocations : [];
    }

    async removePortAllocation(routerId) {
        // Try to load existing allocations from file first, then localStorage
        let existingAllocations = await this.loadStateFromFile('port-allocations');
        if (!existingAllocations) {
            existingAllocations = await this.loadState('portAllocations') || { allocations: [] };
        }
        if (!existingAllocations.allocations) {
            existingAllocations = { allocations: [] };
        }
        
        existingAllocations.allocations = existingAllocations.allocations.filter(
            allocation => allocation.routerId !== routerId
        );
        
        existingAllocations.lastUpdated = new Date().toISOString();
        
        // Save to both file and localStorage
        const fileSuccess = await this.saveStateToFile('port-allocations', existingAllocations);
        const localStorageSuccess = await this.saveState('portAllocations', existingAllocations);
        
        return fileSuccess || localStorageSuccess; // Success if either works
    }

    // Router Connection History
    async saveRouterConnection(connectionData) {
        const existingConnections = await this.loadState('routerConnections') || { connections: [] };
        
        // Add the new connection to the beginning of the array
        existingConnections.connections.unshift({
            ...connectionData,
            timestamp: new Date().toISOString()
        });
        
        // Keep only the last 50 connections
        existingConnections.connections = existingConnections.connections.slice(0, 50);
        
        existingConnections.lastUpdated = new Date().toISOString();
        existingConnections.version = '1.0';
        
        return await this.saveState('routerConnections', existingConnections);
    }

    async getRouterConnections() {
        const data = await this.loadState('routerConnections');
        return data ? data.connections : [];
    }

    async getLastSuccessfulConnection() {
        const connections = await this.getRouterConnections();
        return connections.find(conn => conn.success === true) || null;
    }

    // Utility methods
    async clearAllState() {
        logger.info('Clearing all state from both files and localStorage...');
        const results = await Promise.allSettled([
            this.clearTunnelState(), // Already clears both file and localStorage
            this.deleteStateFile('port-allocations'),
            this.deleteState('portAllocations'),
            this.deleteState('routerConnections')
        ]);
        
        const success = results.every(result => result.status === 'fulfilled' && result.value);
        logger.info('All state cleared:', success ? 'success' : 'partial failure');
        return success;
    }

    async getStateInfo() {
        const tunnelState = await this.getTunnelState();
        const portAllocations = await this.getPortAllocations();
        const routerConnections = await this.getRouterConnections();
        
        // Check file-based storage
        const tunnelStateFile = await this.loadStateFromFile('tunnel-state');
        const portAllocationsFile = await this.loadStateFromFile('port-allocations');
        
        return {
            hasTunnelState: !!tunnelState,
            tunnelStateHasPIDs: !!(tunnelState && tunnelState.processIds),
            portAllocationsCount: portAllocations.length,
            routerConnectionsCount: routerConnections.length,
            lastConnection: routerConnections[0] || null,
            fileStorage: {
                hasTunnelStateFile: !!tunnelStateFile,
                hasPortAllocationsFile: !!portAllocationsFile,
                stateDirectory: this.stateDir
            }
        };
    }

    // Reset singleton instance (for testing)
    static reset() {
        StateManager.instance = null;
    }
}

module.exports = StateManager;
