const fs = require('fs');
const path = require('path');

/**
 * NetPilot Agent Dual-Output Logger
 * 
 * Provides categorized logging with dual output:
 * - Terminal: Colored output when TTY is detected (for development)
 * - Files: Clean text without ANSI codes (for production/storage)
 * 
 * Categories:
 * - main.log: Application lifecycle, startup, shutdown
 * - config.log: Configuration loading, validation, updates
 * - tunnel.log: Tunnel operations, monitoring, heartbeat
 * - router.log: Router communication, SSH, package installation
 * - port.log: Port allocation, cloud VM communication
 * - status.log: Status API server, health checks
 * - error.log: All errors from all modules (centralized)
 * - debug.log: Detailed debug information
 * 
 * VIEWING COLORED LOGS:
 * For colorized log viewing, use these tools:
 * - bat: `bat --language log agent/logs/main.log`
 * - bat with tail: `tail -f agent/logs/main.log | bat --paging=never -l log`
 * - ccze: `cat agent/logs/main.log | ccze`
 * 
 * COLOR CHOICES:
 * Colors selected for maximum readability across light/dark terminals:
 * - Avoided: bright yellow (poor light bg contrast), blue (invisible on cmd.exe), grey (solarized conflicts)
 * - Using: red, green, cyan, magenta, white - proven accessible colors
 */
class Logger {
  constructor() {
    if (Logger.instance) {
      return Logger.instance;
    }

    // Determine writable logs directory
    try {
      // In Electron main process, app.getPath('userData') is a safe, writable location
      const { app: electronApp } = require('electron');
      if (electronApp && electronApp.getPath) {
        this.logsDir = path.join(electronApp.getPath('userData'), 'logs');
      } else {
        // Fallback to current working directory if electron app is not available yet
        this.logsDir = path.join(process.cwd(), 'logs');
      }
    } catch (err) {
      // Not running inside Electron (unit tests, etc.)
      this.logsDir = path.join(process.cwd(), 'logs');
    }

    this.maxFileSize = 10 * 1024 * 1024; // 10MB
    this.writeQueue = [];
    this.isProcessing = false;
    
    // TTY detection for colored output
    this.isTerminal = process.stdout.isTTY;
    
    // ANSI color codes (only used for terminal output)
    // Selected for maximum accessibility across terminals
    this.colors = {
      reset: '\x1b[0m',
      bright: '\x1b[1m',
      dim: '\x1b[2m',
      // Safe text colors - avoid blue, bright yellow, grey
      red: '\x1b[31m',
      green: '\x1b[32m',
      cyan: '\x1b[36m',
      magenta: '\x1b[35m',
      white: '\x1b[37m',
      // Dim variants for timestamps
      dimCyan: '\x1b[2m\x1b[36m'
    };
    
    // Level colors for terminal output - using accessible colors only
    this.levelColors = {
      ERROR: this.colors.red,
      WARN: this.colors.magenta,        // Changed from yellow to magenta
      INFO: this.colors.green,
      DEBUG: this.colors.cyan,
      TRACE: this.colors.dimCyan        // Changed from gray to dimCyan
    };
    
    // Category colors for terminal output - avoiding problematic colors
    this.categoryColors = {
      MAIN: this.colors.cyan,           // Changed from blue to cyan
      CONFIG: this.colors.magenta,
      TUNNEL: this.colors.cyan,
      ROUTER: this.colors.green,
      PORT: this.colors.white,          // Changed from yellow to white
      STATUS: this.colors.cyan,         // Changed from blue to cyan
      ERROR: this.colors.red,
      DEBUG: this.colors.dimCyan        // Changed from gray to dimCyan
    };

    this.ensureLogsDir();
    Logger.instance = this;
  }

  ensureLogsDir() {
    if (!fs.existsSync(this.logsDir)) {
      fs.mkdirSync(this.logsDir, { recursive: true });
    }
  }

  formatTimestamp() {
    return new Date().toISOString();
  }

  // Clean format for file output (no ANSI codes)
  formatCleanMessage(level, category, message) {
    const timestamp = this.formatTimestamp();
    return `[${timestamp}] [${level}] [${category}] ${message}`;
  }

  // Colored format for terminal output (with ANSI codes when TTY detected)
  formatColoredMessage(level, category, message) {
    if (!this.isTerminal) {
      // If not a terminal, return clean format
      return this.formatCleanMessage(level, category, message);
    }

    const timestamp = this.formatTimestamp();
    const levelColor = this.levelColors[level] || '';
    const categoryColor = this.categoryColors[category] || '';
    const reset = this.colors.reset;
    
    // Format: [dimCyan timestamp] [colored level] [colored category] message
    return `${this.colors.dimCyan}[${timestamp}]${reset} ${levelColor}[${level}]${reset} ${this.colors.bright}${categoryColor}[${category}]${reset} ${message}`;
  }

  async writeToFile(filename, message) {
    const cleanMessage = this.formatCleanMessage(
      message.level,
      message.category,
      message.text
    );

    this.writeQueue.push({
      filename,
      content: cleanMessage + '\n'
    });

    if (!this.isProcessing) {
      this.processWriteQueue();
    }
  }

  async processWriteQueue() {
    this.isProcessing = true;

    while (this.writeQueue.length > 0) {
      const { filename, content } = this.writeQueue.shift();
      const filePath = path.join(this.logsDir, filename);

      try {
        // Check file size and rotate if needed
        if (fs.existsSync(filePath)) {
          const stats = fs.statSync(filePath);
          if (stats.size > this.maxFileSize) {
            await this.rotateLogFile(filePath);
          }
        }

        await fs.promises.appendFile(filePath, content);
      } catch (error) {
        // Fallback to console if file writing fails
        console.error(`Logger: Failed to write to ${filename}:`, error.message);
      }
    }

    this.isProcessing = false;
  }

  async rotateLogFile(filePath) {
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const rotatedPath = `${filePath}.${timestamp}`;
      await fs.promises.rename(filePath, rotatedPath);
    } catch (error) {
      console.error('Logger: Failed to rotate log file:', error.message);
    }
  }

  log(level, category, message) {
    const logData = {
      level: level.toUpperCase(),
      category: category.toUpperCase(),
      text: message
    };

    // Terminal output (colored if TTY, clean if not)
    const terminalMessage = this.formatColoredMessage(logData.level, logData.category, logData.text);
    console.log(terminalMessage);

    // File output (always clean)
    const filename = `${category.toLowerCase()}.log`;
    this.writeToFile(filename, logData);

    // Also write errors to error.log
    if (level.toUpperCase() === 'ERROR') {
      this.writeToFile('error.log', logData);
    }
  }

  // Category-specific methods
  main(message) {
    this.log('INFO', 'MAIN', message);
  }

  config(message) {
    this.log('INFO', 'CONFIG', message);
  }

  tunnel(message) {
    this.log('INFO', 'TUNNEL', message);
  }

  router(message) {
    this.log('INFO', 'ROUTER', message);
  }

  port(message) {
    this.log('INFO', 'PORT', message);
  }

  status(message) {
    this.log('INFO', 'STATUS', message);
  }

  // Level-specific methods
  error(message) {
    this.log('ERROR', 'ERROR', message);
  }

  warn(message) {
    this.log('WARN', 'WARN', message);
  }

  info(message) {
    this.log('INFO', 'INFO', message);
  }

  debug(message) {
    this.log('DEBUG', 'DEBUG', message);
  }

  trace(message) {
    this.log('TRACE', 'TRACE', message);
  }
}

// Export singleton instance
module.exports = new Logger(); 