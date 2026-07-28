"use client";
import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, Paperclip, Copy, RotateCcw, ThumbsUp, ThumbsDown, FileText, ChevronDown, Sparkles, Loader2, ArrowUp, Mic, Plus, X } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { personalFilesApi } from "@/lib/api";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function PersonalChatPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Array<{role: "user"|"assistant", content: string, id: string}>>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [attachedFile, setAttachedFile] = useState<{name: string, id: string} | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: (file: File) => personalFilesApi.upload(file),
    onSuccess: (data, file) => {
      setAttachedFile({ name: file.name, id: data.data?.document_id || "temp" });
      toast.success("File attached");
      queryClient.invalidateQueries({ queryKey: ["personal_files"] });
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error?.message || "Failed to attach file");
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      uploadMutation.mutate(e.target.files[0]);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const removeAttachedFile = () => setAttachedFile(null);
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
    const userMsgId = Date.now().toString();
    setMessages(prev => [...prev, { role: "user", content: userMessage, id: userMsgId }]);
    setIsTyping(true);
    
    // Simulate streaming
    setTimeout(() => {
      setIsTyping(false);
      setMessages(prev => [...prev, { role: "assistant", content: "This is a placeholder response for the new Personal AI Workspace. Connect to the real `/api/v1/personal/message` endpoint to enable true RAG and LLM streaming.\n\n```python\nprint(\"Hello World\")\n```", id: (Date.now() + 1).toString() }]);
    }, 1500);
  };

  return (
    <div className="flex flex-col h-full bg-bg text-text-primary selection:bg-primary/30 relative">
      
      {/* Mobile Header */}
      <div className="h-14 border-b border-border-default flex items-center justify-between px-4 bg-surface/80 backdrop-blur-xl sticky top-0 z-10 md:hidden shadow-sm">
        <div className="w-8"></div>
        <div className="flex justify-center">
          <ThemeToggle />
        </div>
        <div className="w-8"></div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth pb-40">
        <div className="max-w-3xl mx-auto space-y-8">
          
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center min-h-[50vh] text-center space-y-6 animate-fade-in mt-10">
              <div className="w-16 h-16 bg-surface-2 border border-border-default rounded-3xl flex items-center justify-center shadow-card relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-accent/10 opacity-50"></div>
                <Bot className="w-8 h-8 text-foreground z-10" />
              </div>
              <div className="space-y-2">
                <h2 className="text-2xl font-bold text-text-primary">How can I help you, {user?.full_name?.split(' ')[0]}?</h2>
                <p className="text-text-secondary max-w-md mx-auto text-sm">Your personal AI assistant is ready. Ask questions, upload files, or explore your knowledge base.</p>
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
                    className="card-premium p-4 text-left group cursor-pointer"
                  >
                    <div className="text-sm font-semibold text-text-primary mb-1 group-hover:text-primary transition-colors flex items-center gap-2">
                      {prompt.title}
                    </div>
                    <div className="text-xs text-text-secondary">{prompt.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={msg.id} className={`flex gap-4 ${msg.role === "assistant" ? "" : "justify-end"} animate-fade-in group`}>
                
                {msg.role === "assistant" && (
                  <div className="w-8 h-8 rounded-lg bg-surface border border-border-default flex items-center justify-center shrink-0 shadow-sm">
                    <Bot className="w-4 h-4 text-foreground" />
                  </div>
                )}
                
                <div className={`flex flex-col gap-2 max-w-[85%]`}>
                  <div className={`px-5 py-3.5 rounded-2xl text-[15px] leading-relaxed shadow-sm overflow-hidden ${
                    msg.role === "user" 
                      ? "bg-surface-2 border border-border-default text-text-primary rounded-tr-sm" 
                      : "bg-transparent text-text-primary"
                  }`}>
                    {msg.role === "assistant" ? (
                      <div className="text-[15px] leading-relaxed break-words space-y-4">
                        <ReactMarkdown 
                          components={{
                            p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
                            pre: ({node, ...props}) => <pre className="bg-surface-2 border border-border-default rounded-xl p-4 my-3 overflow-x-auto text-sm font-mono text-text-primary shadow-inner" {...props} />,
                            code: ({node, className, children, ...props}) => {
                              const match = /language-(\w+)/.exec(className || '')
                              return match ? (
                                <code className={className} {...props}>
                                  {children}
                                </code>
                              ) : (
                                <code className="bg-surface-2 border border-border-default px-1.5 py-0.5 rounded-md text-[13px] font-mono text-primary" {...props}>
                                  {children}
                                </code>
                              )
                            }
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                    )}
                  </div>

                  {msg.role === "assistant" && (
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity ml-1 mt-1">
                      <button className="p-1.5 text-text-secondary hover:text-text-primary hover:bg-surface-2 rounded-md transition-colors" title="Copy">
                        <Copy className="w-3.5 h-3.5" />
                      </button>
                      <button className="p-1.5 text-text-secondary hover:text-text-primary hover:bg-surface-2 rounded-md transition-colors" title="Retry">
                        <RotateCcw className="w-3.5 h-3.5" />
                      </button>
                      <div className="w-px h-4 bg-border-default mx-1"></div>
                      <button className="p-1.5 text-text-secondary hover:text-success hover:bg-success/10 rounded-md transition-colors" title="Good response">
                        <ThumbsUp className="w-3.5 h-3.5" />
                      </button>
                      <button className="p-1.5 text-text-secondary hover:text-danger hover:bg-danger/10 rounded-md transition-colors" title="Bad response">
                        <ThumbsDown className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
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
              <div className="w-8 h-8 rounded-lg bg-surface border border-border-default flex items-center justify-center shrink-0 shadow-sm">
                <Bot className="w-4 h-4 text-foreground" />
              </div>
              <div className="px-5 py-4 bg-transparent flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} className="h-4" />
        </div>
      </div>

      {/* Input Area */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-bg via-bg to-transparent pt-20 pointer-events-none">
        <div className="max-w-3xl mx-auto pointer-events-auto">
          <form 
            onSubmit={handleSubmit} 
            className="relative flex flex-col bg-[#2A2A2A] shadow-card rounded-[2rem] p-2 transition-all duration-300"
          >
            {/* File Chip Row */}
            {attachedFile && (
              <div className="px-3 pt-2 pb-1">
                <div className="inline-flex items-center gap-3 bg-[#1A1A1A] border border-border-default rounded-xl p-2 pr-3 max-w-[250px]">
                  <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center shrink-0">
                    <FileText className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex flex-col min-w-0 flex-1">
                    <span className="text-sm font-semibold text-text-primary truncate">{attachedFile.name}</span>
                    <span className="text-xs text-text-secondary">File</span>
                  </div>
                  <button type="button" onClick={removeAttachedFile} className="w-5 h-5 bg-text-primary text-bg rounded-full flex items-center justify-center shrink-0 hover:bg-text-secondary transition-colors">
                    <X className="w-3 h-3" />
                  </button>
                </div>
              </div>
            )}
            
            <div className="flex items-end gap-2 px-2 py-1">
              <input 
                type="file" 
                className="hidden" 
                ref={fileInputRef} 
                onChange={handleFileChange} 
              />
              <button 
                type="button" 
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadMutation.isPending}
                className="p-2.5 text-text-secondary hover:text-text-primary hover:bg-[#3A3A3A] rounded-full transition-colors shrink-0 disabled:opacity-50 mt-1"
              >
                {uploadMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Plus className="w-6 h-6" />}
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
                placeholder="Ask anything"
                className="flex-1 bg-transparent border-0 focus:ring-0 resize-none py-3 text-text-primary placeholder-text-secondary outline-none text-[16px] leading-relaxed self-center max-h-40 overflow-y-auto"
                style={{ minHeight: '48px' }}
              />
              
              <div className="flex items-center gap-1.5 shrink-0 mt-1">
                <button type="button" className="p-2.5 text-text-secondary hover:text-text-primary hover:bg-[#3A3A3A] rounded-full transition-colors">
                  <Mic className="w-5 h-5" />
                </button>
                <button 
                  type="submit" 
                  disabled={!input.trim() || isTyping}
                  className={`p-2.5 rounded-full transition-all duration-300 disabled:opacity-50 ${input.trim() ? 'bg-[#DE6F44] hover:bg-[#cc633a] text-white shadow-sm' : 'bg-[#3A3A3A] text-text-secondary'}`}
                >
                  <ArrowUp className="w-5 h-5" />
                </button>
              </div>
            </div>
          </form>
          <div className="text-center mt-3 text-[11px] text-text-secondary font-medium">
            AI can make mistakes. Verify important information.
          </div>
        </div>
      </div>
    </div>
  );
}
