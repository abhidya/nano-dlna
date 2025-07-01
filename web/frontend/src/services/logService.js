/**
 * Frontend Log Service
 * Collects and sends frontend logs to the backend for aggregation
 */

class LogService {
  constructor() {
    this.backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
    this.logQueue = [];
    this.isOnline = navigator.onLine;
    this.batchSize = 10;
    this.flushInterval = 5000; // 5 seconds
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Start batch processing
    this.startBatchProcessor();
    
    // Override console methods to capture logs
    this.setupConsoleCapture();
  }
  
  setupEventListeners() {
    // Network status
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.flushLogs();
    });
    
    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
    
    // Unhandled errors
    window.addEventListener('error', (event) => {
      this.logError('Unhandled Error', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack
      });
    });
    
    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.logError('Unhandled Promise Rejection', {
        reason: event.reason,
        stack: event.reason?.stack
      });
    });
    
    // Page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.flushLogs(); // Flush logs when page becomes hidden
      }
    });
    
    // Before page unload
    window.addEventListener('beforeunload', () => {
      this.flushLogs();
    });
  }
  
  setupConsoleCapture() {
    // Store original console methods
    this.originalConsole = {
      log: console.log,
      warn: console.warn,
      error: console.error,
      info: console.info,
      debug: console.debug
    };
    
    // Override console methods
    console.log = (...args) => {
      this.originalConsole.log(...args);
      this.captureConsoleLog('INFO', args);
    };
    
    console.warn = (...args) => {
      this.originalConsole.warn(...args);
      this.captureConsoleLog('WARNING', args);
    };
    
    console.error = (...args) => {
      this.originalConsole.error(...args);
      this.captureConsoleLog('ERROR', args);
    };
    
    console.info = (...args) => {
      this.originalConsole.info(...args);
      this.captureConsoleLog('INFO', args);
    };
    
    console.debug = (...args) => {
      this.originalConsole.debug(...args);
      this.captureConsoleLog('DEBUG', args);
    };
  }
  
  captureConsoleLog(level, args) {
    try {
      // Convert arguments to strings
      const message = args.map(arg => {
        if (typeof arg === 'object') {
          try {
            return JSON.stringify(arg, null, 2);
          } catch (e) {
            return String(arg);
          }
        }
        return String(arg);
      }).join(' ');
      
      // Get stack trace for location info
      const stack = new Error().stack;
      const stackLines = stack.split('\n');
      
      // Find the first line that's not from this log service
      let filename = 'unknown';
      let lineNumber = 0;
      
      for (let i = 2; i < stackLines.length; i++) {
        const line = stackLines[i];
        if (line.includes('http') && !line.includes('logService')) {
          const match = line.match(/\/([^\/]+):(\d+):(\d+)/);
          if (match) {
            filename = match[1];
            lineNumber = parseInt(match[2]);
            break;
          }
        }
      }
      
      this.addLogEntry({
        level,
        message,
        filename,
        line_number: lineNumber,
        component: 'console',
        timestamp: Date.now() / 1000,
        stack: level === 'ERROR' ? stack : undefined
      });
    } catch (error) {
      // Fallback to original console to avoid infinite loops
      this.originalConsole.error('Error in console capture:', error);
    }
  }
  
  startBatchProcessor() {
    setInterval(() => {
      if (this.logQueue.length > 0) {
        this.flushLogs();
      }
    }, this.flushInterval);
  }
  
  addLogEntry(logData) {
    this.logQueue.push({
      ...logData,
      timestamp: logData.timestamp || Date.now() / 1000,
      user_agent: navigator.userAgent,
      url: window.location.href
    });
    
    // Flush immediately for errors or if queue is full
    if (logData.level === 'ERROR' || this.logQueue.length >= this.batchSize) {
      this.flushLogs();
    }
  }
  
  async flushLogs() {
    if (this.logQueue.length === 0 || !this.isOnline) {
      return;
    }
    
    const logsToSend = [...this.logQueue];
    this.logQueue = [];
    
    try {
      const response = await fetch(`${this.backendUrl}/api/logs/frontend`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          logs: logsToSend,
          session_id: this.getSessionId(),
          timestamp: Date.now() / 1000
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
    } catch (error) {
      // Put logs back in queue on failure
      this.logQueue.unshift(...logsToSend);
      
      // Log error using original console to avoid infinite loops
      this.originalConsole.error('Failed to send logs to backend:', error);
    }
  }
  
  getSessionId() {
    let sessionId = sessionStorage.getItem('log_session_id');
    if (!sessionId) {
      sessionId = Date.now().toString(36) + Math.random().toString(36).substr(2);
      sessionStorage.setItem('log_session_id', sessionId);
    }
    return sessionId;
  }
  
  // Public API methods
  logInfo(message, data = {}) {
    this.addLogEntry({
      level: 'INFO',
      message,
      component: data.component || 'app',
      filename: data.filename || 'unknown',
      line_number: data.line_number || 0,
      extra_data: data
    });
  }
  
  logWarning(message, data = {}) {
    this.addLogEntry({
      level: 'WARNING',
      message,
      component: data.component || 'app',
      filename: data.filename || 'unknown',
      line_number: data.line_number || 0,
      extra_data: data
    });
  }
  
  logError(message, data = {}) {
    this.addLogEntry({
      level: 'ERROR',
      message,
      component: data.component || 'app',
      filename: data.filename || 'unknown',
      line_number: data.line_number || 0,
      stack: data.stack,
      extra_data: data
    });
  }
  
  logDebug(message, data = {}) {
    this.addLogEntry({
      level: 'DEBUG',
      message,
      component: data.component || 'app',
      filename: data.filename || 'unknown',
      line_number: data.line_number || 0,
      extra_data: data
    });
  }
  
  // React component logging helpers
  logComponentMount(componentName) {
    this.logInfo(`Component mounted: ${componentName}`, {
      component: componentName,
      event_type: 'mount'
    });
  }
  
  logComponentUnmount(componentName) {
    this.logInfo(`Component unmounted: ${componentName}`, {
      component: componentName,
      event_type: 'unmount'
    });
  }
  
  logUserAction(action, data = {}) {
    this.logInfo(`User action: ${action}`, {
      component: 'user_interaction',
      action,
      ...data
    });
  }
  
  logApiCall(url, method, status, duration, error = null) {
    const level = error ? 'ERROR' : status >= 400 ? 'WARNING' : 'INFO';
    this.addLogEntry({
      level,
      message: `API call: ${method} ${url} - ${status}${error ? ` (${error})` : ''}`,
      component: 'api',
      filename: 'api_client',
      extra_data: {
        url,
        method,
        status,
        duration,
        error
      }
    });
  }
  
  logPerformance(metric, value, data = {}) {
    this.logInfo(`Performance: ${metric} = ${value}`, {
      component: 'performance',
      metric,
      value,
      ...data
    });
  }
  
  // Cleanup method
  destroy() {
    // Restore original console methods
    Object.assign(console, this.originalConsole);
    
    // Flush remaining logs
    this.flushLogs();
  }
}

// Create singleton instance
const logService = new LogService();

// Export singleton
export default logService;

// Export individual methods for convenience
export const {
  logInfo,
  logWarning,
  logError,
  logDebug,
  logComponentMount,
  logComponentUnmount,
  logUserAction,
  logApiCall,
  logPerformance
} = logService;