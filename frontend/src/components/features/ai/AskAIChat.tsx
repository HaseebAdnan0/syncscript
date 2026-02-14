'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles } from 'lucide-react';
import { ChatMessage as ChatMessageType } from '@/lib/types/vault';

interface AskAIChatProps {
  vaultId: number;
  conversationId?: number;
  onNewConversation?: (conversationId: number) => void;
  messages: ChatMessageType[];
  onSendMessage: (question: string) => Promise<void>;
  isLoading: boolean;
}

export default function AskAIChat({
  vaultId: _vaultId, // Keep for future use
  conversationId: _conversationId, // Keep for future use
  onNewConversation: _onNewConversation, // Keep for future use
  messages,
  onSendMessage,
  isLoading
}: AskAIChatProps) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');

    await onSendMessage(userMessage);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages List */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Sparkles className="w-12 h-12 text-[#F7931A]/30 mb-4" />
            <p className="text-[#94A3B8] text-sm">
              Ask questions about your vault's sources and get cited answers from Claude AI.
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white'
                    : 'bg-black/50 border border-white/10 text-white/90'
                }`}
              >
                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                  {message.content}
                </p>

                {/* Citations for assistant messages */}
                {message.role === 'assistant' && message.sources_cited.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-white/10">
                    {message.sources_cited.map((citation, idx) => (
                      <button
                        key={idx}
                        className="text-xs bg-[#F7931A]/20 text-[#F7931A] px-3 py-1 rounded-full border border-[#F7931A]/30 hover:bg-[#F7931A]/30 transition-colors"
                        title={citation.excerpt}
                      >
                        {citation.source_title}
                      </button>
                    ))}
                  </div>
                )}

                {/* Timestamp */}
                <div className={`text-xs mt-2 ${
                  message.role === 'user' ? 'text-white/60' : 'text-[#94A3B8]'
                }`}>
                  {new Date(message.created_at).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-[80%] bg-black/50 border border-white/10 rounded-2xl px-4 py-3">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-[#F7931A] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-[#F7931A] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-[#F7931A] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                <span className="text-xs text-[#94A3B8]">Thinking...</span>
              </div>
            </div>
          </div>
        )}

        {/* Auto-scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="px-6 py-4 border-t border-white/10">
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your vault..."
            disabled={isLoading}
            className="flex-1 bg-black/50 border-b-2 border-white/20 h-12 px-4 text-white placeholder:text-[#94A3B8] focus:border-[#F7931A] focus:outline-none transition-colors disabled:opacity-50"
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white p-3 rounded-full shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all disabled:opacity-50 disabled:hover:scale-100"
            title="Send message"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
