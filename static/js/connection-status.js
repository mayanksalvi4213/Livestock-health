/**
 * Connection Status Monitor
 * 
 * This utility monitors the user's internet connection and provides
 * visual feedback when the connection is slow or offline.
 */

class ConnectionMonitor {
  constructor(options = {}) {
    this.statusElement = options.statusElement || '#connection-status';
    this.offlineClass = options.offlineClass || 'connection-offline';
    this.onlineClass = options.onlineClass || 'connection-online';
    this.slowClass = options.slowClass || 'connection-slow';
    this.checkInterval = options.checkInterval || 30000; // 30 seconds
    this.offlineTimeout = options.offlineTimeout || 5000; // 5 seconds
    this.slowThreshold = options.slowThreshold || 3000; // 3 seconds
    this.pingUrl = options.pingUrl || '/ping';
    this.pingTimer = null;
    this.isOnline = navigator.onLine;
    
    this.init();
  }
  
  /**
   * Initialize the connection monitor
   */
  init() {
    // Create status element if it doesn't exist
    this.ensureStatusElement();
    
    // Set up event listeners for online/offline events
    window.addEventListener('online', () => this.handleOnline());
    window.addEventListener('offline', () => this.handleOffline());
    
    // Initial connection check
    this.checkConnection();
    
    // Start periodic checking
    this.pingTimer = setInterval(() => this.checkConnection(), this.checkInterval);
  }
  
  /**
   * Ensure the status element exists
   */
  ensureStatusElement() {
    const statusEl = document.querySelector(this.statusElement);
    
    if (!statusEl) {
      const newStatusEl = document.createElement('div');
      newStatusEl.id = this.statusElement.replace('#', '');
      newStatusEl.className = 'connection-status-container';
      newStatusEl.innerHTML = `
        <div class="connection-status-content">
          <i class="fas fa-wifi"></i>
          <span class="connection-message">Checking connection...</span>
        </div>
      `;
      
      // Add CSS
      const style = document.createElement('style');
      style.textContent = `
        .connection-status-container {
          position: fixed;
          bottom: 20px;
          right: 20px;
          z-index: 9999;
          transition: opacity 0.3s ease-in-out;
          opacity: 0;
        }
        .connection-status-container.active {
          opacity: 1;
        }
        .connection-status-content {
          padding: 8px 16px;
          border-radius: 4px;
          display: flex;
          align-items: center;
          box-shadow: 0 2px 5px rgba(0,0,0,0.2);
          font-size: 0.9rem;
          max-width: 300px;
        }
        .connection-status-container i {
          margin-right: 8px;
        }
        .connection-online {
          background-color: #d4edda;
          color: #155724;
        }
        .connection-offline {
          background-color: #f8d7da;
          color: #721c24;
        }
        .connection-slow {
          background-color: #fff3cd;
          color: #856404;
        }
      `;
      
      document.head.appendChild(style);
      document.body.appendChild(newStatusEl);
    }
  }
  
  /**
   * Handle online event
   */
  handleOnline() {
    this.isOnline = true;
    this.updateStatus('online', 'Connected');
    
    // Verify connection with a ping
    this.checkConnection();
  }
  
  /**
   * Handle offline event
   */
  handleOffline() {
    this.isOnline = false;
    this.updateStatus('offline', 'You are offline. Please check your internet connection.');
  }
  
  /**
   * Check connection by pinging the server
   */
  async checkConnection() {
    // If navigator says we're offline, trust it
    if (!navigator.onLine) {
      this.handleOffline();
      return;
    }
    
    const startTime = Date.now();
    
    try {
      // Use a small timeout to detect very slow connections
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.offlineTimeout);
      
      const response = await fetch(this.pingUrl, {
        method: 'GET',
        cache: 'no-store',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const endTime = Date.now();
        const pingTime = endTime - startTime;
        
        // Check if connection is slow
        if (pingTime > this.slowThreshold) {
          this.updateStatus('slow', `Slow connection detected (${pingTime}ms). This may affect app performance.`);
        } else {
          this.updateStatus('online', 'Connected', true);
        }
      } else {
        this.updateStatus('offline', 'Server error. Please try again later.');
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        this.updateStatus('slow', 'Very slow connection detected. Some features may not work properly.');
      } else {
        this.updateStatus('offline', 'Connection error. Please check your internet connection.');
      }
    }
  }
  
  /**
   * Update status display
   */
  updateStatus(status, message, autoHide = false) {
    const statusEl = document.querySelector(this.statusElement);
    if (!statusEl) return;
    
    // Remove previous classes
    statusEl.classList.remove(this.onlineClass, this.offlineClass, this.slowClass);
    
    // Add appropriate class
    if (status === 'online') {
      statusEl.classList.add(this.onlineClass);
    } else if (status === 'offline') {
      statusEl.classList.add(this.offlineClass);
    } else if (status === 'slow') {
      statusEl.classList.add(this.slowClass);
    }
    
    // Update message
    const messageEl = statusEl.querySelector('.connection-message');
    if (messageEl) {
      messageEl.textContent = message;
    }
    
    // Show the status
    statusEl.classList.add('active');
    
    // Auto-hide status if online after a few seconds
    if (autoHide) {
      setTimeout(() => {
        statusEl.classList.remove('active');
      }, 3000);
    }
  }
  
  /**
   * Stop monitoring
   */
  stop() {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }
}

// Example usage:
// const connectionMonitor = new ConnectionMonitor({
//   statusElement: '#connection-status'
// }); 