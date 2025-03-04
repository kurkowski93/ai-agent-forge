import React, { useState } from 'react';

/**
 * Safely render content that might be undefined or null
 * @param {any} content - Content to render
 * @returns {string} - String representation of content
 */
const safeRender = (content) => {
  if (content === undefined || content === null) {
    return '';
  }
  if (typeof content === 'object') {
    try {
      return JSON.stringify(content, null, 2);
    } catch (error) {
      return String(content);
    }
  }
  return String(content);
};

/**
 * Status badge component
 * @param {string} status - Current status
 * @returns {JSX.Element} - Status badge
 */
const StatusBadge = ({ status }) => {
  // Determine the actual display status
  const displayStatus = status === 'starting' && status.length > 0 ? 'processing' : status;
  
  // Map status to color and icon
  const statusConfig = {
    starting: {
      bgColor: 'bg-indigo-100',
      textColor: 'text-indigo-800',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    },
    processing: {
      bgColor: 'bg-amber-100',
      textColor: 'text-amber-800',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      )
    },
    complete: {
      bgColor: 'bg-emerald-100',
      textColor: 'text-emerald-800',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      )
    },
    error: {
      bgColor: 'bg-red-100',
      textColor: 'text-red-800',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    }
  };
  
  const config = statusConfig[displayStatus] || statusConfig.processing;
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor}`}>
      {config.icon}
      {displayStatus.charAt(0).toUpperCase() + displayStatus.slice(1)}
    </span>
  );
};

/**
 * Debug helper to display step data
 * @param {Object} step - The step object
 * @returns {JSX.Element} - Debug info component
 */
const StepDebugInfo = ({ step }) => {
  return (
    <div className="mt-1 p-2 bg-gray-100 rounded text-xs">
      <div className="font-semibold mb-1">Step Debug Info:</div>
      <pre className="overflow-auto max-h-32 text-xs">
        {JSON.stringify(step, null, 2)}
      </pre>
    </div>
  );
};

/**
 * Helper to get the step title/name from various formats
 * @param {Object} step - The step object
 * @returns {string} - Step title/name
 */
const getStepTitle = (step) => {
  // Try different common step name properties
  if (step.name) return step.name;
  if (step.step) return step.step;
  if (step.node) return step.node;
  if (step.title) return step.title;
  if (step.type) return step.type;
  
  // Return a default if none found
  return 'Step';
};

/**
 * Individual step item component
 * @param {Object} step - Step data
 * @param {boolean} isCurrentStep - Whether this is the current step
 * @param {boolean} isPastStep - Whether this is a past step
 * @returns {JSX.Element} - Step item component
 */
const StepItem = ({ step, isCurrentStep, isPastStep }) => {
  const [expanded, setExpanded] = useState(isCurrentStep);
  const [showDebug, setShowDebug] = useState(false);
  
  const getStepStatus = () => {
    if (step.status) return step.status;
    if (isCurrentStep) return 'processing';
    if (isPastStep) return 'complete';
    return 'starting';
  };
  
  const getStatusStyles = () => {
    const status = getStepStatus();
    
    const styles = {
      dot: '',
      line: '',
      title: '',
      card: ''
    };
    
    switch (status) {
      case 'complete':
        styles.dot = 'bg-emerald-500';
        styles.line = 'border-emerald-500';
        styles.title = 'text-emerald-800';
        styles.card = 'border-emerald-200';
        break;
      case 'processing':
        styles.dot = 'bg-amber-500';
        styles.line = 'border-amber-500';
        styles.title = 'text-amber-800';
        styles.card = 'border-amber-200';
        break;
      case 'error':
        styles.dot = 'bg-red-500';
        styles.line = 'border-red-500';
        styles.title = 'text-red-800';
        styles.card = 'border-red-200';
        break;
      default:
        styles.dot = 'bg-gray-300';
        styles.line = 'border-gray-300';
        styles.title = 'text-gray-500';
        styles.card = 'border-gray-200';
    }
    
    return styles;
  };
  
  const styles = getStatusStyles();
  const status = getStepStatus();
  
  // Get agent type badge color
  const getAgentBadgeColor = () => {
    return step.agentType === 'core' 
      ? 'bg-indigo-50 text-indigo-700' 
      : 'bg-emerald-50 text-emerald-700';
  };

  // Get step content
  const stepTitle = getStepTitle(step);
  const stepContent = step.content || step.message || step.description || step.text || '';
  const stepInput = step.input || step.inputs || step.request || {};
  const stepOutput = step.output || step.outputs || step.response || step.result || {};
  const stepError = step.error || '';
  const stepMetadata = step.metadata || step.meta || {};

  return (
    <div className="relative pb-8">
      {/* Vertical line */}
      <div className={`absolute top-0 left-4 -ml-px h-full w-0.5 border-r ${styles.line}`}></div>
      
      {/* Step dot */}
      <div className="relative flex items-start">
        <div className="h-8 flex items-center">
          <div className={`relative z-10 w-2 h-2 rounded-full ${styles.dot} flex items-center justify-center`}>
            {status === 'processing' && (
              <div className="absolute w-4 h-4 rounded-full bg-amber-500 opacity-30 animate-ping"></div>
            )}
          </div>
        </div>
        
        <div className="min-w-0 flex-1 ml-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <h3 className={`text-sm font-medium ${styles.title}`}>
                {stepTitle}
              </h3>
              <div className="ml-2">
                <StatusBadge status={status} />
              </div>
              {step.agentType && (
                <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${getAgentBadgeColor()}`}>
                  {step.agentType === 'core' ? 'Core' : 'Generated'}
                </span>
              )}
            </div>
            <div className="flex items-center">
              <button
                onClick={() => setShowDebug(!showDebug)}
                className="ml-2 text-gray-400 hover:text-gray-600 focus:outline-none"
                title="Debug Step Data"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                </svg>
              </button>
              <button
                onClick={() => setExpanded(!expanded)}
                className="ml-2 text-gray-500 hover:text-gray-700 focus:outline-none"
              >
                {expanded ? (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M5 10a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            </div>
          </div>
          
          {showDebug && <StepDebugInfo step={step} />}
          
          {expanded && (
            <div className={`mt-2 p-3 bg-white border rounded-md ${styles.card} shadow-sm ${expanded ? 'shadow-md' : ''}`}>
              {stepContent && (
                <p className="text-sm text-gray-600 mb-2">{stepContent}</p>
              )}
              
              {Object.keys(stepInput).length > 0 && (
                <div className="mb-2">
                  <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Input</h4>
                  <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                    {safeRender(stepInput)}
                  </pre>
                </div>
              )}
              
              {Object.keys(stepOutput).length > 0 && (
                <div className="mb-2">
                  <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Output</h4>
                  <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                    {safeRender(stepOutput)}
                  </pre>
                </div>
              )}
              
              {stepError && (
                <div className="mb-2">
                  <h4 className="text-xs font-medium text-red-500 uppercase tracking-wide mb-1">Error</h4>
                  <pre className="text-xs bg-red-50 text-red-700 p-2 rounded overflow-x-auto">
                    {safeRender(stepError)}
                  </pre>
                </div>
              )}
              
              {Object.keys(stepMetadata).length > 0 && (
                <div>
                  <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Metadata</h4>
                  <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                    {safeRender(stepMetadata)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * Empty state component when no steps are available
 * @param {string} status - Current status
 * @returns {JSX.Element} - Empty state component
 */
const EmptyState = ({ status }) => (
  <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col items-center justify-center text-center">
    {status === 'processing' ? (
      <>
        <div className="mb-4">
          <div className="animate-spin rounded-full h-10 w-10 border-4 border-indigo-500 border-t-transparent"></div>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Processing...</h3>
        <p className="text-gray-500">
          The agent is working on your request. Steps will appear here as they are completed.
        </p>
      </>
    ) : (
      <>
        <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Steps Yet</h3>
        <p className="text-gray-500">
          When the agent processes your request, the steps will appear here.
        </p>
      </>
    )}
  </div>
);

/**
 * Agent steps component
 * @param {Array} steps - Array of step objects
 * @param {string} currentStep - ID of the current step
 * @param {string} status - Current status
 * @returns {JSX.Element} - Agent steps component
 */
const AgentSteps = ({ steps = [], currentStep, status }) => {
  if (!steps || steps.length === 0) {
    return <EmptyState status={status} />;
  }
  
  // Log steps for debugging
  console.log('Rendering steps:', steps);
  
  return (
    <div className="flow-root">
      <ul className="-mb-8">
        {steps.map((step, index) => (
          <li key={step.id || `step-${index}`}>
            <StepItem
              step={step}
              isCurrentStep={currentStep && step.id === currentStep}
              isPastStep={currentStep && index < steps.findIndex(s => s.id === currentStep)}
            />
          </li>
        ))}
      </ul>
    </div>
  );
};

export default AgentSteps; 