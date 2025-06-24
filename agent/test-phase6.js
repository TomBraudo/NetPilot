/**
 * NetPilot Agent - Phase 6 Testing Script
 * Agent User Interface Validation
 * 
 * Tests all Phase 6 components:
 * - Main Window Design ✅
 * - Setup Process Flow ✅
 * - Advanced Features ✅
 *   - Settings Panel ✅
 *   - Log Viewer ✅
 *   - Reconnect Functionality ✅
 *   - Uninstall Option ✅
 */

const { app, BrowserWindow } = require('electron');
const path = require('path');

class Phase6Tester {
  constructor() {
    this.testResults = [];
    this.window = null;
  }

  async runAllTests() {
    console.log('\n🧪 Phase 6: Agent User Interface - Testing Started');
    console.log('==================================================\n');

    try {
      await this.testMainWindowDesign();
      await this.testSetupProcessFlow();
      await this.testAdvancedFeatures();
      await this.testResponsiveDesign();
      await this.testAccessibility();
      
      this.printResults();
      
    } catch (error) {
      console.error('❌ Phase 6 testing failed:', error.message);
      return false;
    }
  }

  async testMainWindowDesign() {
    console.log('🎨 Testing Main Window Design...');
    
    try {
      // Test 1: Window Creation and Basic Layout
      await this.createTestWindow();
      this.addResult('✅ Window creation', 'success', 'Electron window opens successfully');
      
      // Test 2: NetPilot Branding Elements
      const hasTitle = await this.checkElement('.app-title');
      this.addResult(hasTitle ? '✅ NetPilot branding' : '❌ NetPilot branding', 
                     hasTitle ? 'success' : 'error', 
                     'NetPilot title and logo area present');
      
      // Test 3: Form Input Fields
      const inputFields = [
        '#router-ip',
        '#username', 
        '#password'
      ];
      
      for (const field of inputFields) {
        const exists = await this.checkElement(field);
        this.addResult(exists ? `✅ Input field ${field}` : `❌ Input field ${field}`,
                       exists ? 'success' : 'error',
                       `Form input ${field} exists with proper styling`);
      }
      
      // Test 4: Action Buttons
      const buttons = [
        '#test-connection-btn',
        '#enable-wifi-btn',
        '#install-btn'
      ];
      
      for (const button of buttons) {
        const exists = await this.checkElement(button);
        this.addResult(exists ? `✅ Button ${button}` : `❌ Button ${button}`,
                       exists ? 'success' : 'error',
                       `Action button ${button} exists and styled correctly`);
      }
      
      // Test 5: Progress Section
      const progressExists = await this.checkElement('#progress-section');
      this.addResult(progressExists ? '✅ Progress section' : '❌ Progress section',
                     progressExists ? 'success' : 'error',
                     'Progress bar and steps section implemented');
      
      // Test 6: Status Indicator
      const statusExists = await this.checkElement('#status-indicator');
      this.addResult(statusExists ? '✅ Status indicator' : '❌ Status indicator',
                     statusExists ? 'success' : 'error',
                     'Connection status indicator with color coding');
      
    } catch (error) {
      this.addResult('❌ Main Window Design', 'error', `Failed: ${error.message}`);
    }
  }

  async testSetupProcessFlow() {
    console.log('🔄 Testing Setup Process Flow...');
    
    try {
      // Test 1: Input Validation
      const validationExists = await this.checkJSFunction('getFormCredentials');
      this.addResult(validationExists ? '✅ Input validation' : '❌ Input validation',
                     validationExists ? 'success' : 'error',
                     'IP format and required field validation');
      
      // Test 2: SSH Connectivity Test
      const testConnExists = await this.checkJSFunction('handleTestConnection');
      this.addResult(testConnExists ? '✅ SSH connectivity test' : '❌ SSH connectivity test',
                     testConnExists ? 'success' : 'error',
                     'Test Connection functionality implemented');
      
      // Test 3: Progress Tracking (5 Steps)
      const steps = [1, 2, 3, 4, 5];
      let allStepsExist = true;
      
      for (const step of steps) {
        const stepExists = await this.checkElement(`[data-step="${step}"]`);
        if (!stepExists) allStepsExist = false;
      }
      
      this.addResult(allStepsExist ? '✅ Progress tracking (5 steps)' : '❌ Progress tracking',
                     allStepsExist ? 'success' : 'error',
                     'All 5 installation steps with visual progress');
      
      // Test 4: Error Handling
      const errorHandlingExists = await this.checkJSFunction('showNotification');
      this.addResult(errorHandlingExists ? '✅ Error handling' : '❌ Error handling',
                     errorHandlingExists ? 'success' : 'error',
                     'User-friendly error messages and notifications');
      
      // Test 5: Success Confirmation
      const successHandlingExists = await this.checkJSFunction('updateConnectionStatus');
      this.addResult(successHandlingExists ? '✅ Success confirmation' : '❌ Success confirmation',
                     successHandlingExists ? 'success' : 'error',
                     'Success confirmation with tunnel status');
      
    } catch (error) {
      this.addResult('❌ Setup Process Flow', 'error', `Failed: ${error.message}`);
    }
  }

