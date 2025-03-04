import React, { useState, useEffect, useRef } from 'react';
import ChatInterface from './components/ChatInterface';
import AgentState from './components/AgentState';
import AgentSteps from './components/AgentSteps';
import ConnectionStatus from './components/ConnectionStatus';
import { 
  initializeCoreAgent, 
  sendMessageToCore, 
  generateAgent,
  sendMessageToAgent,
  streamMessageToCore,
  streamGenerateAgent,
  streamMessageToAgent
} from './services/agentService';

// Custom hook for managing agent state
function useAgentState() {
  const [messages, setMessages] = useState([]);
  const [state, setState] = useState(null);
  const [steps, setSteps] = useState([]);
  const [currentStep, setCurrentStep] = useState(null);
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const streamRef = useRef(null);

  // Helper to add a message to the chat
  const addMessage = (role, content) => {
    setMessages(prev => [...prev, { role, content }]);
  };

  // Reset stream state - but keep steps history
  const resetStreamState = () => {
    // We're not clearing steps anymore
    // setSteps([]);
    setCurrentStep(null);
    setStatus('');
    setError(null);
  };

  // Clear steps explicitly when needed
  const clearSteps = () => {
    setSteps([]);
    setCurrentStep(null);
  };

  // Close existing stream if any
  const closeStream = () => {
    if (streamRef.current) {
      streamRef.current.close();
      streamRef.current = null;
    }
  };

  // Standard callbacks for streaming
  const getStreamCallbacks = (onCompleteCallback, agentType = 'core') => ({
    onStep: (data) => {
      console.log(`Received step data for ${agentType}:`, data);
      
      // Normalize step data structure
      const normalizedStep = {
        id: data.id || data.node || `step-${Date.now()}`,
        name: data.node || 'Step',
        description: typeof data.updates === 'string' ? data.updates : null,
        input: data.input || null,
        output: data.output || null,
        metadata: data.updates && typeof data.updates === 'object' ? data.updates : null,
        timestamp: data.timestamp ? new Date(data.timestamp * 1000).toISOString() : new Date().toISOString(),
        agentType: agentType
      };
      
      console.log('Normalized step:', normalizedStep);
      
      setSteps(prev => {
        // Check if step already exists
        const stepExists = prev.some(step => step.id === normalizedStep.id);
        if (stepExists) {
          // Update existing step
          return prev.map(step => 
            step.id === normalizedStep.id ? { ...step, ...normalizedStep } : step
          );
        } else {
          // Add new step
          return [...prev, normalizedStep];
        }
      });
      
      setCurrentStep(normalizedStep.id);
      setStatus('processing');
    },
    onState: (data) => {
      setState(data);
    },
    onComplete: (data) => {
      setStatus('complete');
      setLoading(false);
      if (onCompleteCallback) {
        onCompleteCallback(data);
      }
    },
    onError: (data) => {
      console.error('Stream error:', data);
      setStatus('error');
      setLoading(false);
      setError(data.error || 'Unknown error occurred');
    }
  });

  return {
    messages,
    setMessages,
    state,
    setState,
    steps,
    setSteps,
    currentStep,
    setCurrentStep,
    loading,
    setLoading,
    error,
    setError,
    status,
    setStatus,
    streamRef,
    addMessage,
    resetStreamState,
    clearSteps,
    closeStream,
    getStreamCallbacks
  };
}

