import React, { useState, useRef, useEffect } from 'react';

/**
 * Error message component
 * @param {string} error - Error message to display
 * @returns {JSX.Element} - Error message component
 */
const ErrorMessage = ({ error }) => (
  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-4 flex items-start">
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
    </svg>
    <span className="text-sm">{error}</span>
  </div>
);

/**
 * Loading indicator component
 * @returns {JSX.Element} - Loading indicator
 */
const LoadingIndicator = () => (
  <div className="flex items-center space-x-2 p-3 rounded-lg max-w-[85%] bg-white border border-slate-200 animate-pulse">
    <div className="flex-shrink-0 h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center">
      <div className="h-5 w-5 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin"></div>
    </div>
    <div className="flex-1 space-y-2">
      <div className="h-2 bg-slate-200 rounded w-3/4"></div>
      <div className="h-2 bg-slate-200 rounded w-1/2"></div>
    </div>
  </div>
);

/**
 * Message time component
 * @param {Date} timestamp - Message timestamp
 * @returns {JSX.Element} - Time display
 */
const MessageTime = ({ timestamp = new Date() }) => (
  <div className="text-xs text-gray-400 mt-1">
    {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
  </div>
);

/**
 * User avatar component
 * @returns {JSX.Element} - User avatar
 */
const UserAvatar = () => (
  <div className="flex-shrink-0 h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center">
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-indigo-600" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
    </svg>
  </div>
);

/**
 * Assistant avatar component
 * @returns {JSX.Element} - Assistant avatar
 */
const AssistantAvatar = () => (
  <div className="flex-shrink-0 h-8 w-8 rounded-full bg-emerald-100 flex items-center justify-center">
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-emerald-600" viewBox="0 0 20 20" fill="currentColor">
      <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
      <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
    </svg>
  </div>
);

/**
 * System avatar component
 * @returns {JSX.Element} - System avatar
 */
const SystemAvatar = () => (
  <div className="flex-shrink-0 h-8 w-8 rounded-full bg-amber-100 flex items-center justify-center">
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-amber-600" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
    </svg>
  </div>
);

/**
 * Message component
 * @param {object} message - Message object
 * @param {string} message.role - Message role (user, assistant, system)
 * @param {string} message.content - Message content
 * @returns {JSX.Element} - Message component
 */
const Message = ({ message }) => {
  // Get the appropriate avatar based on message role
  const getAvatar = () => {
    switch (message.role) {
      case 'user':
        return <UserAvatar />;
      case 'assistant':
        return <AssistantAvatar />;
      case 'system':
        return <SystemAvatar />;
      default:
        return null;
    }
  };

  // Get the appropriate message style based on role
  const getMessageStyle = () => {
    switch (message.role) {
      case 'user':
        return 'bg-indigo-50 border border-indigo-100 text-gray-800';
      case 'assistant':
        return 'bg-white border border-gray-200 text-gray-800';
      case 'system':
        return 'bg-amber-50 border border-amber-100 text-gray-800';
      default:
        return 'bg-gray-50 border border-gray-200 text-gray-800';
    }
  };

  // Format code blocks in messages
  const formatContent = (content) => {
    // Simple regex to detect code blocks (text between triple backticks)
    const codeBlockRegex = /```([\s\S]*?)```/g;
    
    // Split the content by code blocks
    const parts = content.split(codeBlockRegex);
    
    if (parts.length === 1) {
      // No code blocks found, return the content as is
      return <p className="whitespace-pre-wrap">{content}</p>;
    }
    
    // Render parts with code blocks highlighted
    return parts.map((part, index) => {
      // Even indices are regular text, odd indices are code blocks
      if (index % 2 === 0) {
        return part ? <p key={index} className="whitespace-pre-wrap mb-2">{part}</p> : null;
      } else {
        return (
          <pre key={index} className="bg-gray-800 text-gray-100 p-3 rounded-md overflow-x-auto mb-2 text-sm">
            <code>{part}</code>
          </pre>
        );
      }
    });
  };

  return (
    <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
      {message.role !== 'user' && (
        <div className="mr-2 mt-1">
          {getAvatar()}
        </div>
      )}
      
      <div className={`rounded-lg p-3 max-w-[85%] shadow-sm ${getMessageStyle()}`}>
        <div className="text-sm">
          {formatContent(message.content)}
        </div>
        <MessageTime />
      </div>
      
      {message.role === 'user' && (
        <div className="ml-2 mt-1">
          {getAvatar()}
        </div>
      )}
    </div>
  );
};

/**
 * Empty chat state component
 * @returns {JSX.Element} - Empty state component
 */
const EmptyState = () => (
  <div className="flex flex-col items-center justify-center h-full p-6 text-center">
    <div className="bg-indigo-50 rounded-full p-4 mb-4">
      <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
      </svg>
    </div>
    <h3 className="text-lg font-medium text-gray-900 mb-2">Start a Conversation</h3>
    <p className="text-gray-500 max-w-sm">
      Send a message to begin interacting with the agent. Be specific about what you want to accomplish.
    </p>
  </div>
);

/**
 * Date divider component
 * @param {string} date - Date string to display
 * @returns {JSX.Element} - Date divider component
 */
const DateDivider = ({ date }) => (
  <div className="flex justify-center mb-4">
    <div className="bg-indigo-50 px-3 py-1 rounded-full text-xs text-indigo-600 font-medium shadow-sm border border-indigo-100">
      {date}
    </div>
  </div>
);

/**
 * Chat interface component
 * @param {string} title - Chat title
 * @param {Array} messages - Array of message objects
 * @param {Function} onSendMessage - Function to call when sending a message
 * @param {boolean} loading - Whether the chat is loading
 * @param {string} error - Error message to display
 * @returns {JSX.Element} - Chat interface component
 */
const ChatInterface = ({ title, messages, onSendMessage, loading, error }) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const messagesContainerRef = useRef(null);

  // Scroll to bottom when new messages come in
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Focus input when component mounts
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const handleSend = () => {
    if (inputValue.trim() && !loading) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevent default behavior (new line)
      handleSend();
    }
  };

  // Group messages by date
  const groupMessagesByDate = (messages) => {
    const groups = [];
    let currentDate = null;
    let currentGroup = [];

    messages.forEach((message) => {
      const messageDate = new Date().toLocaleDateString(); // Use actual message date when available
      
      if (messageDate !== currentDate) {
        if (currentGroup.length > 0) {
          groups.push({
            date: currentDate,
            messages: currentGroup
          });
        }
        currentDate = messageDate;
        currentGroup = [message];
      } else {
        currentGroup.push(message);
      }
    });

    if (currentGroup.length > 0) {
      groups.push({
        date: currentDate,
        messages: currentGroup
      });
    }

    return groups;
  };

  const messageGroups = groupMessagesByDate(messages);

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {title && (
        <div className="p-4 bg-indigo-600 text-white">
          <h3 className="text-lg font-semibold">{title}</h3>
        </div>
      )}
      
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4"
      >
        {error && <ErrorMessage error={error} />}
        
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          <div>
            {messageGroups.map((group, groupIndex) => (
              <div key={groupIndex} className="mb-6">
                <DateDivider date={group.date} />
                
                <div className="space-y-1">
                  {group.messages.map((message, messageIndex) => (
                    <Message key={messageIndex} message={message} />
                  ))}
                </div>
              </div>
            ))}
            
            {loading && <LoadingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
      
      <div className="border-t border-gray-200 p-3 bg-white">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <div className="relative flex-1">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a message..."
              className="w-full p-3 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none max-h-32"
              rows={1}
              disabled={loading}
              style={{ minHeight: '44px' }}
            />
            {inputValue.length > 0 && (
              <button
                type="button"
                onClick={() => setInputValue('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </button>
            )}
          </div>
          
          <button
            type="submit"
            disabled={!inputValue.trim() || loading}
            className={`p-3 rounded-lg ${
              !inputValue.trim() || loading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm hover:shadow transition-all'
            }`}
          >
            {loading ? (
              <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
              </svg>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface; 