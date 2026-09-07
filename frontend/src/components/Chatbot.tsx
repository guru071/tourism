'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  MessageSquare,
  X,
  Send,
  Bot,
  User,
  RotateCcw,
  Sparkles,
  AlertCircle,
  Loader2,
  ChevronDown,
  Info,
} from 'lucide-react';
import { sendChatMessage, ChatMessage } from '@/lib/api';

interface DisplayMessage extends ChatMessage {
  id: string;
  timestamp: string;
  isError?: boolean;
}

const INITIAL_MESSAGE: DisplayMessage = {
  id: 'welcome-1',
  role: 'model',
  content:
    'Welcome to TourismOS. I am your AI travel assistant. How can I assist you with destination discovery, customized itineraries, or travel planning today?',
  timestamp: '',
};

const SUGGESTED_PROMPTS = [
  'Recommend a 3-day cultural itinerary for Kyoto',
  'What are top destinations for eco-tourism?',
  'Suggest a weekend getaway for outdoor adventure',
  'How do I budget for a European multi-city trip?',
];

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [messages, setMessages] = useState<DisplayMessage[]>([
    { ...INITIAL_MESSAGE, timestamp: formatTime(new Date()) },
  ]);
  const [input, setInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
      inputRef.current?.focus();
    }
  }, [isOpen, messages]);

  const handleSend = async (messageText?: string) => {
    const text = (messageText || input).trim();
    if (!text || isLoading) return;

    const userMessage: DisplayMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: formatTime(new Date()),
    };

    // Prepare history without error messages
    const validHistory: ChatMessage[] = messages
      .filter((m) => !m.isError)
      .map((m) => ({
        role: m.role,
        content: m.content,
      }));

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setLastFailedMessage(null);

    try {
      const response = await sendChatMessage(text, validHistory);
      const botMessage: DisplayMessage = {
        id: `model-${Date.now()}`,
        role: 'model',
        content: response.reply,
        timestamp: formatTime(new Date()),
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error
          ? err.message
          : 'Unable to connect to the AI assistant service. Please verify your connection and try again.';
      const errorMessage: DisplayMessage = {
        id: `err-${Date.now()}`,
        role: 'model',
        content: errorMsg,
        timestamp: formatTime(new Date()),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
      setLastFailedMessage(text);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleReset = () => {
    setMessages([{ ...INITIAL_MESSAGE, timestamp: formatTime(new Date()) }]);
    setInput('');
    setIsLoading(false);
    setLastFailedMessage(null);
  };

  const handleRetry = () => {
    if (lastFailedMessage) {
      handleSend(lastFailedMessage);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 select-none">
      {/* Chat Window */}
      {isOpen && (
        <div
          className="fixed bottom-20 right-6 z-50 flex h-[580px] max-h-[calc(100vh-6.5rem)] w-[380px] max-w-[calc(100vw-2rem)] sm:w-[420px] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl transition-all duration-200"
          role="dialog"
          aria-label="AI Travel Assistant"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900 px-4 py-3.5 text-white">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-sm">
                <Bot className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-white">TourismOS Assistant</h3>
                  <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-medium text-emerald-400 ring-1 ring-inset ring-emerald-500/20">
                    Online
                  </span>
                </div>
                <p className="text-xs text-slate-400">AI-Powered Travel Intelligence</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={handleReset}
                title="Reset conversation"
                aria-label="Reset conversation"
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
              >
                <RotateCcw className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                title="Minimize chat"
                aria-label="Minimize chat"
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
              >
                <ChevronDown className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto bg-slate-50/50 p-4 space-y-4">
            {messages.map((msg) => {
              const isUser = msg.role === 'user';
              return (
                <div
                  key={msg.id}
                  className={`flex items-start gap-2.5 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
                >
                  <div
                    className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs ${
                      isUser
                        ? 'border-emerald-600 bg-emerald-600 text-white'
                        : msg.isError
                        ? 'border-rose-200 bg-rose-50 text-rose-600'
                        : 'border-slate-200 bg-white text-emerald-600 shadow-sm'
                    }`}
                  >
                    {isUser ? (
                      <User className="h-4 w-4" />
                    ) : msg.isError ? (
                      <AlertCircle className="h-4 w-4" />
                    ) : (
                      <Bot className="h-4 w-4" />
                    )}
                  </div>

                  <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[80%]`}>
                    <div
                      className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                        isUser
                          ? 'rounded-tr-none bg-emerald-600 text-white shadow-sm'
                          : msg.isError
                          ? 'rounded-tl-none border border-rose-200 bg-rose-50 text-rose-900 shadow-sm'
                          : 'rounded-tl-none border border-slate-200/80 bg-white text-slate-800 shadow-sm'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                      {msg.isError && lastFailedMessage && (
                        <button
                          type="button"
                          onClick={handleRetry}
                          className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-rose-700 hover:text-rose-900 underline underline-offset-2"
                        >
                          <RotateCcw className="h-3 w-3" />
                          Retry request
                        </button>
                      )}
                    </div>
                    {msg.timestamp && (
                      <span className="mt-1 px-1 text-[10px] text-slate-400">
                        {msg.timestamp}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex items-start gap-2.5">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-white text-emerald-600 shadow-sm">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="rounded-2xl rounded-tl-none border border-slate-200/80 bg-white px-4 py-3 shadow-sm">
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-emerald-600" />
                    <span>Processing response...</span>
                  </div>
                </div>
              </div>
            )}

            {/* Suggested prompts */}
            {messages.length === 1 && !isLoading && (
              <div className="pt-2">
                <div className="mb-2 flex items-center gap-1.5 text-[11px] font-medium text-slate-500">
                  <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
                  <span>Suggested inquiries</span>
                </div>
                <div className="space-y-1.5">
                  {SUGGESTED_PROMPTS.map((prompt, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleSend(prompt)}
                      className="block w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-left text-xs text-slate-700 hover:border-emerald-500 hover:bg-emerald-50/50 hover:text-emerald-900 transition-colors shadow-sm"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-slate-200 bg-white p-3.5">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-2"
            >
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about destinations, itineraries..."
                disabled={isLoading}
                className="flex-1 rounded-xl border border-slate-300 bg-slate-50/50 px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/20 disabled:opacity-50 transition-all"
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                aria-label="Send message"
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-sm hover:bg-emerald-700 disabled:opacity-40 disabled:hover:bg-emerald-600 transition-colors"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </button>
            </form>
            <div className="mt-2 flex items-center justify-center gap-1 text-[11px] text-slate-400">
              <Info className="h-3 w-3 shrink-0" />
              <span>Automated assistant. Verify itinerary details independently.</span>
            </div>
          </div>
        </div>
      )}

      {/* Floating Toggle Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label={isOpen ? 'Close assistant chat' : 'Open AI assistant chat'}
        aria-expanded={isOpen}
        className="group relative flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-lg hover:shadow-xl hover:scale-105 active:scale-95 transition-all duration-200"
      >
        {isOpen ? (
          <X className="h-6 w-6" />
        ) : (
          <>
            <MessageSquare className="h-6 w-6" />
            <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-3.5 w-3.5 rounded-full border-2 border-white bg-emerald-500" />
            </span>
          </>
        )}
      </button>
    </div>
  );
}