function App() {
  // Core agent state
  const core = useAgentState();
  
  // Generated agent state
  const [hasGeneratedAgent, setHasGeneratedAgent] = useState(false);
  const [generatedAgentId, setGeneratedAgentId] = useState(null);
  const generatedAgent = useAgentState();
  
  // Global application state
  const [appError, setAppError] = useState(null);
  const [isFirstVisit, setIsFirstVisit] = useState(true);
  const [activeTab, setActiveTab] = useState('core'); // 'core' or 'generated'
  const [showSidebar, setShowSidebar] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [activeAgent, setActiveAgent] = useState('core'); // 'core' or 'generated'
  
  // Combined steps from both agents
  const [allSteps, setAllSteps] = useState([]);
  
  // Update combined steps when either agent's steps change
  useEffect(() => {
    setAllSteps([...core.steps, ...generatedAgent.steps]);
  }, [core.steps, generatedAgent.steps]);

  // Initialize core agent on mount
  useEffect(() => {
    const initialize = async () => {
      try {
        setAppError(null);
        await initializeCoreAgent();
        console.log('Core agent initialized');
        setConnectionStatus('connected');
        
        // Check if this is the first visit
        const hasVisitedBefore = localStorage.getItem('hasVisitedBefore');
        if (!hasVisitedBefore) {
          setIsFirstVisit(true);
          localStorage.setItem('hasVisitedBefore', 'true');
        } else {
          setIsFirstVisit(false);
        }
      } catch (error) {
        console.error('Failed to initialize core agent:', error);
        setAppError('Failed to initialize core agent. Please make sure the backend server is running.');
        setConnectionStatus('disconnected');
      }
    };
    
    initialize();
    
    // Clean up streams on unmount
    return () => {
      core.closeStream();
      generatedAgent.closeStream();
    };
  }, []);

  // Function to retry initialization
  const retryInitialization = () => {
    const initialize = async () => {
      try {
        setAppError(null);
        await initializeCoreAgent();
        console.log('Core agent initialized');
        setConnectionStatus('connected');
      } catch (error) {
        console.error('Failed to initialize core agent:', error);
        setAppError('Failed to initialize core agent. Please make sure the backend server is running.');
        setConnectionStatus('disconnected');
      }
    };
    
    initialize();
  };

  // Send message to core agent with streaming
  const handleSendToCore = async (message) => {
    try {
      // Reset any previous errors
      core.setError(null);
      setAppError(null);
      
      // Add user message to the conversation
      core.addMessage('user', message);
      
      // Set loading state
      core.setLoading(true);
      
      // Reset stream state but don't clear steps
      core.resetStreamState();
      
      // Set active agent to core
      setActiveAgent('core');
      
      // Close any existing stream
      core.closeStream();
      
      // Start streaming
      core.streamRef.current = streamMessageToCore(message, core.getStreamCallbacks((data) => {
        // Add the agent's response to the conversation
        core.addMessage('assistant', data.message);
      }, 'core'));
    } catch (error) {
      console.error('Error sending message to core:', error);
      core.setLoading(false);
      core.setError('Failed to send message. Please try again.');
    }
  };

  // Generate agent from core with streaming
  const handleGenerateAgent = async () => {
    try {
      // Reset any previous errors
      generatedAgent.setError(null);
      setAppError(null);
      
      // Set loading state
      generatedAgent.setLoading(true);
      
      // Reset stream state but don't clear steps
      generatedAgent.resetStreamState();
      
      // Set active agent to generated
      setActiveAgent('generated');
      
      // Close any existing stream
      generatedAgent.closeStream();
      
      // Start streaming
      generatedAgent.streamRef.current = streamGenerateAgent(generatedAgent.getStreamCallbacks((data) => {
        // Set generated agent ID
        setGeneratedAgentId(data.agent_id);
        setHasGeneratedAgent(true);
        
        // Add initial message
        generatedAgent.setMessages([{ role: 'assistant', content: data.message }]);
        
        // Switch to generated agent tab
        setActiveTab('generated');
      }, 'generated'));
    } catch (error) {
      console.error('Error generating agent:', error);
      generatedAgent.setLoading(false);
      generatedAgent.setError('Failed to generate agent. Please try again.');
    }
  };

  // Send message to generated agent with streaming
  const handleSendToGeneratedAgent = async (message) => {
    if (!generatedAgentId) {
      generatedAgent.setError('No agent has been generated yet.');
      return;
    }
    
    try {
      // Reset any previous errors
      generatedAgent.setError(null);
      setAppError(null);
      
      // Add user message to the conversation
      generatedAgent.addMessage('user', message);
      
      // Set loading state
      generatedAgent.setLoading(true);
      
      // Reset stream state but don't clear steps
      generatedAgent.resetStreamState();
      
      // Set active agent to generated
      setActiveAgent('generated');
      
      // Close any existing stream
      generatedAgent.closeStream();
      
      // Start streaming
      generatedAgent.streamRef.current = streamMessageToAgent(generatedAgentId, message, generatedAgent.getStreamCallbacks((data) => {
        // Add the agent's response to the conversation
        generatedAgent.addMessage('assistant', data.message);
      }, 'generated'));
    } catch (error) {
      console.error('Error sending message to generated agent:', error);
      generatedAgent.setLoading(false);
      generatedAgent.setError('Failed to send message. Please try again.');
    }
  };

  // Close welcome modal
  const handleCloseWelcome = () => {
    setIsFirstVisit(false);
  };

  // Toggle sidebar visibility
  const toggleSidebar = () => {
    setShowSidebar(!showSidebar);
  };

  // Get the active agent's state and steps
  const getActiveAgentData = () => {
    if (activeAgent === 'core') {
      return {
        state: core.state,
        steps: core.steps,
        currentStep: core.currentStep,
        status: core.status,
        loading: core.loading
      };
    } else {
      return {
        state: generatedAgent.state,
        steps: generatedAgent.steps,
        currentStep: generatedAgent.currentStep,
        status: generatedAgent.status,
        loading: generatedAgent.loading
      };
    }
  };

  // If there's a global app error, show an error message
  if (appError) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full">
          <div className="flex items-center justify-center mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h1 className="text-xl font-bold text-center mb-2">Connection Error</h1>
          <p className="text-gray-700 text-center mb-4">{appError}</p>
          <div className="flex justify-center">
            <button 
              onClick={retryInitialization}
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-opacity-50 transition"
            >
              Retry Connection
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Welcome modal for first-time users
  const WelcomeModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 animate-fade-in">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">Welcome to Chameleon AI Agent</h2>
        <p className="text-gray-600 mb-4">
          This application allows you to interact with AI agents. Here's how to use it:
        </p>
        <ol className="list-decimal pl-5 mb-6 space-y-2 text-gray-600">
          <li>Start by chatting with the <strong>Core Agent</strong> to define what you want to create</li>
          <li>Once you've established your requirements, click <strong>Generate Agent</strong></li>
          <li>Interact with your newly created <strong>Generated Agent</strong> that's built to your specifications</li>
        </ol>
        <button 
          onClick={handleCloseWelcome}
          className="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded transition duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-opacity-50"
        >
          Get Started
        </button>
      </div>
    </div>
  );

  // Status indicator component
  const StatusIndicator = () => (
    <div className="flex items-center">
      <div className={`h-2 w-2 rounded-full mr-2 ${
        connectionStatus === 'connected' ? 'bg-emerald-500' : 'bg-red-500'
      }`}></div>
      <span className="text-sm text-gray-600">
        {connectionStatus === 'connected' ? 'Connected' : 'Disconnected'}
      </span>
    </div>
  );

  // Get active agent data
  const activeAgentData = getActiveAgentData();

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Welcome modal for first-time users */}
      {isFirstVisit && <WelcomeModal />}
      
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-indigo-700">Chameleon AI Agent</h1>
              <div className="ml-4">
                <StatusIndicator />
              </div>
            </div>
            <div className="hidden md:flex space-x-4">
              <button 
                onClick={toggleSidebar}
                className="text-gray-600 hover:text-gray-900 focus:outline-none"
              >
                {showSidebar ? (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </header>
      
      {/* Mobile tabs - only visible on small screens */}
      <div className="md:hidden bg-white border-b border-gray-200">
        <div className="flex">
          <button
            onClick={() => setActiveTab('core')}
            className={`flex-1 py-3 text-center font-medium ${
              activeTab === 'core' 
                ? 'text-indigo-600 border-b-2 border-indigo-500' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Core Agent
          </button>
          <button
            onClick={() => setActiveTab('generated')}
            className={`flex-1 py-3 text-center font-medium ${
              activeTab === 'generated' 
                ? 'text-indigo-600 border-b-2 border-indigo-500' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
            disabled={!hasGeneratedAgent}
          >
            Generated Agent
          </button>
          <button
            onClick={toggleSidebar}
            className="px-4 text-gray-500 hover:text-gray-700"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
      
      {/* Main content */}
      <div className="flex-1 flex flex-col md:flex-row">
        {/* Core Agent - visible on desktop or when selected on mobile */}
        <div className={`flex-1 flex flex-col ${
          activeTab === 'core' || window.innerWidth >= 768 ? 'block' : 'hidden md:block'
        }`}>
          <div className="bg-white p-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-800">Core Agent</h2>
          </div>
          
          <div className="flex-1 overflow-hidden flex flex-col">
            <ChatInterface 
              messages={core.messages}
              onSendMessage={handleSendToCore}
              loading={core.loading}
              error={core.error}
            />
          </div>
        </div>
        
        {/* Generated Agent - visible on desktop or when selected on mobile */}
        <div className={`flex-1 flex flex-col ${
          activeTab === 'generated' || window.innerWidth >= 768 ? 'block' : 'hidden md:block'
        }`}>
          <div className="bg-white p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-800">
              Generated Agent
            </h2>
          </div>
          
          <div className="flex-1 overflow-hidden flex flex-col">
            {hasGeneratedAgent ? (
              <ChatInterface 
                messages={generatedAgent.messages}
                onSendMessage={handleSendToGeneratedAgent}
                loading={generatedAgent.loading}
                error={generatedAgent.error}
              />
            ) : (
              <div className="flex-1 flex items-center justify-center p-4 bg-gray-50">
                <div className="text-center max-w-md p-6 bg-white rounded-lg shadow-sm">
                  <div className="bg-indigo-50 rounded-full p-4 inline-block mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Agent Generated Yet</h3>
                  <p className="text-gray-500 mb-4">Chat with the Core Agent to define your requirements, then generate a specialized agent.</p>
                  <button
                    onClick={handleGenerateAgent}
                    disabled={generatedAgent.loading || core.loading}
                    className={`py-2 px-4 rounded-md font-medium text-sm mb-3 ${
                      generatedAgent.loading || core.loading
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm hover:shadow transition-all'
                    }`}
                  >
                    {generatedAgent.loading ? 'Generating...' : 'Generate Agent'}
                  </button>
                  <div>
                    <button
                      onClick={() => setActiveTab('core')}
                      className="text-indigo-600 hover:text-indigo-700 font-medium"
                    >
                      Go to Core Agent →
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* Sidebar - collapsible on all screen sizes */}
        <div className={`${
          showSidebar ? 'block' : 'hidden'
        } w-full md:w-80 bg-white border-l border-gray-200 overflow-auto transition-all duration-300 ease-in-out`}>
          <div className="sticky top-0 bg-white z-10">
            <div className="p-4 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-800">Processing Steps</h2>
              <button 
                onClick={toggleSidebar}
                className="text-gray-500 hover:text-gray-700 focus:outline-none"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          
          <div className="p-4">
            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-md font-medium text-gray-700">Core Agent Steps</h3>
                <span className="text-xs text-gray-500">{core.steps.length} steps</span>
              </div>
              <AgentSteps 
                steps={core.steps}
                currentStep={activeAgent === 'core' ? core.currentStep : null}
                status={activeAgent === 'core' ? core.status : 'complete'}
              />
            </div>
            
            {hasGeneratedAgent && (
              <div className="mb-6">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-md font-medium text-gray-700">Generated Agent Steps</h3>
                  <span className="text-xs text-gray-500">{generatedAgent.steps.length} steps</span>
                </div>
                <AgentSteps 
                  steps={generatedAgent.steps}
                  currentStep={activeAgent === 'generated' ? generatedAgent.currentStep : null}
                  status={activeAgent === 'generated' ? generatedAgent.status : 'complete'}
                />
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Mobile action button to show sidebar - only visible when sidebar is hidden */}
      {!showSidebar && (
        <button
          onClick={toggleSidebar}
          className="md:hidden fixed bottom-4 right-4 bg-indigo-600 text-white p-3 rounded-full shadow-lg z-20"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>
      )}
    </div>
  );
}

export default App; 