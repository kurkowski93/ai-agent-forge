import React from 'react';

const AgentState = ({ state }) => {
  if (!state) {
    return (
      <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6 h-full flex flex-col items-center justify-center">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        <div className="text-lg text-gray-500">No state available</div>
        <p className="text-gray-400 text-sm mt-2 text-center">Chat with the agent to initialize its state</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 h-full overflow-hidden flex flex-col">
      <div className="px-6 py-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white">
        <h3 className="text-xl font-bold tracking-wide">Agent State</h3>
      </div>
      
      <div className="flex-1 overflow-y-auto p-6">
        {/* Agent Blueprint */}
        <div className="mb-6">
          <h4 className="text-lg font-semibold text-gray-800 mb-3">Blueprint:</h4>
          <div className="bg-gray-50 rounded-lg border border-gray-200 p-4 whitespace-pre-wrap overflow-x-auto shadow-sm">
            {state.agent_blueprint || "No blueprint available"}
          </div>
        </div>
        
        {/* Planned Step */}
        <div className="mb-6">
          <h4 className="text-lg font-semibold text-gray-800 mb-3">Planned Step:</h4>
          <div className="bg-gray-50 rounded-lg border border-gray-200 p-4 shadow-sm font-mono text-gray-800">
            {state.planned_step || "None"}
          </div>
        </div>
        
        {/* Config Status */}
        <div className="mb-6">
          <h4 className="text-lg font-semibold text-gray-800 mb-3">Agent Config:</h4>
          <div className={`inline-flex items-center px-4 py-2 rounded-full ${
            state.has_agent_config 
              ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' 
              : 'bg-amber-100 text-amber-800 border border-amber-200'
          }`}>
            <div className={`w-3 h-3 rounded-full mr-2 ${
              state.has_agent_config ? 'bg-emerald-500' : 'bg-amber-500'
            }`}></div>
            {state.has_agent_config ? "Ready" : "Not Ready"}
          </div>
        </div>
        
        {/* Agent Config JSON - new section */}
        {state.has_agent_config && state.agent_config && (
          <div className="mb-6">
            <h4 className="text-lg font-semibold text-gray-800 mb-3">Config JSON:</h4>
            <div className="bg-gray-50 rounded-lg border border-gray-200 p-4 shadow-sm overflow-x-auto">
              <pre className="text-xs text-gray-800 font-mono whitespace-pre-wrap">
                {JSON.stringify(state.agent_config, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentState; 