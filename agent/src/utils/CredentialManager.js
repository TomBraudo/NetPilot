const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class CredentialManager {
  constructor() {
    this.credentialsDir = path.join(process.env.APPDATA || process.env.HOME || __dirname, '.netpilot');
    this.credentialsFile = path.join(this.credentialsDir, 'credentials.json');
    this.ensureCredentialsDir();
  }

  ensureCredentialsDir() {
    if (!fs.existsSync(this.credentialsDir)) {
      fs.mkdirSync(this.credentialsDir, { recursive: true });
    }
  }

  // Simple encryption for basic security (not production-grade)
  encrypt(text) {
    const algorithm = 'aes-256-cbc';
    const key = crypto.scryptSync('netpilot-agent-key', 'salt', 32);
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipher(algorithm, key);
    let encrypted = cipher.update(text, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    return iv.toString('hex') + ':' + encrypted;
  }

  decrypt(text) {
    try {
      const algorithm = 'aes-256-cbc';
      const key = crypto.scryptSync('netpilot-agent-key', 'salt', 32);
      const textParts = text.split(':');
      const iv = Buffer.from(textParts.shift(), 'hex');
      const encryptedText = textParts.join(':');
      const decipher = crypto.createDecipher(algorithm, key);
      let decrypted = decipher.update(encryptedText, 'hex', 'utf8');
      decrypted += decipher.final('utf8');
      return decrypted;
    } catch (error) {
      return '';
    }
  }

  loadCredentials() {
    try {
      if (!fs.existsSync(this.credentialsFile)) {
        return {};
      }
      const data = fs.readFileSync(this.credentialsFile, 'utf8');
      return JSON.parse(data);
    } catch (error) {
      return {};
    }
  }

  saveCredentials(credentials) {
    try {
      fs.writeFileSync(this.credentialsFile, JSON.stringify(credentials, null, 2));
    } catch (error) {
      console.error('Failed to save credentials:', error);
    }
  }

  async setPassword(service, account, password) {
    try {
      const credentials = this.loadCredentials();
      const key = `${service}:${account}`;
      credentials[key] = password ? this.encrypt(password) : '';
      this.saveCredentials(credentials);
      return true;
    } catch (error) {
      console.error('Failed to set password:', error);
      throw error;
    }
  }

  async getPassword(service, account) {
    try {
      const credentials = this.loadCredentials();
      const key = `${service}:${account}`;
      const encrypted = credentials[key];
      return encrypted ? this.decrypt(encrypted) : null;
    } catch (error) {
      console.error('Failed to get password:', error);
      return null;
    }
  }

  async deletePassword(service, account) {
    try {
      const credentials = this.loadCredentials();
      const key = `${service}:${account}`;
      delete credentials[key];
      this.saveCredentials(credentials);
      return true;
    } catch (error) {
      console.error('Failed to delete password:', error);
      return false;
    }
  }
}

module.exports = CredentialManager; 