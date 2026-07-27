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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;
    
    const userMessage = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setIsTyping(true);
    
    // TODO: Connect to real backend streaming endpoint
    // For now, simulate streaming typing animation
    setTimeout(() => {
      setIsTyping(false);
      setMessages(prev => [...prev, { role: "assistant", content: "This is a placeholder response for the new Personal AI Workspace. Connect to the real `/api/v1/personal/message` endpoint to enable true RAG and LLM streaming." }]);
    }, 1500);
  };

  return (
    <div className="flex flex-col h-full bg-gray-900 text-gray-100">
      
      {/* Header */}
      <div className="h-14 border-b border-gray-800 flex items-center justify-center bg-gray-900/50 backdrop-blur-md sticky top-0 z-10">
        <h2 className="text-sm font-semibold text-gray-300">GPT-4o</h2>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth">
        <div className="max-w-3xl mx-auto space-y-8 pb-10">
          
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[50vh] text-center space-y-4">
              <div className="w-16 h-16 bg-blue-600/20 rounded-2xl flex items-center justify-center">
                <Bot className="w-8 h-8 text-blue-500" />
              </div>
              <h2 className="text-2xl font-bold text-gray-200">How can I help you today, {user?.full_name.split(' ')[0]}?</h2>
              <p className="text-gray-500 max-w-md">Your personal AI assistant is ready. Ask questions, upload files, or explore your knowledge base.</p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`flex gap-4 ${msg.role === "assistant" ? "" : "justify-end"}`}>
                
                {msg.role === "assistant" && (
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}
                
                <div className={`px-5 py-3.5 max-w-[85%] rounded-2xl text-[15px] leading-relaxed ${
                  msg.role === "user" 
                    ? "bg-gray-800 text-gray-100" 
                    : "bg-transparent text-gray-200"
                }`}>
                  {msg.content}
                </div>

                {msg.role === "user" && (
                  <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center shrink-0">
                    <UserIcon className="w-5 h-5 text-gray-300" />
                  </div>
                )}
              </div>
            ))
          )}

          {isTyping && (
            <div className="flex gap-4">
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="px-5 py-4 bg-transparent text-gray-200 flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4 bg-gray-900 border-t border-gray-800 relative z-10">
        <div className="max-w-3xl mx-auto">
          <form onSubmit={handleSubmit} className="relative flex items-end gap-2 bg-gray-800 border border-gray-700 rounded-2xl p-2 shadow-sm focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent transition-all">
            
            <button type="button" className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded-xl transition-colors shrink-0">
              <Paperclip className="w-5 h-5" />
            </button>
            
            <textarea
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              placeholder="Message RATAN Personal..."
              className="w-full max-h-32 bg-transparent border-0 focus:ring-0 resize-none py-2.5 px-2 text-gray-100 placeholder-gray-500"
              style={{ minHeight: '44px' }}
            />
            
            <button 
              type="submit" 
              disabled={!input.trim() || isTyping}
              className="p-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl transition-colors shrink-0 mb-0.5 mr-0.5"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
          <div className="text-center mt-2 text-xs text-gray-500">
            RATAN Personal can make mistakes. Consider verifying important information.
          </div>
        </div>
      </div>
    </div>
  );
}
