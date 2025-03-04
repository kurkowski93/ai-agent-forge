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
    <div className="bg-white rounded-lg shadow-md h-[500px] overflow-auto">
      <div className="p-4 bg-slate-800 text-white rounded-t-lg">
        <h3 className="text-lg font-semibold">Agent State</h3>
      </div>
      
      <div className="p-4 overflow-auto flex-grow">
        {!state ? (
          <div className="text-gray-500 italic">No state available</div>
        ) : (
          <>
            {state.planned_step && (
              <div className="mb-4">
                <h4 className="font-semibold text-gray-700 mb-2">Planned Step:</h4>
                <div className="bg-slate-50 p-3 rounded-md border border-slate-200">
                  <code className="text-sm whitespace-pre-wrap">{typeof state.planned_step === 'string' ? state.planned_step : JSON.stringify(state.planned_step, null, 2)}</code>
                </div>
              </div>
            )}
            
            {state.agent_config && (
              <div className="mb-4">
                <div className="flex items-center mb-2">
                  <h4 className="font-semibold text-gray-700">Agent Config:</h4>
                  {state.has_agent_config && (
                    <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">Ready</span>
                  )}
                </div>
                <div className="bg-slate-50 p-3 rounded-md border border-slate-200 max-h-64 overflow-auto">
                  <code className="text-sm whitespace-pre-wrap">{JSON.stringify(state.agent_config, null, 2)}</code>
                </div>
              </div>
            )}
            
            {state.agent_state && Object.keys(state.agent_state).filter(key => key !== 'planned_step' && key !== 'agent_config').length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-700 mb-2">Config JSON:</h4>
                <div className="bg-slate-50 p-3 rounded-md border border-slate-200 max-h-64 overflow-auto">
                  <code className="text-sm whitespace-pre-wrap">{JSON.stringify(
                    Object.fromEntries(
                      Object.entries(state.agent_state).filter(([key]) => key !== 'planned_step' && key !== 'agent_config')
                    ), 
                    null, 
                    2
                  )}</code>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AgentState; 