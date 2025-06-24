const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');

class PortManager {
  constructor() {
    this.dbPath = process.env.DB_PATH || path.join(__dirname, '../data/ports.db');
    this.db = null;
    
    // Port configuration
    this.portRange = {
      min: 2200,
      max: 2299
    };
    
    // Timeout configuration (in milliseconds)
    this.inactivityTimeout = 24 * 60 * 60 * 1000; // 24 hours
  }

  async initialize() {
    return new Promise((resolve, reject) => {
      try {
        // Ensure data directory exists
        const dataDir = path.dirname(this.dbPath);
        if (!fs.existsSync(dataDir)) {
          console.log(`Creating data directory: ${dataDir}`);
          fs.mkdirSync(dataDir, { recursive: true });
        }
        
        console.log(`Connecting to database: ${this.dbPath}`);
        this.db = new sqlite3.Database(this.dbPath, (err) => {
          if (err) {
            console.error('Database connection failed:', err);
            reject(err);
            return;
          }
          
          console.log('Connected to port management database');
          this.createTables().then(resolve).catch(reject);
        });
      } catch (error) {
        console.error('Database initialization error:', error);
        reject(error);
      }
    });
  }

  async createTables() {
    const sql = `
      CREATE TABLE IF NOT EXISTS port_allocations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        port INTEGER NOT NULL UNIQUE,
        router_id TEXT NOT NULL,
        router_username TEXT,
        router_password TEXT,
        allocated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_heartbeat DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active',
        metadata TEXT
      );
      
      CREATE INDEX IF NOT EXISTS idx_router_id ON port_allocations(router_id);
      CREATE INDEX IF NOT EXISTS idx_port ON port_allocations(port);
      CREATE INDEX IF NOT EXISTS idx_status ON port_allocations(status);
    `;

    return new Promise((resolve, reject) => {
      this.db.exec(sql, (err) => {
        if (err) {
          console.error('Failed to create tables:', err);
          reject(err);
        } else {
          console.log('Database tables initialized');
          resolve();
        }
      });
    });
  }

  async allocatePort(routerId, routerCredentials = null) {
    try {
      // Check if router already has a port allocated
      const existingAllocation = await this.getAllocationByRouterId(routerId);
      if (existingAllocation) {
        console.log(`Router ${routerId} already has port ${existingAllocation.port} allocated`);
        // Update credentials if provided
        if (routerCredentials) {
          await this.updateRouterCredentials(existingAllocation.port, routerCredentials);
          existingAllocation.routerUsername = routerCredentials.username;
          existingAllocation.routerPassword = routerCredentials.password;
        }
        return existingAllocation;
      }

      // Use atomic allocation to prevent race conditions
      const allocation = await this.atomicAllocatePort(routerId, routerCredentials);
      console.log(`Port ${allocation.port} allocated to router ${routerId}`);
      
      return allocation;
    } catch (error) {
      console.error('Port allocation failed:', error);
      throw error;
    }
  }

  async atomicAllocatePort(routerId, routerCredentials = null, retryCount = 0) {
    const maxRetries = 5;
    const self = this;
    
    return new Promise((resolve, reject) => {
      // Simple approach: try each port sequentially with INSERT OR IGNORE
      let currentPort = self.portRange.min;
      
      function tryNextPort() {
        if (currentPort > self.portRange.max) {
          reject(new Error('No available ports in range 2200-2299'));
          return;
        }
        
        const insertSql = `
          INSERT OR IGNORE INTO port_allocations (port, router_id, router_username, router_password, metadata, allocated_at, last_heartbeat, status)
          VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'active')
        `;
        
        const username = routerCredentials?.username || null;
        const password = routerCredentials?.password || null;
        
        self.db.run(insertSql, [currentPort, routerId, username, password, JSON.stringify({})], function(err) {
          if (err) {
            if (err.code === 'SQLITE_CONSTRAINT' && retryCount < maxRetries) {
              console.log(`Port allocation collision detected, retrying... (attempt ${retryCount + 1}/${maxRetries})`);
              setTimeout(() => {
                self.atomicAllocatePort(routerId, routerCredentials, retryCount + 1)
                  .then(resolve)
                  .catch(reject);
              }, 100 + (retryCount * 50));
              return;
            }
            reject(err);
            return;
          }
          
          if (this.changes > 0) {
            // Successfully inserted
            resolve({
              id: this.lastID,
              port: currentPort,
              routerId: routerId,
              routerUsername: username,
              routerPassword: password,
              allocatedAt: new Date().toISOString(),
              lastHeartbeat: new Date().toISOString(),
              status: 'active',
              metadata: {}
            });
          } else {
            // Port already taken, try next one
            currentPort++;
            setImmediate(tryNextPort);
          }
        });
      }
      
      tryNextPort();
    });
  }