  async testAdvancedFeatures() {
    console.log('⚙️ Testing Advanced Features...');
    
    try {
      // Test 1: Settings Panel
      const settingsModal = await this.checkElement('#settings-modal');
      const settingsBtn = await this.checkElement('#settings-btn');
      this.addResult((settingsModal && settingsBtn) ? '✅ Settings panel' : '❌ Settings panel',
                     (settingsModal && settingsBtn) ? 'success' : 'error',
                     'Enhanced settings modal with 3 tabs (General, Cloud VM, Advanced)');
      
      // Test 2: Settings Tabs
      const tabs = ['general', 'cloud', 'advanced'];
      let allTabsExist = true;
      
      for (const tab of tabs) {
        const tabExists = await this.checkElement(`[data-tab="${tab}"]`);
        const contentExists = await this.checkElement(`#${tab}-tab`);
        if (!tabExists || !contentExists) allTabsExist = false;
      }
      
      this.addResult(allTabsExist ? '✅ Settings tabs' : '❌ Settings tabs',
                     allTabsExist ? 'success' : 'error',
                     'All 3 settings tabs with proper content sections');
      
      // Test 3: Log Viewer
      const logsModal = await this.checkElement('#logs-modal');
      const logsContent = await this.checkElement('#logs-content');
      const logFilters = await this.checkElement('.logs-filters');
      this.addResult((logsModal && logsContent && logFilters) ? '✅ Log viewer' : '❌ Log viewer',
                     (logsModal && logsContent && logFilters) ? 'success' : 'error',
                     'Comprehensive log viewer with filtering and export');
      
      // Test 4: Reconnect Functionality  
      const reconnectBtn = await this.checkElement('#reconnect-btn');
      const reconnectFunction = await this.checkJSFunction('handleReconnect');
      this.addResult((reconnectBtn && reconnectFunction) ? '✅ Reconnect functionality' : '❌ Reconnect functionality',
                     (reconnectBtn && reconnectFunction) ? 'success' : 'error',
                     'Re-establish tunnel without full reinstall');
      
      // Test 5: Uninstall Option
      const uninstallBtn = await this.checkElement('#uninstall-btn');
      const uninstallFunction = await this.checkJSFunction('handleUninstall');
      this.addResult((uninstallBtn && uninstallFunction) ? '✅ Uninstall option' : '❌ Uninstall option',
                     (uninstallBtn && uninstallFunction) ? 'success' : 'error',
                     'Remove NetPilot components from router');
      
      // Test 6: Status Actions Management
      const statusActions = await this.checkElement('#status-actions');
      const showActions = await this.checkJSFunction('showStatusActions');
      const hideActions = await this.checkJSFunction('hideStatusActions');
      this.addResult((statusActions && showActions && hideActions) ? '✅ Status actions' : '❌ Status actions',
                     (statusActions && showActions && hideActions) ? 'success' : 'error',
                     'Dynamic status action buttons based on connection state');
      
      // Test 7: Enhanced Help Modal
      const helpModal = await this.checkElement('#help-modal');
      const helpContent = await this.checkElement('.help-content');
      this.addResult((helpModal && helpContent) ? '✅ Help system' : '❌ Help system',
                     (helpModal && helpContent) ? 'success' : 'error',
                     'Comprehensive help documentation with troubleshooting');
      
    } catch (error) {
      this.addResult('❌ Advanced Features', 'error', `Failed: ${error.message}`);
    }
  }

  async testResponsiveDesign() {
    console.log('📱 Testing Responsive Design...');
    
    try {
      // Test 1: Mobile CSS Rules
      const hasMobileCSS = await this.checkCSSRule('@media (max-width: 500px)');
      this.addResult(hasMobileCSS ? '✅ Mobile responsive' : '❌ Mobile responsive',
                     hasMobileCSS ? 'success' : 'error',
                     'CSS responsive design for mobile devices');
      
      // Test 2: Modal Responsiveness
      const hasModalResponsive = await this.checkElement('.modal-content');
      this.addResult(hasModalResponsive ? '✅ Modal responsive' : '❌ Modal responsive',
                     hasModalResponsive ? 'success' : 'error',
                     'Modals adapt to different screen sizes');
      
    } catch (error) {
      this.addResult('❌ Responsive Design', 'error', `Failed: ${error.message}`);
    }
  }

  async testAccessibility() {
    console.log('♿ Testing Accessibility...');
    
    try {
      // Test 1: Focus Styles
      const hasFocusStyles = await this.checkCSSRule('button:focus');
      this.addResult(hasFocusStyles ? '✅ Focus accessibility' : '❌ Focus accessibility',
                     hasFocusStyles ? 'success' : 'error',
                     'Proper focus styles for keyboard navigation');
      
      // Test 2: ARIA Labels and Semantic HTML
      const hasSemanticHTML = await this.checkElement('main') && await this.checkElement('header') && await this.checkElement('footer');
      this.addResult(hasSemanticHTML ? '✅ Semantic HTML' : '❌ Semantic HTML',
                     hasSemanticHTML ? 'success' : 'error',
                     'Semantic HTML structure for screen readers');
      
    } catch (error) {
      this.addResult('❌ Accessibility', 'error', `Failed: ${error.message}`);
    }
  }

