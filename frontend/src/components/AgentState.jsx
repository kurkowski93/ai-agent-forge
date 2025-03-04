import React, { useState } from 'react';

/**
 * Empty state component when no state is available
 * @returns {JSX.Element} - Empty state component
 */
const EmptyState = () => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex flex-col items-center justify-center text-center">
    <div className="bg-gray-50 rounded-full p-4 mb-4">
      <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    </div>
    <h3 className="text-lg font-medium text-gray-900 mb-2">No State Available</h3>
    <p className="text-gray-500 max-w-sm">
      Chat with the agent to initialize its state. The agent's internal state will be displayed here once it's available.
    </p>
  </div>
);

/**
 * Collapsible section component for displaying a section of the agent state
 * @param {string} title - Section title
 * @param {object} data - Section data
 * @param {boolean} [badge] - Whether to show a badge
 * @param {string} [badgeText] - Text for the badge
 * @param {boolean} [defaultExpanded=true] - Whether the section is expanded by default
 * @returns {JSX.Element} - Collapsible state section component
 */
const CollapsibleSection = ({ title, data, badge, badgeText, defaultExpanded = true }) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  
  // Format JSON data with syntax highlighting
  const formatJSON = (data) => {
    if (typeof data === 'string') return data;
    
    try {
      // Convert to string with pretty formatting
      const jsonString = JSON.stringify(data, null, 2);
      
      // Simple syntax highlighting
      return jsonString
        .replace(/"([^"]+)":/g, '<span class="text-purple-600">"$1"</span>:')
        .replace(/"([^"]+)"/g, '<span class="text-green-600">"$1"</span>')
        .replace(/\b(true|false|null)\b/g, '<span class="text-blue-600">$1</span>')
        .replace(/\b(\d+)\b/g, '<span class="text-amber-600">$1</span>');
    } catch (e) {
      return String(data);
    }
  };
  
  return (
    <div className="mb-4 bg-white rounded-lg border border-gray-200 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 border-b border-gray-200 focus:outline-none hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center">
          <h4 className="font-medium text-gray-700">{title}</h4>
          {badge && (
            <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">
              {badgeText}
            </span>
          )}
        </div>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className={`h-5 w-5 text-gray-500 transition-transform ${isExpanded ? 'transform rotate-180' : ''}`}
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>
      
      {isExpanded && (
        <div className="p-4">
          <div className="bg-gray-50 rounded-md border border-gray-200 p-3 max-h-64 overflow-auto">
            <pre 
              className="text-sm font-mono whitespace-pre-wrap text-gray-800"
              dangerouslySetInnerHTML={{ __html: formatJSON(data) }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Search input component
 * @param {string} value - Current search value
 * @param {Function} onChange - Function to call when search value changes
 * @returns {JSX.Element} - Search input component
 */
const SearchInput = ({ value, onChange }) => (
  <div className="relative mb-4">
    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    </div>
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Search in state..."
      className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
    />
    {value && (
      <button
        onClick={() => onChange('')}
        className="absolute inset-y-0 right-0 pr-3 flex items-center"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400 hover:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    )}
  </div>
);

/**
 * Agent state component
 * @param {object} state - Agent state
 * @returns {JSX.Element} - Agent state component
 */
const AgentState = ({ state }) => {
  const [searchTerm, setSearchTerm] = useState('');
  
  // Debug state
  console.log("AgentState received state:", state);
  
  if (!state) {
    return <EmptyState />;
  }
  
  // Filter state based on search term
  const filterState = (data, term) => {
    if (!term) return true;
    
    const jsonString = JSON.stringify(data).toLowerCase();
    return jsonString.includes(term.toLowerCase());
  };
  
  // Extract state data from different possible formats
  const extractStateData = () => {
    // If state is already in the expected format
    if (state.planned_step || state.agent_config) {
      return {
        plannedStep: state.planned_step,
        agentConfig: state.agent_config,
        otherState: Object.fromEntries(
          Object.entries(state.agent_state || {}).filter(
            ([key]) => key !== 'planned_step' && key !== 'agent_config'
          )
        ),
        hasAgentConfig: state.has_agent_config
      };
    }
    
    // If state is wrapped in agent_state
    if (state.agent_state) {
      const agentState = state.agent_state;
      return {
        plannedStep: agentState.planned_step,
        agentConfig: agentState.agent_config,
        otherState: Object.fromEntries(
          Object.entries(agentState).filter(
            ([key]) => key !== 'planned_step' && key !== 'agent_config'
          )
        ),
        hasAgentConfig: state.has_agent_config || agentState.has_agent_config
      };
    }
    
    // If state is the entire object
    return {
      plannedStep: state.planned_step,
      agentConfig: state.agent_config,
      otherState: Object.fromEntries(
        Object.entries(state).filter(
          ([key]) => key !== 'planned_step' && key !== 'agent_config' && key !== 'has_agent_config'
        )
      ),
      hasAgentConfig: state.has_agent_config
    };
  };
  
  const { plannedStep, agentConfig, otherState, hasAgentConfig } = extractStateData();
  
  // Check if sections should be displayed based on search
  const showPlannedStep = plannedStep && (!searchTerm || filterState(plannedStep, searchTerm));
  const showAgentConfig = agentConfig && (!searchTerm || filterState(agentConfig, searchTerm));
  const showOtherState = Object.keys(otherState || {}).length > 0 && 
    (!searchTerm || filterState(otherState, searchTerm));
  
  // If nothing to show, display the entire state
  const showFullState = !showPlannedStep && !showAgentConfig && !showOtherState && state;
  
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
        <h3 className="text-sm font-medium text-gray-700">Agent State</h3>
      </div>
      
      <div className="p-4">
        <SearchInput value={searchTerm} onChange={setSearchTerm} />
        
        {!showPlannedStep && !showAgentConfig && !showOtherState && !showFullState && (
          <div className="text-center py-8 text-gray-500">
            No results found for "{searchTerm}"
          </div>
        )}
        
        {showPlannedStep && (
          <CollapsibleSection 
            title="Planned Step" 
            data={plannedStep} 
          />
        )}
        
        {showAgentConfig && (
          <CollapsibleSection 
            title="Agent Config" 
            data={agentConfig}
            badge={hasAgentConfig}
            badgeText="Ready"
          />
        )}
        
        {showOtherState && (
          <CollapsibleSection 
            title="Additional State" 
            data={otherState}
            defaultExpanded={false}
          />
        )}
        
        {showFullState && (
          <CollapsibleSection 
            title="Full State" 
            data={state}
            defaultExpanded={true}
          />
        )}
      </div>
    </div>
  );
};

export default AgentState; 