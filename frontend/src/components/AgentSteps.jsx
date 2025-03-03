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
  return (
    <div className="bg-white rounded-lg shadow-md p-4 h-full overflow-auto">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">Agent Processing Steps</h3>
      
      {status && (
        <div className="mb-4">
          <div className="flex items-center">
            <div className={`h-3 w-3 rounded-full mr-2 ${
              status === 'starting' ? 'bg-blue-500 animate-pulse' :
              status === 'complete' ? 'bg-green-500' :
              status === 'error' ? 'bg-red-500' : 'bg-gray-500'
            }`} />
            <span className="font-medium text-gray-700">
              Status: {typeof status === 'string' ? status.charAt(0).toUpperCase() + status.slice(1) : String(status)}
            </span>
          </div>
        </div>
      )}
      
      {steps.length === 0 ? (
        <div className="text-gray-500 italic">No steps recorded yet</div>
      ) : (
        <div className="space-y-3">
          {steps.map((step, index) => (
            <div 
              key={index}
              className={`p-3 rounded-md border ${
                currentStep === step.node ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
            >
              <div className="flex items-center mb-1">
                <div className={`h-2 w-2 rounded-full mr-2 ${
                  index < steps.indexOf(steps.find(s => s.node === currentStep)) ? 'bg-green-500' :
                  index === steps.indexOf(steps.find(s => s.node === currentStep)) ? 'bg-blue-500 animate-pulse' :
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
          ))}
        </div>
      )}
    </div>
  );
};

export default AgentSteps; 