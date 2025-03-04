import React from 'react';

const safeRender = (content) => {
  if (content === null || content === undefined) return '';
  if (typeof content === 'string' || typeof content === 'number') return content;
  if (typeof content === 'object') {
    try {
      return JSON.stringify(content);
    } catch (e) {
      return String(content);
    }
  }
  return String(content);
};

const AgentSteps = ({ steps = [], currentStep, status }) => {
  // Determine the actual display status
  const displayStatus = status === 'starting' && steps.length > 0 ? 'processing' : status;
  
  return (
    <div className="bg-white rounded-lg shadow-md p-4 h-[500px] overflow-auto">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">Agent Processing Steps</h3>
      
      {status && (
        <div className="mb-4">
          <div className="flex items-center">
            <div className={`h-3 w-3 rounded-full mr-2 ${
              displayStatus === 'starting' ? 'bg-slate-500 animate-pulse' :
              displayStatus === 'processing' ? 'bg-amber-500 animate-pulse' :
              displayStatus === 'complete' ? 'bg-green-500' :
              displayStatus === 'error' ? 'bg-red-500' : 'bg-gray-500'
            }`} />
            <span className="font-medium text-gray-700">
              Status: {typeof displayStatus === 'string' ? displayStatus.charAt(0).toUpperCase() + displayStatus.slice(1) : String(displayStatus)}
            </span>
          </div>
        </div>
      )}
      
      {steps.length === 0 ? (
        <div className="text-gray-500 italic flex justify-center items-center h-64">
          {status === 'starting' ? (
            <div className="flex flex-col items-center">
              <div className="animate-spin h-10 w-10 border-4 border-slate-700 rounded-full border-t-transparent mb-3"></div>
              <span>Initializing process...</span>
            </div>
          ) : (
            <span>No steps recorded yet</span>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {steps.map((step, index) => {
            const isCurrentStep = currentStep === step.node;
            const isPastStep = index < steps.indexOf(steps.find(s => s.node === currentStep));
            
            return (
              <div 
                key={index}
                className={`p-3 rounded-md border transition-all duration-300 ${
                  isCurrentStep ? 'border-amber-500 bg-amber-50 shadow-md' : 
                  isPastStep ? 'border-green-500 bg-green-50' : 'border-gray-200'
                }`}
              >
                <div className="flex items-center mb-1">
                  <div className={`h-2 w-2 rounded-full mr-2 ${
                    isPastStep ? 'bg-green-500' :
                    isCurrentStep ? 'bg-amber-500 animate-pulse' :
                    'bg-gray-300'
                  }`} />
                  <span className="font-semibold text-gray-800">
                    {safeRender(step.node || step.step || 'Unknown step')}
                  </span>
                </div>
                
                {step.message && (
                  <p className="text-sm text-gray-600 ml-4">{safeRender(step.message)}</p>
                )}
                
                {step.updates && Object.keys(step.updates).length > 0 && (
                  <div className="mt-2 ml-4">
                    <p className="text-xs text-gray-500 mb-1">Updates:</p>
                    <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-32">
                      {typeof step.updates === 'object' ? JSON.stringify(step.updates, null, 2) : String(step.updates)}
                    </pre>
                  </div>
                )}
                
                {step.timestamp && (
                  <div className="text-xs text-gray-400 mt-1 ml-4">
                    {new Date(step.timestamp * 1000).toLocaleTimeString()}
                  </div>
                )}
              </div>
            );
          })}
          
          {/* Animated dots indicating that something is happening between steps */}
          {status !== 'complete' && status !== 'error' && (
            <div className="flex justify-center py-2">
              <div className="flex space-x-1">
                <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '600ms' }}></div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AgentSteps; 