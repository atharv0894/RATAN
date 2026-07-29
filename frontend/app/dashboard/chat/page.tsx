"use client";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { chatApi, documentsApi } from "@/lib/api";
import { ChatMessage, RAGResponse } from "@/types";
import { cn, formatRelativeTime } from "@/lib/utils";
import { toast } from "sonner";
import {
  Send, Brain, User, Copy, ThumbsUp, ThumbsDown, RotateCcw,
  FileText, Sparkles, ChevronRight, MessageSquare, Plus, X, Paperclip,
  MoreVertical, Edit2, Trash2, Pin, Menu, Loader2
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { motion, AnimatePresence } from "framer-motion";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: RAGResponse["citations"];
  confidence?: number;
  follow_up_questions?: string[];
  provider?: string;
  timestamp: number;
}

const SUGGESTED_PROMPTS = [
  "What are the maintenance procedures for the hydraulic system?",
  "Explain the safety protocols for welding operations",
  "What is the torque specification for the main assembly bolts?",
  "Summarize the quality inspection checklist",
  "What are the emergency shutdown procedures?",
];

let msgIdCounter = 0;
const getMsgId = () => `msg_${Date.now()}_${msgIdCounter++}`;

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<RAGResponse["citations"][0] | null>(null);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<{ id: string; title: string; created_at: number; is_pinned?: boolean }[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // UI State
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const fetchSessions = async () => {
    try {
      const { data } = await chatApi.listSessions();
      setSessions(data.data);
    } catch {
      console.error("Failed to fetch sessions");
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading]);

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
  };

  const sendMessage = async (text: string) => {
    if (!text.trim() && !attachedFile) return;

    let currentInput = text;
    
    if (attachedFile) {
      try {
        toast.info(`Uploading ${attachedFile.name}...`);
        await documentsApi.upload(attachedFile);
        toast.success("Document uploaded and indexing started!");
        currentInput = `[Attached Document: ${attachedFile.name}] ` + currentInput;
        setAttachedFile(null);
      } catch {
        toast.error("Failed to upload attached document.");
      }
    }

    const newMsg: Message = { id: getMsgId(), role: "user", content: currentInput, timestamp: Date.now() };
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((prev) => [...prev, newMsg]);
    setInput("");
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }

    setIsLoading(true);
    let aiMessageAdded = false;
    const aiId = getMsgId();

    try {
      for await (const chunk of chatApi.sendStream(currentInput, history as ChatMessage[], undefined, sessionId || undefined)) {
        if (chunk.type === "chunk") {
          setIsLoading(false);
          if (!aiMessageAdded) {
            aiMessageAdded = true;
            setMessages((prev) => [
              ...prev,
              { id: aiId, role: "assistant", content: chunk.text, timestamp: Date.now() },
            ]);
          } else {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === aiId ? { ...m, content: m.content + chunk.text } : m
              )
            );
          }
        } else if (chunk.type === "done") {
          setIsLoading(false);
          if (!aiMessageAdded) {
            setMessages((prev) => [
              ...prev,
              { id: aiId, role: "assistant", content: chunk.full_answer || "", timestamp: Date.now() },
            ]);
          }
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiId
                ? {
                    ...m,
                    content: chunk.full_answer || m.content,
                    citations: chunk.citations,
                    confidence: chunk.confidence,
                    provider: chunk.provider,
                  }
                : m
            )
          );
          if (chunk.session_id && !sessionId) {
            setSessionId(chunk.session_id);
          }
          fetchSessions();
        } else if (chunk.type === "error") {
          toast.error(chunk.message || "An error occurred during streaming.");
        }
      }
    } catch (e) {
      toast.error("Failed to get a response. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard");
  };

  const retryLast = () => {
    const lastUserMsg = [...messages].reverse().find((m) => m.role === "user");
    if (lastUserMsg) {
      setMessages((prev) => prev.slice(0, -1));
      sendMessage(lastUserMsg.content);
    }
  };

  const loadSession = async (id: string) => {
    try {
      setIsLoading(true);
      const { data } = await chatApi.getSession(id);
      const msgs = data.data.map((m: any) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        timestamp: m.created_at,
      }));
      setMessages(msgs);
      setSessionId(id);
      if (window.innerWidth < 768) setIsSidebarOpen(false);
    } catch {
      toast.error("Failed to load chat history");
    } finally {
      setIsLoading(false);
    }
  };

  const newChat = () => {
    setMessages([]);
    setSessionId(null);
    if (window.innerWidth < 768) setIsSidebarOpen(false);
  };

  // Session Management
  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this chat?")) return;
    try {
      await chatApi.deleteSession(id);
      setSessions(prev => prev.filter(s => s.id !== id));
      if (sessionId === id) newChat();
      toast.success("Chat deleted");
    } catch {
      toast.error("Failed to delete chat");
    }
    setActiveMenuId(null);
  };

  const handleRenameSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!editTitle.trim()) {
      setEditingSessionId(null);
      return;
    }
    try {
      await chatApi.renameSession(id, editTitle);
      setSessions(prev => prev.map(s => s.id === id ? { ...s, title: editTitle } : s));
      toast.success("Chat renamed");
    } catch {
      toast.error("Failed to rename chat");
    }
    setEditingSessionId(null);
    setActiveMenuId(null);
  };

  const handlePinSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await chatApi.pinSession(id);
      fetchSessions();
    } catch {
      toast.error("Failed to pin chat");
    }
    setActiveMenuId(null);
  };

  const filteredSessions = sessions.filter(s => s.title.toLowerCase().includes(searchQuery.toLowerCase()));

  // Group sessions
  const now = Date.now() / 1000;
  const day = 86400;
  const groups = {
    "Pinned": filteredSessions.filter(s => s.is_pinned),
    "Today": filteredSessions.filter(s => !s.is_pinned && now - s.created_at < day),
    "Yesterday": filteredSessions.filter(s => !s.is_pinned && now - s.created_at >= day && now - s.created_at < day * 2),
    "Last 7 Days": filteredSessions.filter(s => !s.is_pinned && now - s.created_at >= day * 2 && now - s.created_at < day * 7),
    "Older": filteredSessions.filter(s => !s.is_pinned && now - s.created_at >= day * 7),
  };

  return (
    <DashboardLayout title="AI Knowledge Assistant" subtitle="Ask questions about your industrial documentation">
      <div className="flex h-[calc(100vh-8rem)] gap-4 relative">
        
        {/* Sidebar Toggle */}
        <AnimatePresence>
          {!isSidebarOpen && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute top-4 left-4 z-50 flex items-center gap-2"
            >
              <button 
                className="p-2 bg-surface border border-border-default rounded-lg hover:bg-surface-2 transition-colors shadow-sm text-muted-foreground hover:text-foreground"
                onMouseEnter={() => setIsSidebarOpen(true)}
                onClick={() => setIsSidebarOpen(true)}
                title="Open Chat History"
              >
                <Menu className="w-5 h-5" />
              </button>
              <button 
                className="p-2 bg-surface border border-border-default rounded-lg hover:bg-surface-2 transition-colors shadow-sm text-muted-foreground hover:text-foreground"
                onClick={newChat}
                title="New Chat"
              >
                <Edit2 className="w-5 h-5" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Sidebar History */}
        <AnimatePresence initial={false}>
          {isSidebarOpen && (
            <>
              {/* Mobile overlay */}
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/50 z-30 md:hidden backdrop-blur-sm" 
                onClick={() => setIsSidebarOpen(false)}
              />
              
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: 256 }}
                exit={{ width: 0 }}
                transition={{ duration: 0.2, ease: "easeInOut" }}
                className="bg-background border-r border-border-default flex flex-col overflow-hidden shrink-0 z-40 absolute md:relative h-full left-0 shadow-xl md:shadow-none"
                onMouseLeave={() => {
                  if (typeof window !== 'undefined' && window.innerWidth >= 768) {
                    setIsSidebarOpen(false);
                  }
                }}
              >
                <div className="w-64 flex flex-col h-full">
                  <div className="p-3 space-y-3">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={newChat}
                        className="flex-1 flex items-center justify-start gap-2 bg-transparent hover:bg-surface-2 text-foreground rounded-lg px-3 py-2 text-sm font-medium transition-all"
                      >
                        <Plus className="w-4 h-4" />
                        New Chat
                      </button>
                      <button 
                        onClick={() => setIsSidebarOpen(false)}
                        className="p-2 rounded-lg hover:bg-surface-2 text-muted-foreground transition-colors"
                      >
                        <Menu className="w-5 h-5" />
                      </button>
                    </div>
                    <input 
                      type="text"
                      placeholder="Search chats..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full bg-surface-2 border border-border-default rounded-md px-3 py-1.5 text-sm focus:outline-none focus:border-primary/50"
                    />
                  </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-4">
                {Object.entries(groups).map(([label, items]) => {
                  if (items.length === 0) return null;
                  return (
                    <div key={label}>
                      <div className="text-[11px] font-semibold text-muted-foreground/60 px-3 py-2">
                        {label}
                      </div>
                      <div className="space-y-0.5">
                        {items.map((s) => (
                          <div
                            key={s.id}
                            className={cn(
                              "group relative w-full flex items-center justify-between px-3 py-2 rounded-lg text-left text-sm transition-all cursor-pointer",
                              sessionId === s.id
                                ? "bg-surface-2 text-foreground"
                                : "text-muted-foreground hover:bg-surface-2 hover:text-foreground"
                            )}
                            onClick={() => loadSession(s.id)}
                            onMouseLeave={() => setActiveMenuId(null)}
                          >
                            {editingSessionId === s.id ? (
                              <input 
                                autoFocus
                                type="text"
                                value={editTitle}
                                onChange={e => setEditTitle(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && handleRenameSession(s.id, e as any)}
                                onBlur={e => handleRenameSession(s.id, e as any)}
                                className="flex-1 bg-background border border-primary/50 rounded px-1 py-0.5 text-sm"
                                onClick={e => e.stopPropagation()}
                              />
                            ) : (
                              <span className="truncate flex-1 pr-6">{s.title}</span>
                            )}
                            
                            <div className={cn(
                              "absolute right-2 flex items-center",
                              activeMenuId === s.id || sessionId === s.id ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                            )}>
                              <button 
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setActiveMenuId(activeMenuId === s.id ? null : s.id);
                                }}
                                className="p-1 hover:bg-background rounded"
                              >
                                <MoreVertical className="w-3.5 h-3.5" />
                              </button>
                              
                              <AnimatePresence>
                                {activeMenuId === s.id && (
                                  <motion.div 
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.95 }}
                                    className="absolute right-0 top-6 bg-surface border border-border-default rounded-md shadow-xl py-1 z-50 w-28"
                                  >
                                    <button 
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setEditTitle(s.title);
                                        setEditingSessionId(s.id);
                                        setActiveMenuId(null);
                                      }}
                                      className="w-full text-left px-3 py-1.5 text-xs hover:bg-surface-2 flex items-center gap-2"
                                    >
                                      <Edit2 className="w-3 h-3" /> Rename
                                    </button>
                                    <button 
                                      onClick={(e) => handlePinSession(s.id, e)}
                                      className="w-full text-left px-3 py-1.5 text-xs hover:bg-surface-2 flex items-center gap-2"
                                    >
                                      <Pin className="w-3 h-3" /> {s.is_pinned ? 'Unpin' : 'Pin'}
                                    </button>
                                    <button 
                                      onClick={(e) => handleDeleteSession(s.id, e)}
                                      className="w-full text-left px-3 py-1.5 text-xs hover:bg-surface-2 text-danger flex items-center gap-2"
                                    >
                                      <Trash2 className="w-3 h-3" /> Delete
                                    </button>
                                  </motion.div>
                                )}
                              </AnimatePresence>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col overflow-hidden bg-background relative">
          <div className="flex-1 overflow-y-auto p-4 md:p-8 flex flex-col items-center">
            
            <div className="w-full max-w-212.5 flex flex-col pb-40">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full space-y-8 text-center pt-20">
                  <div className="w-16 h-16 rounded-full bg-surface border border-border-default flex items-center justify-center shadow-sm">
                    <Brain className="w-8 h-8 text-foreground" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-semibold text-foreground">How can I help you today?</h2>
                  </div>
                </div>
              ) : (
                <AnimatePresence>
                  {messages.map((msg) => (
                    <motion.div 
                      key={msg.id} 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={cn("flex w-full gap-4 mt-6", msg.role === "user" ? "justify-end" : "justify-start")}
                    >
                      {msg.role === "assistant" && (
                        <div className="w-8 h-8 rounded-full border border-border-default flex items-center justify-center shrink-0 mt-1 bg-surface">
                          <Brain className="w-4 h-4 text-foreground" />
                        </div>
                      )}
                      <div className={cn("max-w-[85%]", msg.role === "user" ? "items-end flex flex-col" : "items-start flex flex-col")}>
                        <div className={cn(
                          "px-5 py-3.5 text-[15px] leading-relaxed",
                          msg.role === "user"
                            ? "bg-primary text-white rounded-3xl shadow-sm"
                            : "bg-transparent text-foreground rounded-lg"
                        )}>
                          {msg.role === "assistant" ? (
                            <div className="prose prose-invert prose-p:leading-relaxed max-w-none [&>p]:mb-4 [&>p:last-child]:mb-0 [&>ul]:mb-4 [&>ol]:mb-4 [&>code]:bg-surface-2 [&>code]:px-1.5 [&>code]:py-0.5 [&>code]:rounded-md [&>pre]:bg-surface-2 [&>pre]:p-4 [&>pre]:rounded-lg [&>pre]:border [&>pre]:border-border-default">
                              <ReactMarkdown>{msg.content}</ReactMarkdown>
                            </div>
                          ) : (
                            msg.content
                          )}
                        </div>

                        {msg.role === "assistant" && (
                          <div className="mt-2 flex flex-col gap-3 w-full">
                            <div className="flex items-center gap-2">
                              {msg.confidence !== undefined && (
                                <div className="text-xs text-muted-foreground/60">
                                  Confidence: {(msg.confidence * 100).toFixed(0)}%
                                </div>
                              )}
                              <div className="flex items-center gap-1 ml-auto">
                                <button onClick={() => copyToClipboard(msg.content)} className="p-1 rounded hover:bg-surface-2 text-muted-foreground transition-colors" title="Copy">
                                  <Copy className="w-4 h-4" />
                                </button>
                                <button onClick={retryLast} className="p-1 rounded hover:bg-surface-2 text-muted-foreground transition-colors" title="Regenerate">
                                  <RotateCcw className="w-4 h-4" />
                                </button>
                                <button className="p-1 rounded hover:bg-surface-2 text-muted-foreground hover:text-success transition-colors">
                                  <ThumbsUp className="w-4 h-4" />
                                </button>
                                <button className="p-1 rounded hover:bg-surface-2 text-muted-foreground hover:text-danger transition-colors">
                                  <ThumbsDown className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                            
                            {/* Citations */}
                            {msg.citations && msg.citations.length > 0 && (
                              <div className="flex flex-wrap gap-2 mt-1">
                                {msg.citations.slice(0, 3).map((c, i) => (
                                  <button
                                    key={i}
                                    onClick={() => setSelectedCitation(c)}
                                    className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full bg-surface border border-border-default hover:bg-surface-2 transition-colors text-muted-foreground"
                                  >
                                    <FileText className="w-3 h-3 shrink-0" />
                                    <span className="truncate max-w-30">{c.document_name}</span>
                                    <span>p.{c.page}</span>
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              )}
              
              {isLoading && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex w-full gap-4 mt-6 justify-start">
                  <div className="w-8 h-8 rounded-full border border-border-default flex items-center justify-center shrink-0 mt-1 bg-surface">
                    <Brain className="w-4 h-4 text-foreground" />
                  </div>
                  <div className="px-2 py-3.5 flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm">Thinking...</span>
                  </div>
                </motion.div>
              )}
              <div ref={bottomRef} className="h-4" />
            </div>
          </div>

          {/* Input Area */}
          <div className="w-full flex justify-center p-4 bg-linear-to-t from-background via-background to-transparent absolute bottom-0 left-0 right-0 pt-10">
            <div className="w-full max-w-212.5 relative">
              {attachedFile && (
                <div className="absolute -top-12 left-0 flex items-center gap-2 px-3 py-1.5 bg-surface border border-border-default rounded-lg w-max text-xs text-foreground shadow-sm">
                  <FileText className="w-3.5 h-3.5" />
                  <span className="truncate max-w-50">{attachedFile.name}</span>
                  <button onClick={() => setAttachedFile(null)} className="ml-2 hover:text-danger transition-colors">
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
              
              <div className="flex flex-col bg-surface border border-border-default rounded-2xl shadow-lg focus-within:ring-2 focus-within:ring-primary/20 transition-all">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={handleInput}
                  onKeyDown={handleKeyDown}
                  placeholder="Message RATAN..."
                  rows={1}
                  className="w-full bg-transparent text-[15px] text-foreground placeholder:text-muted-foreground focus:outline-none resize-none max-h-48 px-4 py-3.5"
                  style={{ minHeight: "52px" }}
                />
                <div className="flex justify-between items-center px-3 pb-2 pt-1">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-surface-2 transition-colors"
                    title="Attach Document"
                  >
                    <Paperclip className="w-4 h-4" />
                  </button>
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    onChange={(e) => setAttachedFile(e.target.files?.[0] || null)} 
                    className="hidden" 
                    accept=".pdf,.txt,.md,.csv" 
                  />
                  <button
                    onClick={() => sendMessage(input)}
                    disabled={(!input.trim() && !attachedFile) || isLoading}
                    className="p-1.5 rounded-lg bg-foreground text-background hover:opacity-90 transition-opacity disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <p className="text-xs text-muted-foreground/60 text-center mt-3 mb-1">
                RATAN can make mistakes. Consider verifying important information.
              </p>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
