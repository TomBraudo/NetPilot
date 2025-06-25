const { ipcRenderer } = require('electron');
const logger = require('../utils/Logger');

class StateManager {
    constructor() {
        if (StateManager.instance) {
            return StateManager.instance;
        }

        // Check if we're in the main process or renderer process
        this.isMainProcess = !ipcRenderer;
        
        StateManager.instance = this;
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

    // Tunnel State Management
    async saveTunnelState(tunnelState) {
        const stateData = {
            activeTunnel: tunnelState,
            lastUpdated: new Date().toISOString(),
            version: '1.0'
        };
        return await this.saveState('tunnelState', stateData);
    }

    async getTunnelState() {
        const data = await this.loadState('tunnelState');
        return data ? data.activeTunnel : null;
    }

    async clearTunnelState() {
        return await this.deleteState('tunnelState');
    }

    // Port Allocation Management
    async savePortAllocation(portData) {
        const existingAllocations = await this.loadState('portAllocations') || { allocations: [] };
        
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
        
        return await this.saveState('portAllocations', existingAllocations);
    }

    async getPortAllocations() {
        const data = await this.loadState('portAllocations');
        return data ? data.allocations : [];
    }

    async removePortAllocation(routerId) {
        const existingAllocations = await this.loadState('portAllocations') || { allocations: [] };
        
        existingAllocations.allocations = existingAllocations.allocations.filter(
            allocation => allocation.routerId !== routerId
        );
        
        existingAllocations.lastUpdated = new Date().toISOString();
        
        return await this.saveState('portAllocations', existingAllocations);
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
        logger.info('Clearing all state from localStorage...');
        const results = await Promise.allSettled([
            this.clearTunnelState(),
            this.deleteState('portAllocations'),
            this.deleteState('routerConnections')
        ]);
        
        const success = results.every(result => result.status === 'fulfilled' && result.value);
        logger.info('All state cleared from localStorage:', success ? 'success' : 'partial failure');
        return success;
    }

    async getStateInfo() {
        const tunnelState = await this.getTunnelState();
        const portAllocations = await this.getPortAllocations();
        const routerConnections = await this.getRouterConnections();
        
        return {
            hasTunnelState: !!tunnelState,
            portAllocationsCount: portAllocations.length,
            routerConnectionsCount: routerConnections.length,
            lastConnection: routerConnections[0] || null
        };
    }

    // Reset singleton instance (for testing)
    static reset() {
        StateManager.instance = null;
    }
}

module.exports = StateManager;
