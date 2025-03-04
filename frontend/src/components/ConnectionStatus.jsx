import React, { useState, useEffect } from 'react';
import { checkConnection } from '../services/connectionService';

/**
 * Component for displaying backend connection status
 * @returns {JSX.Element} - Connection status component
 */
const ConnectionStatus = () => {
  const [status, setStatus] = useState('checking');
  const [error, setError] = useState(null);

  useEffect(() => {
    const checkConnectionStatus = async () => {
      try {
        setStatus('checking');
        const result = await checkConnection();
        if (result.status === 'ok') {
          setStatus('connected');
        } else {
          setStatus('disconnected');
          setError(result.error || 'Unknown error');
        }
      } catch (error) {
        setStatus('disconnected');
        setError(error.message || 'Failed to check connection');
      }
    };

    // Check connection on mount
    checkConnectionStatus();

    // Set up interval to check connection periodically
    const interval = setInterval(checkConnectionStatus, 30000); // Check every 30 seconds

    // Clean up interval on unmount
    return () => clearInterval(interval);
  }, []);

  // Status indicator styles
  const statusConfig = {
    checking: {
      bgColor: 'bg-gray-100',
      textColor: 'text-gray-600',
      icon: (
        <svg className="animate-spin h-4 w-4 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      ),
      message: 'Checking connection...'
    },
    connected: {
      bgColor: 'bg-emerald-50',
      textColor: 'text-emerald-800',
      icon: (
        <svg className="h-4 w-4 text-emerald-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      ),
      message: 'Connected to backend'
    },
    disconnected: {
      bgColor: 'bg-red-50',
      textColor: 'text-red-800',
      icon: (
        <svg className="h-4 w-4 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      ),
      message: 'Disconnected from backend'
    }
  };

  const currentStatus = statusConfig[status];

  return (
    <div className="fixed bottom-0 right-0 m-4 z-50">
      <div className={`${currentStatus.bgColor} ${currentStatus.textColor} rounded-lg shadow-lg p-3 flex items-center`}>
        <div className="mr-2">
          {currentStatus.icon}
        </div>
        <div>
          <p className="text-sm font-medium">{currentStatus.message}</p>
          {error && status === 'disconnected' && (
            <p className="text-xs mt-1">{error}</p>
          )}
        </div>
        {status === 'disconnected' && (
          <button 
            onClick={() => window.location.reload()}
            className="ml-3 bg-indigo-600 hover:bg-indigo-700 text-white text-xs py-1 px-2 rounded"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
};

export default ConnectionStatus; 