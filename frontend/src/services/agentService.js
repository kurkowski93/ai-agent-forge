import axios from 'axios';

const API_URL = '/api/agents';

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
  try {
    // Create an event source for SSE
    const eventSource = new EventSource(`${API_URL}/core/message/stream?message=${encodeURIComponent(message)}`);
    
    // Handle different event types
    if (callbacks.onStep) {
      eventSource.addEventListener('step', (event) => {
        try {
          const data = JSON.parse(event.data);
          callbacks.onStep(data);
        } catch (error) {
          console.error('Error parsing step data:', error, event.data);
        }
      });
    }
    
    if (callbacks.onState) {
      eventSource.addEventListener('state', (event) => {
        try {
          const data = JSON.parse(event.data);
          callbacks.onState(data);
        } catch (error) {
          console.error('Error parsing state data:', error, event.data);
        }
      });
    }
    
    if (callbacks.onComplete) {
      eventSource.addEventListener('complete', (event) => {
        try {
          const data = JSON.parse(event.data);
          callbacks.onComplete(data);
        } catch (error) {
          console.error('Error parsing complete data:', error, event.data);
        } finally {
          // Close the connection when complete
          eventSource.close();
        }
      });
    }
    
    // Handle error events from the SSE stream
    eventSource.addEventListener('error', (event) => {
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
      console.error('EventSource error:', error);
      if (callbacks.onError) {
        callbacks.onError({ error: 'Connection error' });
      }
      eventSource.close();
    };
    
    // Return methods to control the stream
    return {
      close: () => {
        console.log('Manually closing EventSource');
        eventSource.close();
      }
    };
  } catch (error) {
    console.error('Error setting up stream to core agent:', error);
    if (callbacks.onError) {
      callbacks.onError({ error: error.message });
    }
    return { close: () => {} };
  }
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
  try {
    // Create an event source for SSE
    const eventSource = new EventSource(`${API_URL}/core/generate/stream`);
    
    // Handle different event types
    if (callbacks.onStep) {
      eventSource.addEventListener('step', (event) => {
        try {
          const data = JSON.parse(event.data);
          callbacks.onStep(data);
        } catch (error) {
          console.error('Error parsing step data:', error, event.data);
        }
      });
    }
    
    if (callbacks.onState) {
      eventSource.addEventListener('state', (event) => {
        try {
          const data = JSON.parse(event.data);
          callbacks.onState(data);
        } catch (error) {
          console.error('Error parsing state data:', error, event.data);
        }
      });
    }
    
    if (callbacks.onComplete) {
      eventSource.addEventListener('complete', (event) => {
        try {
          const data = JSON.parse(event.data);
          callbacks.onComplete(data);
        } catch (error) {
          console.error('Error parsing complete data:', error, event.data);
        } finally {
          // Close the connection when complete
          eventSource.close();
        }
      });
    }
    
    // Handle error events from the SSE stream
    eventSource.addEventListener('error', (event) => {
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
      console.error('EventSource error:', error);
      if (callbacks.onError) {
        callbacks.onError({ error: 'Connection error' });
      }
      eventSource.close();
    };
    
    // Return methods to control the stream
    return {
      close: () => {
        console.log('Manually closing EventSource');
        eventSource.close();
      }
    };
  } catch (error) {
    console.error('Error setting up stream for agent generation:', error);
    if (callbacks.onError) {
      callbacks.onError({ error: error.message });
    }
    return { close: () => {} };
  }
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
  try {
    // Create an event source for SSE
    const eventSource = new EventSource(`${API_URL}/${agentId}/message/stream?message=${encodeURIComponent(message)}`);
    
    // Handle different event types
    if (callbacks.onStep) {
      eventSource.addEventListener('step', (event) => {
        try {
          const data = JSON.parse(event.data);
          callbacks.onStep(data);
        } catch (error) {
          console.error('Error parsing step data:', error, event.data);
        }
      });
    }
    
    if (callbacks.onState) {
      eventSource.addEventListener('state', (event) => {
        try {
          const data = JSON.parse(event.data);
          callbacks.onState(data);
        } catch (error) {
          console.error('Error parsing state data:', error, event.data);
        }
      });
    }
    
    if (callbacks.onComplete) {
      eventSource.addEventListener('complete', (event) => {
        try {
          const data = JSON.parse(event.data);
          callbacks.onComplete(data);
        } catch (error) {
          console.error('Error parsing complete data:', error, event.data);
        } finally {
          // Close the connection when complete
          eventSource.close();
        }
      });
    }
    
    // Handle error events from the SSE stream
    eventSource.addEventListener('error', (event) => {
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
      console.error('EventSource error:', error);
      if (callbacks.onError) {
        callbacks.onError({ error: 'Connection error' });
      }
      eventSource.close();
    };
    
    // Return methods to control the stream
    return {
      close: () => {
        console.log('Manually closing EventSource');
        eventSource.close();
      }
    };
  } catch (error) {
    console.error(`Error setting up stream to agent ${agentId}:`, error);
    if (callbacks.onError) {
      callbacks.onError({ error: error.message });
    }
    return { close: () => {} };
  }
}; 