  async releasePort(port, routerId) {
    return new Promise((resolve, reject) => {
      const sql = `
        UPDATE port_allocations 
        SET status = 'released', last_heartbeat = CURRENT_TIMESTAMP
        WHERE port = ? AND router_id = ? AND status = 'active'
      `;

      this.db.run(sql, [port, routerId], function(err) {
        if (err) {
          reject(err);
          return;
        }

        if (this.changes === 0) {
          reject(new Error(`No active allocation found for port ${port} and router ${routerId}`));
          return;
        }

        console.log(`Port ${port} released by router ${routerId}`);
        resolve(true);
      });
    });
  }

  async getPortStatus(port) {
    return new Promise((resolve, reject) => {
      const sql = `
        SELECT * FROM port_allocations 
        WHERE port = ? AND status = 'active'
        ORDER BY allocated_at DESC 
        LIMIT 1
      `;

      this.db.get(sql, [port], (err, row) => {
        if (err) {
          reject(err);
          return;
        }

        if (!row) {
          resolve({ port, status: 'available' });
          return;
        }

        resolve({
          port: row.port,
          routerId: row.router_id,
          allocatedAt: row.allocated_at,
          lastHeartbeat: row.last_heartbeat,
          status: row.status,
          metadata: JSON.parse(row.metadata || '{}')
        });
      });
    });
  }

  async getAllocationByRouterId(routerId) {
    return new Promise((resolve, reject) => {
      const sql = `
        SELECT * FROM port_allocations 
        WHERE router_id = ? AND status = 'active'
        ORDER BY allocated_at DESC 
        LIMIT 1
      `;

      this.db.get(sql, [routerId], (err, row) => {
        if (err) {
          reject(err);
          return;
        }

        if (!row) {
          resolve(null);
          return;
        }

        resolve({
          id: row.id,
          port: row.port,
          routerId: row.router_id,
          routerUsername: row.router_username,
          routerPassword: row.router_password,
          allocatedAt: row.allocated_at,
          lastHeartbeat: row.last_heartbeat,
          status: row.status,
          metadata: JSON.parse(row.metadata || '{}')
        });
      });
    });
  }

  async getAllAllocations() {
    return new Promise((resolve, reject) => {
      const sql = `
        SELECT * FROM port_allocations 
        WHERE status = 'active'
        ORDER BY allocated_at DESC
      `;

      this.db.all(sql, [], (err, rows) => {
        if (err) {
          reject(err);
          return;
        }

        const allocations = rows.map(row => ({
          id: row.id,
          port: row.port,
          routerId: row.router_id,
          allocatedAt: row.allocated_at,
          lastHeartbeat: row.last_heartbeat,
          status: row.status,
          metadata: JSON.parse(row.metadata || '{}')
        }));

        resolve(allocations);
      });
    });
  }

