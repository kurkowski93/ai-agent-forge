import { API_BASE_URL } from '../config';

/**
 * Service for checking connection status with the backend
 */

// Endpoint to check connection
const HEALTH_CHECK_ENDPOINT = '/api/health';

// Timeout for health check requests (in milliseconds)
const HEALTH_CHECK_TIMEOUT = 5000;

/**
 * Check the connection to the backend server
 * @returns {Promise<Object>} - Object with status and error properties
 */
export const checkConnection = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      return { status: 'ok' };
    } else {
      return { 
        status: 'error', 
        error: `Server responded with status: ${response.status}` 
      };
    }
  } catch (error) {
    console.error('Connection check failed:', error);
    return { 
      status: 'error', 
      error: error.message || 'Failed to connect to the server' 
    };
  }
};

/**
 * Start monitoring the connection to the backend server
 * @param {Function} onStatusChange - Callback function that receives connection status
 * @returns {Function} - Function to stop monitoring
 */
export const startConnectionMonitoring = (onStatusChange) => {
  let isConnected = null;
  let intervalId = null;
  
  // Function to check connection
  const checkConnectionStatus = async () => {
    try {
      const result = await checkConnection();
      const newStatus = result.status === 'ok';
      
      // Only trigger callback if status has changed
      if (isConnected !== newStatus) {
        isConnected = newStatus;
        onStatusChange(newStatus);
      }
    } catch (error) {
      console.error('Connection monitoring error:', error);
      
      // If we get an error, consider it disconnected
      if (isConnected !== false) {
        isConnected = false;
        onStatusChange(false);
      }
    }
  };
  
  // Initial check
  checkConnectionStatus();
  
  // Set up interval for periodic checks
  intervalId = setInterval(checkConnectionStatus, 10000); // Check every 10 seconds
  
  // Return function to stop monitoring
  return () => {
    if (intervalId) {
      clearInterval(intervalId);
    }
  };
}; 