"use client";
import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User as UserIcon, Paperclip } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export default function PersonalChatPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Array<{role: "user"|"assistant", content: string}>>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isTyping) return;
    
    const userMessage = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setIsTyping(true);
    
    // Simulate streaming
    setTimeout(() => {
      setIsTyping(false);
      setMessages(prev => [...prev, { role: "assistant", content: "This is a placeholder response for the new Personal AI Workspace. Connect to the real `/api/v1/personal/message` endpoint to enable true RAG and LLM streaming." }]);
    }, 1500);
  };

  return (
    <div className="flex flex-col h-full bg-(--bg) text-(--text-primary) selection:bg-primary/30">
      
      {/* Header */}
      <div className="h-14 border-b border-(--border) flex items-center justify-between px-4 bg-(--surface)/80 backdrop-blur-xl sticky top-0 z-10 md:hidden shadow-sm">
        <div className="w-8"></div> {/* Spacer for menu button from layout */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-(--surface-2) border border-(--border) shadow-sm cursor-pointer hover:border-(--primary)/50 transition-colors">
          <span className="text-sm font-semibold text-(--text-primary)">GPT-4o</span>
          <svg className="w-4 h-4 text-(--text-secondary)" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
        <div className="w-8"></div>
      </div>

      <div className="hidden md:flex h-14 border-b border-(--border) items-center justify-center bg-(--surface)/80 backdrop-blur-xl sticky top-0 z-10 shadow-sm">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-(--surface-2) border border-(--border) shadow-sm cursor-pointer hover:border-(--primary)/50 transition-colors">
          <span className="text-sm font-semibold text-(--text-primary)">GPT-4o</span>
          <svg className="w-4 h-4 text-(--text-secondary)" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth pb-32">
        <div className="max-w-3xl mx-auto space-y-8">
          
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center min-h-[50vh] text-center space-y-6 animate-fade-in mt-10">
              <div className="w-16 h-16 bg-gradient-to-br from-(--primary) to-(--accent) rounded-2xl flex items-center justify-center shadow-[var(--shadow-glow)]">
                <Bot className="w-8 h-8 text-white" />
              </div>
              <div className="space-y-2">
                <h2 className="text-2xl font-bold text-(--text-primary)">How can I help you, {user?.full_name?.split(' ')[0]}?</h2>
                <p className="text-(--text-secondary) max-w-md mx-auto text-sm">Your personal AI assistant is ready. Ask questions, upload files, or explore your knowledge base.</p>
              </div>
              
              {/* Suggested Prompts */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl mt-8">
                {[
                  { title: "Summarize a PDF", desc: "Upload a document to extract key insights" },
                  { title: "Explain complex code", desc: "Paste your code to get a step-by-step breakdown" },
                  { title: "Generate a report", desc: "Format my notes into a professional document" },
                  { title: "Plan a schedule", desc: "Help me organize my tasks for the week" }
                ].map((prompt, i) => (
                  <button 
                    key={i}
                    onClick={() => setInput(prompt.title)}
                    className="card-premium p-4 text-left group cursor-pointer hover:bg-(--surface-2)"
                  >
                    <div className="text-sm font-semibold text-(--text-primary) mb-1 group-hover:text-(--primary) transition-colors">{prompt.title}</div>
                    <div className="text-xs text-(--text-secondary)">{prompt.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`flex gap-4 ${msg.role === "assistant" ? "" : "justify-end"} animate-fade-in`}>
                
                {msg.role === "assistant" && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-(--primary) to-(--accent) flex items-center justify-center shrink-0 shadow-md">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                )}
                
                <div className={`px-5 py-3.5 max-w-[85%] rounded-2xl text-[15px] leading-relaxed shadow-sm ${
                  msg.role === "user" 
                    ? "bg-(--surface-2) border border-(--border) text-(--text-primary) rounded-tr-sm" 
                    : "bg-transparent text-(--text-primary)"
                }`}>
                  {msg.content}
                </div>

                {msg.role === "user" && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shrink-0 shadow-inner">
                    <span className="text-white text-xs font-bold">{user?.full_name?.charAt(0).toUpperCase()}</span>
                  </div>
                )}
              </div>
            ))
          )}

          {isTyping && (
            <div className="flex gap-4 animate-fade-in">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-(--primary) to-(--accent) flex items-center justify-center shrink-0 shadow-md">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="px-5 py-4 bg-transparent flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 bg-(--primary) rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-(--primary) rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-(--primary) rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} className="h-4" />
        </div>
      </div>

      {/* Input Area */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-(--bg) via-(--bg) to-transparent pt-10">
        <div className="max-w-3xl mx-auto">
          <form 
            onSubmit={handleSubmit} 
            className="relative flex items-end gap-2 bg-(--surface) border border-(--border) shadow-[var(--shadow-card)] rounded-[1.25rem] p-2 focus-within:border-(--primary)/50 focus-within:shadow-[var(--shadow-glow)] transition-all duration-300"
          >
            <button type="button" className="p-2.5 text-(--text-secondary) hover:text-(--text-primary) hover:bg-(--surface-2) rounded-xl transition-colors shrink-0">
              <Paperclip className="w-5 h-5" />
            </button>
            
            <textarea
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
              placeholder="Message RATAN Personal..."
              className="w-full max-h-40 bg-transparent border-0 focus:ring-0 resize-none py-3 px-2 text-(--text-primary) placeholder-(--text-secondary) outline-none text-[15px]"
              style={{ minHeight: '48px' }}
            />
            
            <button 
              type="submit" 
              disabled={!input.trim() || isTyping}
              className="p-2.5 bg-(--primary) hover:bg-(--primary-hover) disabled:bg-(--surface-2) disabled:text-(--text-secondary) text-white rounded-xl transition-all duration-300 shrink-0 mb-0.5 mr-0.5 disabled:opacity-50"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
          <div className="text-center mt-3 text-[11px] text-(--text-secondary) font-medium">
            RATAN Personal can make mistakes. Consider verifying important information.
          </div>
        </div>
      </div>
    </div>
  );
}
