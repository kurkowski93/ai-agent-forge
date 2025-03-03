import React, { useState, useEffect, useRef } from 'react';
import ChatInterface from './components/ChatInterface';
import AgentState from './components/AgentState';
import AgentSteps from './components/AgentSteps';
import { 
  initializeCoreAgent, 
  sendMessageToCore, 
  generateAgent,
  sendMessageToAgent,
  streamMessageToCore,
  streamGenerateAgent,
  streamMessageToAgent
} from './services/agentService';

function App() {
  // Core agent state
  const [coreMessages, setCoreMessages] = useState([]);
  const [coreState, setCoreState] = useState(null);
  const [coreLoading, setCoreLoading] = useState(false);
  
  // Core agent streaming state
  const [coreSteps, setCoreSteps] = useState([]);
  const [currentCoreStep, setCurrentCoreStep] = useState(null);
  const [coreStatus, setCoreStatus] = useState(null);
  const coreStreamRef = useRef(null);
  
  // Generated agent state
  const [hasGeneratedAgent, setHasGeneratedAgent] = useState(false);
  const [generatedAgentId, setGeneratedAgentId] = useState(null);
  const [generatedAgentMessages, setGeneratedAgentMessages] = useState([]);
  const [generatedAgentLoading, setGeneratedAgentLoading] = useState(false);
  
  // Generated agent streaming state
  const [generatedAgentSteps, setGeneratedAgentSteps] = useState([]);
  const [currentGeneratedAgentStep, setCurrentGeneratedAgentStep] = useState(null);
  const [generatedAgentStatus, setGeneratedAgentStatus] = useState(null);
  const generatedAgentStreamRef = useRef(null);

  // Initialize core agent on mount
  useEffect(() => {
    const initialize = async () => {
      try {
        await initializeCoreAgent();
        console.log('Core agent initialized');
      } catch (error) {
        console.error('Failed to initialize core agent:', error);
      }
    };
    
    initialize();
    
    // Clean up streams on unmount
    return () => {
      if (coreStreamRef.current) {
        coreStreamRef.current.close();
      }
      if (generatedAgentStreamRef.current) {
        generatedAgentStreamRef.current.close();
      }
    };
  }, []);

  // Send message to core agent with streaming
  const handleSendToCore = async (message) => {
    try {
      setCoreLoading(true);
      setCoreStatus('starting');
      setCoreSteps([]);
      setCurrentCoreStep(null);
      
      // Add user message to UI
      setCoreMessages(prev => [...prev, { role: 'user', content: message }]);
      
      // Close existing stream if any
      if (coreStreamRef.current) {
        coreStreamRef.current.close();
      }
      
      // Start a new stream
      coreStreamRef.current = streamMessageToCore(message, {
        onStep: (data) => {
          console.log('Step:', data);
          if (data && data.node) {
            setCoreSteps(prev => {
              // Unikaj duplikatów, dodaj tylko jeśli node jest unikalny
              if (!prev.find(step => step.node === data.node)) {
                return [...prev, data];
              }
              return prev;
            });
            setCurrentCoreStep(data.node);
          }
        },
        onState: (data) => {
          console.log('State:', data);
          if (data && data.status) {
            setCoreStatus(data.status);
          }
        },
        onComplete: (data) => {
          console.log('Complete:', data);
          setCoreStatus('complete');
          setCurrentCoreStep(null);
          
          // Add response to UI
          if (data && data.message) {
            setCoreMessages(prev => [...prev, { role: 'assistant', content: data.message }]);
          } else {
            setCoreMessages(prev => [...prev, { 
              role: 'assistant', 
              content: 'Otrzymano odpowiedź od agenta, ale brakuje treści wiadomości.'
            }]);
          }
          
          // Update state
          if (data && data.state) {
            setCoreState(data.state);
          }
          setCoreLoading(false);
        },
        onError: (error) => {
          console.error('Stream error:', error);
          setCoreStatus('error');
          setCoreLoading(false);
          setCoreMessages(prev => [...prev, { 
            role: 'assistant', 
            content: `Błąd: ${error.error || 'Nie udało się komunikować z agentem podstawowym.'}`
          }]);
        }
      });
    } catch (error) {
      console.error('Error communicating with core agent:', error);
      setCoreMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Błąd: Nie udało się komunikować z agentem podstawowym.' 
      }]);
      setCoreLoading(false);
      setCoreStatus('error');
    }
  };

  // Generate agent from core configuration with streaming
  const handleGenerateAgent = async () => {
    try {
      setCoreLoading(true);
      setGeneratedAgentStatus('starting');
      setGeneratedAgentSteps([]);
      setCurrentGeneratedAgentStep(null);
      
      // Close existing stream if any
      if (generatedAgentStreamRef.current) {
        generatedAgentStreamRef.current.close();
      }
      
      // Start a new stream
      generatedAgentStreamRef.current = streamGenerateAgent({
        onStep: (data) => {
          console.log('Step:', data);
          if (data && (data.step || data.node)) {
            setGeneratedAgentSteps(prev => {
              // Avoid duplicates
              const stepKey = data.step || data.node;
              if (!prev.find(step => (step.step === stepKey || step.node === stepKey))) {
                return [...prev, data];
              }
              return prev;
            });
            setCurrentGeneratedAgentStep(data.step || data.node);
          }
        },
        onState: (data) => {
          console.log('State:', data);
          if (data && data.status) {
            setGeneratedAgentStatus(data.status);
          }
        },
        onComplete: (data) => {
          console.log('Complete:', data);
          setGeneratedAgentStatus('complete');
          setCurrentGeneratedAgentStep(null);
          
          if (data && data.agent_id) {
            // Update state
            setGeneratedAgentId(data.agent_id);
            setHasGeneratedAgent(true);
            
            // Add message to generated agent chat
            setGeneratedAgentMessages([
              { role: 'assistant', content: 'Witaj! Jestem wygenerowanym agentem. W czym mogę pomóc?' }
            ]);
            
            // Add confirmation to core agent chat
            setCoreMessages(prev => [...prev, { 
              role: 'system', 
              content: `Agent wygenerowany z ID: ${data.agent_id}` 
            }]);
          } else {
            setCoreMessages(prev => [...prev, { 
              role: 'system', 
              content: 'Agent został wygenerowany, ale brakuje identyfikatora agenta.'
            }]);
          }
          
          setCoreLoading(false);
        },
        onError: (error) => {
          console.error('Stream error:', error);
          setGeneratedAgentStatus('error');
          setCoreLoading(false);
          setCoreMessages(prev => [...prev, { 
            role: 'system', 
            content: `Błąd: ${error.error || 'Nie udało się wygenerować agenta. Upewnij się, że konfiguracja agenta jest gotowa.'}`
          }]);
        }
      });
    } catch (error) {
      console.error('Error generating agent:', error);
      setCoreMessages(prev => [...prev, { 
        role: 'system', 
        content: 'Błąd: Nie udało się wygenerować agenta. Upewnij się, że konfiguracja agenta jest gotowa.' 
      }]);
      setCoreLoading(false);
      setGeneratedAgentStatus('error');
    }
  };

  // Send message to generated agent with streaming
  const handleSendToGeneratedAgent = async (message) => {
    try {
      setGeneratedAgentLoading(true);
      setGeneratedAgentStatus('starting');
      setGeneratedAgentSteps([]);
      setCurrentGeneratedAgentStep(null);
      
      // Add user message to UI
      setGeneratedAgentMessages(prev => [...prev, { role: 'user', content: message }]);
      
      // Close existing stream if any
      if (generatedAgentStreamRef.current) {
        generatedAgentStreamRef.current.close();
      }
      
      // Start a new stream
      generatedAgentStreamRef.current = streamMessageToAgent(generatedAgentId, message, {
        onStep: (data) => {
          console.log('Step:', data);
          if (data && data.node) {
            setGeneratedAgentSteps(prev => {
              // Avoid duplicates
              if (!prev.find(step => step.node === data.node)) {
                return [...prev, data];
              }
              return prev;
            });
            setCurrentGeneratedAgentStep(data.node);
          }
        },
        onState: (data) => {
          console.log('State:', data);
          if (data && data.status) {
            setGeneratedAgentStatus(data.status);
          }
        },
        onComplete: (data) => {
          console.log('Complete:', data);
          setGeneratedAgentStatus('complete');
          setCurrentGeneratedAgentStep(null);
          
          // Add response to UI
          if (data && data.message) {
            setGeneratedAgentMessages(prev => [...prev, { role: 'assistant', content: data.message }]);
          } else {
            setGeneratedAgentMessages(prev => [...prev, { 
              role: 'assistant', 
              content: 'Otrzymano odpowiedź od agenta, ale brakuje treści wiadomości.'
            }]);
          }
          setGeneratedAgentLoading(false);
        },
        onError: (error) => {
          console.error('Stream error:', error);
          setGeneratedAgentStatus('error');
          setGeneratedAgentLoading(false);
          setGeneratedAgentMessages(prev => [...prev, { 
            role: 'assistant', 
            content: `Błąd: ${error.error || 'Nie udało się komunikować z agentem.'}`
          }]);
        }
      });
    } catch (error) {
      console.error('Error communicating with generated agent:', error);
      setGeneratedAgentMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Błąd: Nie udało się komunikować z agentem.' 
      }]);
      setGeneratedAgentLoading(false);
      setGeneratedAgentStatus('error');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-indigo-50 to-white">
      <header className="py-8 px-6 bg-gradient-to-r from-blue-700 to-indigo-800 text-white shadow-lg">
        <div className="container mx-auto">
          <h1 className="text-4xl font-extrabold tracking-tight">AgentForge</h1>
          <p className="text-lg text-blue-100 mt-2">Build and interact with your AI agents</p>
        </div>
      </header>
      
      <main className="container mx-auto px-4 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Left column - Core Agent */}
          <div className="flex-1 flex flex-col">
            <div className="mb-6 flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-800">Core Agent</h2>
              {coreState?.has_agent_config && (
                <button
                  className="px-5 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 
                  transition shadow-md font-medium flex items-center gap-2"
                  onClick={handleGenerateAgent}
                  disabled={coreLoading || hasGeneratedAgent}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clipRule="evenodd" />
                  </svg>
                  Generate Agent
                </button>
              )}
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Chat Interface */}
              <div className="h-[600px] col-span-1">
                <ChatInterface
                  title="Core Agent Chat"
                  messages={coreMessages}
                  onSendMessage={handleSendToCore}
                  loading={coreLoading}
                />
              </div>
              
              {/* Agent State */}
              <div className="h-[600px] col-span-1">
                <AgentState state={coreState} />
              </div>
              
              {/* Agent Steps */}
              <div className="h-[600px] col-span-1">
                <AgentSteps 
                  steps={coreSteps} 
                  currentStep={currentCoreStep}
                  status={coreStatus}
                />
              </div>
            </div>
          </div>
          
          {/* Right column - Generated Agent (conditionally rendered) */}
          {hasGeneratedAgent && (
            <div className="flex-1 flex flex-col">
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-800">Generated Agent</h2>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Chat Interface */}
                <div className="h-[600px]">
                  <ChatInterface
                    title="Generated Agent Chat"
                    messages={generatedAgentMessages}
                    onSendMessage={handleSendToGeneratedAgent}
                    loading={generatedAgentLoading}
                  />
                </div>
                
                {/* Agent Steps */}
                <div className="h-[600px]">
                  <AgentSteps 
                    steps={generatedAgentSteps} 
                    currentStep={currentGeneratedAgentStep}
                    status={generatedAgentStatus}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App; 