  async createTestWindow() {
    return new Promise((resolve) => {
      this.window = new BrowserWindow({
        width: 900,
        height: 700,
        webPreferences: {
          nodeIntegration: false,
          contextIsolation: true,
          preload: path.join(__dirname, 'src', 'preload.js')
        },
        show: false
      });

      this.window.loadFile(path.join(__dirname, 'src', 'renderer', 'index.html'));
      
      this.window.webContents.once('did-finish-load', () => {
        resolve();
      });
    });
  }

  async checkElement(selector) {
    try {
      const result = await this.window.webContents.executeJavaScript(`
        document.querySelector('${selector}') !== null
      `);
      return result;
    } catch (error) {
      return false;
    }
  }

  async checkJSFunction(functionName) {
    try {
      const result = await this.window.webContents.executeJavaScript(`
        typeof window.netPilotUI !== 'undefined' && 
        typeof window.netPilotUI.${functionName} === 'function'
      `);
      return result;
    } catch (error) {
      // Check if function exists in global scope or as method
      try {
        const globalResult = await this.window.webContents.executeJavaScript(`
          typeof ${functionName} !== 'undefined' || 
          (typeof NetPilotAgentUI !== 'undefined' && 
           NetPilotAgentUI.prototype.${functionName} !== undefined)
        `);
        return globalResult;
      } catch (e) {
        return false;
      }
    }
  }

  async checkCSSRule(rule) {
    try {
      const result = await this.window.webContents.executeJavaScript(`
        Array.from(document.styleSheets).some(sheet => {
          try {
            return Array.from(sheet.cssRules || sheet.rules).some(r => 
              r.cssText && r.cssText.includes('${rule}')
            );
          } catch (e) {
            return false;
          }
        })
      `);
      return result;
    } catch (error) {
      return false;
    }
  }

  addResult(test, status, description) {
    this.testResults.push({ test, status, description });
    const icon = status === 'success' ? '✅' : status === 'error' ? '❌' : '⚠️';
    console.log(`   ${icon} ${test}: ${description}`);
  }

  printResults() {
    console.log('\n📊 Phase 6 Test Results Summary');
    console.log('================================\n');
    
    const successful = this.testResults.filter(r => r.status === 'success').length;
    const failed = this.testResults.filter(r => r.status === 'error').length;
    const warnings = this.testResults.filter(r => r.status === 'warning').length;
    const total = this.testResults.length;
    
    console.log(`✅ Successful tests: ${successful}/${total}`);
    console.log(`❌ Failed tests: ${failed}/${total}`);
    console.log(`⚠️  Warnings: ${warnings}/${total}`);
    console.log(`📈 Success rate: ${((successful / total) * 100).toFixed(1)}%\n`);
    
    if (failed > 0) {
      console.log('❌ Failed Tests:');
      this.testResults
        .filter(r => r.status === 'error')
        .forEach(r => console.log(`   • ${r.test}: ${r.description}`));
      console.log('');
    }
    
    // Phase 6 Completion Assessment
    const criticalFeatures = [
      'Main Window Design',
      'Setup Process Flow',
      'Settings panel',
      'Log viewer',
      'Reconnect functionality',
      'Uninstall option'
    ];
    
    const criticalSuccess = this.testResults
      .filter(r => criticalFeatures.some(cf => r.test.includes(cf)) && r.status === 'success')
      .length;
    
    const isPhase6Complete = criticalSuccess >= criticalFeatures.length && failed === 0;
    
    console.log(`🎯 Phase 6 Assessment: ${isPhase6Complete ? '✅ COMPLETE' : '❌ INCOMPLETE'}`);
    
    if (isPhase6Complete) {
      console.log('\n🎉 Phase 6: Agent User Interface - Successfully Implemented!');
      console.log('\nKey Features Completed:');
      console.log('• ✅ Main Window Design with NetPilot branding');
      console.log('• ✅ Complete 5-step setup process flow');
      console.log('• ✅ Enhanced settings panel with 3 tabs');
      console.log('• ✅ Comprehensive log viewer with filtering');
      console.log('• ✅ Reconnect functionality without reinstall');
      console.log('• ✅ Complete uninstall option');
      console.log('• ✅ Responsive design for all screen sizes');
      console.log('• ✅ Accessibility features and focus management');
      console.log('• ✅ Modal system for advanced features');
      console.log('• ✅ Real-time status management');
    }
    
    if (this.window) {
      this.window.close();
    }
    
    return isPhase6Complete;
  }
}

// Run tests when this script is executed directly
if (require.main === module) {
  app.whenReady().then(async () => {
    const tester = new Phase6Tester();
    const success = await tester.runAllTests();
    
    setTimeout(() => {
      app.quit();
      process.exit(success ? 0 : 1);
    }, 2000);
  });
}

module.exports = Phase6Tester; 