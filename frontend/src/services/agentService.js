import axios from 'axios';

const API_URL = '/api/agents';
const CONNECTION_TIMEOUT = 5000; // 5 seconds timeout

/**
 * Create an event source stream with standardized event handling
 * @param {string} url - The URL to connect to
 * @param {object} callbacks - Callback functions for different event types
 * @returns {object} - Object with methods to control the stream
 */
const createEventSourceStream = (url, callbacks = {}) => {
  try {
    // Create an event source for SSE
    const eventSource = new EventSource(url);
    let connectionEstablished = false;
    
    // Set a timeout for connection
    const connectionTimeout = setTimeout(() => {
      if (!connectionEstablished) {
        console.error('Connection timeout - could not connect to the server');
        if (callbacks.onError) {
          callbacks.onError({ 
            error: 'Connection timeout - could not connect to the server. Make sure the backend is running.' 
          });
        }
        eventSource.close();
      }
    }, CONNECTION_TIMEOUT);
    
    // Handle connection open
    eventSource.onopen = () => {
      connectionEstablished = true;
      clearTimeout(connectionTimeout);
      console.log('EventSource connection established');
    };
    
    // Handle different event types
    const eventTypes = ['step', 'state', 'complete'];
    
    eventTypes.forEach(eventType => {
      if (callbacks[`on${eventType.charAt(0).toUpperCase() + eventType.slice(1)}`]) {
        eventSource.addEventListener(eventType, (event) => {
          try {
            const data = JSON.parse(event.data);
            callbacks[`on${eventType.charAt(0).toUpperCase() + eventType.slice(1)}`](data);
          } catch (error) {
            console.error(`Error parsing ${eventType} data:`, error, event.data);
          } finally {
            // Close the connection when complete for the 'complete' event
            if (eventType === 'complete') {
              eventSource.close();
            }
          }
        });
      }
    });
    
    // Handle error events from the SSE stream
    eventSource.addEventListener('error', (event) => {
      clearTimeout(connectionTimeout);
      console.error('SSE error event:', event);
      let data = { error: 'Unknown error' };
      try {
        if (event.data) {
          data = JSON.parse(event.data);
        }
      } catch (e) {
        // If parsing fails, use default error
        console.error('Error parsing error data:', e);
      }
      
      if (callbacks.onError) {
        callbacks.onError(data);
      }
      
      // Close the connection on error
      eventSource.close();
    });
    
    // Also handle connection errors
    eventSource.onerror = (error) => {
      clearTimeout(connectionTimeout);
      console.error('EventSource error:', error);
      
      // Check if the error is due to connection refused
      const isConnectionRefused = error && (
        error.message?.includes('ECONNREFUSED') || 
        error.toString().includes('ECONNREFUSED') ||
        error.toString().includes('Error')
      );
      
      if (callbacks.onError) {
        callbacks.onError({ 
          error: isConnectionRefused 
            ? 'Connection refused. Make sure the backend server is running.' 
            : 'Connection error'
        });
      }
      eventSource.close();
    };
    
    // Return methods to control the stream
    return {
      close: () => {
        clearTimeout(connectionTimeout);
        console.log('Manually closing EventSource');
        eventSource.close();
      }
    };
  } catch (error) {
    console.error('Error setting up event source stream:', error);
    if (callbacks.onError) {
      callbacks.onError({ error: error.message || 'Failed to establish connection' });
    }
    return { close: () => {} };
  }
};

/**
 * Initialize the core agent
 */
export const initializeCoreAgent = async () => {
  try {
    const response = await axios.get(`${API_URL}/initialize`);
    return response.data;
  } catch (error) {
    console.error('Error initializing core agent:', error);
    throw error;
  }
};

/**
 * Send a message to the core agent
 * @param {string} message - The message to send
 */
export const sendMessageToCore = async (message) => {
  try {
    const response = await axios.post(`${API_URL}/core/message`, { message });
    return response.data;
  } catch (error) {
    console.error('Error sending message to core agent:', error);
    throw error;
  }
};

/**
 * Stream a message to the core agent with step-by-step updates
 * @param {string} message - The message to send
 * @param {object} callbacks - Callback functions for different event types
 * @returns {object} - Object with methods to control the stream
 */
export const streamMessageToCore = (message, callbacks = {}) => {
  const url = `${API_URL}/core/message/stream?message=${encodeURIComponent(message)}`;
  return createEventSourceStream(url, callbacks);
};

/**
 * Generate a new agent from the core agent's configuration
 */
export const generateAgent = async () => {
  try {
    const response = await axios.post(`${API_URL}/core/generate`);
    return response.data;
  } catch (error) {
    console.error('Error generating agent:', error);
    throw error;
  }
};

/**
 * Stream the agent generation process with step-by-step updates
 * @param {object} callbacks - Callback functions for different event types
 * @returns {object} - Object with methods to control the stream
 */
export const streamGenerateAgent = (callbacks = {}) => {
  const url = `${API_URL}/core/generate/stream`;
  return createEventSourceStream(url, callbacks);
};

/**
 * Send a message to a specific agent
 * @param {string} agentId - The ID of the agent
 * @param {string} message - The message to send
 */
export const sendMessageToAgent = async (agentId, message) => {
  try {
    const response = await axios.post(`${API_URL}/${agentId}/message`, { message });
    return response.data;
  } catch (error) {
    console.error(`Error sending message to agent ${agentId}:`, error);
    throw error;
  }
};

/**
 * Stream a message to a specific agent with step-by-step updates
 * @param {string} agentId - The ID of the agent
 * @param {string} message - The message to send
 * @param {object} callbacks - Callback functions for different event types
 * @returns {object} - Object with methods to control the stream
 */
export const streamMessageToAgent = (agentId, message, callbacks = {}) => {
  const url = `${API_URL}/${agentId}/message/stream?message=${encodeURIComponent(message)}`;
  return createEventSourceStream(url, callbacks);
}; 