  async updateHeartbeat(port, routerId) {
    return new Promise((resolve, reject) => {
      // First try to update with exact router ID match
      const sql = `
        UPDATE port_allocations 
        SET last_heartbeat = CURRENT_TIMESTAMP
        WHERE port = ? AND router_id = ? AND status = 'active'
      `;

      this.db.run(sql, [port, routerId], (err) => {
        if (err) {
          reject(err);
          return;
        }

        if (this.changes > 0) {
          console.log(`Heartbeat updated for port ${port} with router ${routerId}`);
          resolve(true);
          return;
        }

        // If no exact match, try to update just by port (for legacy compatibility)
        const fallbackSql = `
          UPDATE port_allocations 
          SET last_heartbeat = CURRENT_TIMESTAMP
          WHERE port = ? AND status = 'active'
        `;

        this.db.run(fallbackSql, [port], function(err) {
          if (err) {
            reject(err);
            return;
          }

          if (this.changes === 0) {
            // Create a new allocation entry if port is not found
            console.log(`Creating new allocation for heartbeat on port ${port} with router ${routerId}`);
            const insertSql = `
              INSERT OR REPLACE INTO port_allocations (port, router_id, metadata, allocated_at, last_heartbeat, status)
              VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'active')
            `;
            
            this.db.run(insertSql, [port, routerId, JSON.stringify({})], function(insertErr) {
              if (insertErr) {
                reject(insertErr);
                return;
              }
              console.log(`Heartbeat allocation created for port ${port}`);
              resolve(true);
            });
          } else {
            console.log(`Heartbeat updated for port ${port} (fallback mode)`);
            resolve(true);
          }
        });
      });
    });
  }

  async cleanupInactiveAllocations() {
    const cutoffTime = new Date(Date.now() - this.inactivityTimeout).toISOString();
    
    return new Promise((resolve, reject) => {
      const sql = `
        UPDATE port_allocations 
        SET status = 'expired'
        WHERE status = 'active' 
        AND last_heartbeat < ?
      `;

      this.db.run(sql, [cutoffTime], function(err) {
        if (err) {
          reject(err);
          return;
        }

        if (this.changes > 0) {
          console.log(`Cleaned up ${this.changes} inactive port allocations`);
        }

        resolve(this.changes);
      });
    });
  }

  async getStats() {
    return new Promise((resolve, reject) => {
      const sql = `
        SELECT 
          status,
          COUNT(*) as count
        FROM port_allocations 
        GROUP BY status
      `;

      this.db.all(sql, [], (err, rows) => {
        if (err) {
          reject(err);
          return;
        }

        const stats = {
          totalPorts: this.portRange.max - this.portRange.min + 1,
          available: this.portRange.max - this.portRange.min + 1,
          active: 0,
          released: 0,
          expired: 0
        };

        rows.forEach(row => {
          stats[row.status] = row.count;
          if (row.status === 'active') {
            stats.available -= row.count;
          }
        });

        resolve(stats);
      });
    });
  }

  async resetAllAllocations() {
    return new Promise((resolve, reject) => {
      const sql = `DELETE FROM port_allocations`;

      this.db.run(sql, [], function(err) {
        if (err) {
          reject(err);
          return;
        }

        console.log(`Reset all allocations, deleted ${this.changes} records`);
        resolve(this.changes);
      });
    });
  }

  async updateRouterCredentials(port, credentials) {
    return new Promise((resolve, reject) => {
      const sql = `
        UPDATE port_allocations 
        SET router_username = ?, router_password = ?
        WHERE port = ? AND status = 'active'
      `;

      this.db.run(sql, [credentials.username, credentials.password, port], function(err) {
        if (err) {
          reject(err);
          return;
        }

        if (this.changes === 0) {
          reject(new Error(`No active allocation found for port ${port}`));
          return;
        }

        console.log(`Router credentials updated for port ${port}`);
        resolve(true);
      });
    });
  }

  async getRouterCredentialsByPort(port) {
    return new Promise((resolve, reject) => {
      const sql = `
        SELECT router_username, router_password 
        FROM port_allocations 
        WHERE port = ? AND status = 'active'
        LIMIT 1
      `;

      this.db.get(sql, [port], (err, row) => {
        if (err) {
          reject(err);
          return;
        }

        if (!row) {
          resolve(null);
          return;
        }

        resolve({
          username: row.router_username,
          password: row.router_password
        });
      });
    });
  }

  async cleanup() {
    if (this.db) {
      this.db.close((err) => {
        if (err) {
          console.error('Error closing database:', err);
        } else {
          console.log('Database connection closed');
        }
      });
    }
  }
}

module.exports = PortManager; 