import React, { useState, useRef, useEffect } from 'react';

const ChatInterface = ({ title, messages, onSendMessage, loading }) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  // Scroll to bottom when new messages come in
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

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

  return (
    <div className="bg-white rounded-lg shadow-md flex flex-col h-[500px]">
      <div className="p-4 bg-slate-800 text-white rounded-t-lg">
        <h3 className="text-lg font-semibold">{title}</h3>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 bg-slate-50">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-400 italic">Send a message to begin conversation</p>
          </div>
        ) : (
          <div className="space-y-3">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg max-w-[85%] ${
                  message.role === 'user'
                    ? 'bg-slate-200 text-slate-800 ml-auto'
                    : 'bg-white border border-slate-200 text-slate-800'
                }`}
              >
                <div className="text-sm whitespace-pre-wrap">
                  {message.content}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div className="border-t border-gray-200 p-3 bg-white">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (inputValue.trim()) {
              onSendMessage(inputValue);
              setInputValue('');
            }
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || loading}
            className={`p-2 rounded-md ${
              !inputValue.trim() || loading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-slate-700 text-white hover:bg-slate-800'
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