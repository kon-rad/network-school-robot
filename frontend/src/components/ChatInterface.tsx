import { useState, useRef, useEffect } from 'react';
import { chatApi } from '../services/api';
import type { ChatMessage, ActionResult } from '../types';

interface ChatInterfaceProps {
  onAction?: (action: string) => void;
}

export function ChatInterface({ onAction }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConfigured, setIsConfigured] = useState<boolean | null>(null);
  const [robotConnected, setRobotConnected] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    checkStatus();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const checkStatus = async () => {
    try {
      const status = await chatApi.getStatus();
      setIsConfigured(status.configured);
      setRobotConnected(status.robot_connected);
    } catch {
      setIsConfigured(false);
    }
  };

  const extractActions = (text: string): [string, string[]] => {
    const actionRegex = /\[([^\]]+)\]/g;
    const actions: string[] = [];
    let match;
    while ((match = actionRegex.exec(text)) !== null) {
      actions.push(match[1]);
    }
    const cleanText = text.replace(/\s*\[[^\]]+\]\s*/g, ' ').trim();
    return [cleanText, actions];
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setStreamingContent('');

    try {
      let fullContent = '';
      let actions: string[] = [];
      let actionResults: ActionResult[] = [];

      for await (const event of chatApi.streamMessage(userMessage.content)) {
        if (event.content) {
          fullContent += event.content;
          setStreamingContent(fullContent);
        }
        if (event.actions) {
          actions = event.actions;
        }
        if (event.action_results) {
          actionResults = event.action_results;
        }
      }

      const [cleanContent, extractedActions] = extractActions(fullContent);
      const finalActions = actions.length > 0 ? actions : extractedActions;

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: cleanContent,
        actions: finalActions,
        actionResults: actionResults,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      setStreamingContent('');

      if (onAction && finalActions.length > 0) {
        for (const action of finalActions) {
          onAction(action);
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      setStreamingContent('');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = async () => {
    try {
      await chatApi.clearHistory();
      setMessages([]);
    } catch (error) {
      console.error('Failed to clear history:', error);
    }
  };

  if (isConfigured === null) {
    return (
      <div className="card h-[600px] flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-[var(--text-secondary)]">Connecting to chat service...</p>
        </div>
      </div>
    );
  }

  if (!isConfigured) {
    return (
      <div className="card h-[600px] flex items-center justify-center">
        <div className="text-center max-w-sm px-6">
          <div className="w-12 h-12 rounded-full bg-[var(--warning)]/10 flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-[var(--warning)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-[var(--text-primary)] mb-2">Chat Not Configured</h3>
          <p className="text-sm text-[var(--text-secondary)] mb-4">
            Set the <code className="text-[var(--accent-primary)] bg-[var(--bg-tertiary)] px-1.5 py-0.5 rounded text-xs">OPENAI_API_KEY</code> environment variable to enable the chat feature.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card flex flex-col h-[600px]">
      {/* Header */}
      <div className="card-header flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-[var(--accent-primary)]/10 flex items-center justify-center">
            <svg className="w-4 h-4 text-[var(--accent-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <div>
            <h2 className="font-medium text-[var(--text-primary)]">Chat with Reachy</h2>
            <div className="flex items-center gap-2 text-xs text-[var(--text-tertiary)]">
              <span>Powered by OpenAI</span>
              <span className={`inline-flex items-center gap-1 ${robotConnected ? 'text-[var(--success)]' : 'text-[var(--text-tertiary)]'}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${robotConnected ? 'bg-[var(--success)]' : 'bg-[var(--text-tertiary)]'}`} />
                {robotConnected ? 'Robot connected' : 'Robot offline'}
              </span>
            </div>
          </div>
        </div>
        {messages.length > 0 && (
          <button onClick={handleClearHistory} className="btn btn-ghost btn-sm">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Clear
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {messages.length === 0 && !streamingContent && (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-[var(--text-tertiary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-[var(--text-primary)] mb-1">Start a conversation</h3>
            <p className="text-sm text-[var(--text-secondary)] max-w-xs">
              Say hello to Reachy! Ask questions, get help, or just chat.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-up`}
          >
            <div className={`message ${message.role === 'user' ? 'message-user' : 'message-assistant'}`}>
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              {/* Display captured images */}
              {message.actionResults?.some(r => r.image_base64) && (
                <div className="mt-3">
                  {message.actionResults.filter(r => r.image_base64).map((result, idx) => (
                    <div key={idx} className="rounded-lg overflow-hidden border border-white/10">
                      <img
                        src={`data:image/${result.format || 'jpeg'};base64,${result.image_base64}`}
                        alt="Captured by robot"
                        className="w-full max-h-64 object-cover"
                      />
                    </div>
                  ))}
                </div>
              )}
              {message.actions && message.actions.length > 0 && (
                <div className="mt-2 pt-2 border-t border-white/10">
                  <p className="text-xs text-[var(--text-tertiary)] mb-1.5">Actions:</p>
                  <div className="flex flex-wrap gap-1.5">
                    {message.actions.map((action, idx) => {
                      const result = message.actionResults?.[idx];
                      const isSuccess = result?.success !== false;
                      return (
                        <span
                          key={idx}
                          className={`badge text-xs ${isSuccess ? 'badge-success' : 'badge-error'}`}
                          title={result?.message}
                        >
                          {isSuccess ? '✓' : '✗'} {action}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {streamingContent && (
          <div className="flex justify-start animate-slide-up">
            <div className="message message-assistant">
              <p className="text-sm whitespace-pre-wrap">
                {streamingContent}
                <span className="inline-block w-1.5 h-4 bg-[var(--text-secondary)] animate-pulse ml-0.5 align-middle" />
              </p>
            </div>
          </div>
        )}

        {isLoading && !streamingContent && (
          <div className="flex justify-start">
            <div className="message message-assistant">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-[var(--text-tertiary)] animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 rounded-full bg-[var(--text-tertiary)] animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 rounded-full bg-[var(--text-tertiary)] animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-[var(--border-default)]">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={isLoading}
            className="input flex-1"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="btn btn-primary"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
            <span className="hidden sm:inline">Send</span>
          </button>
        </form>
      </div>
    </div>
  );
}
