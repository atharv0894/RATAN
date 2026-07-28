"use client";
import React, { useState, useRef, useEffect, useCallback, Suspense } from "react";
import {
  Bot, Copy, RotateCcw, ThumbsUp, ThumbsDown, FileText,
  Loader2, ArrowUp, Mic, Plus, X,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { personalFilesApi, personalChatApi } from "@/lib/api";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useSearchParams, useRouter } from "next/navigation";

// ─── Types ───────────────────────────────────────────────────────────────────

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: any[];
  confidence?: number;
  follow_up_questions?: string[];
  provider?: string;
  timestamp?: number;
}

// ─── Core Chat Component ─────────────────────────────────────────────────────

function ChatContent() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isLoadingChat, setIsLoadingChat] = useState(false);
  const [attachedFile, setAttachedFile] = useState<{ name: string; id: string } | null>(null);

  // Ref to track the session ID that is currently loaded in state.
  // We use a ref (not state) to avoid triggering extra renders and race conditions.
  const loadedChatIdRef = useRef<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Scroll ──────────────────────────────────────────────────────────────────

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  // ── Load chat from URL ───────────────────────────────────────────────────────
  // This effect fires when the URL's chat_id changes.
  // Critical: we track `loadedChatIdRef` to prevent overwriting messages
  // that were just sent optimistically (which would cause the welcome flash).

  useEffect(() => {
    const chatId = searchParams.get("chat_id");

    // Case 1: No chat_id in URL — show empty welcome screen.
    if (!chatId) {
      loadedChatIdRef.current = null;
      setMessages([]);
      setAttachedFile(null);
      return;
    }

    // Case 2: This chat_id is already loaded — do nothing to avoid overwrite.
    if (loadedChatIdRef.current === chatId) {
      return;
    }

    // Case 3: Different chat selected — fetch from server.
    const loadChat = async () => {
      try {
        setIsLoadingChat(true);
        setMessages([]);
        setAttachedFile(null);

        const { data } = await personalChatApi.getSession(chatId);
        const sessionData = data.data;

        const msgs: Message[] = (sessionData.messages || []).map((m: any) => ({
          id: m.id,
          role: m.role as "user" | "assistant",
          content: m.content,
          citations: m.citations
            ? typeof m.citations === "string"
              ? JSON.parse(m.citations)
              : m.citations
            : undefined,
          confidence: m.confidence_score,
          follow_up_questions: m.follow_up_questions
            ? typeof m.follow_up_questions === "string"
              ? JSON.parse(m.follow_up_questions)
              : m.follow_up_questions
            : undefined,
          timestamp: m.created_at,
        }));

        loadedChatIdRef.current = chatId;
        setMessages(msgs);
      } catch (err: any) {
        console.error(err);
        // 404 = deleted/invalid chat — redirect to fresh start
        if (err?.response?.status === 404) {
          router.replace("/personal");
        } else {
          toast.error("Failed to load chat history");
        }
      } finally {
        setIsLoadingChat(false);
      }
    };

    loadChat();
  }, [searchParams, router]);

  // ── File Upload ──────────────────────────────────────────────────────────────

  const uploadMutation = useMutation({
    mutationFn: (file: File) => personalFilesApi.upload(file),
    onSuccess: (data, file) => {
      setAttachedFile({ name: file.name, id: data.data?.document_id || "temp" });
      toast.success(`"${file.name}" attached and indexed`);
      queryClient.invalidateQueries({ queryKey: ["personal_files"] });
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error?.message || "Failed to attach file");
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      uploadMutation.mutate(e.target.files[0]);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const removeAttachedFile = () => setAttachedFile(null);

  // ── Send Message ─────────────────────────────────────────────────────────────

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isTyping) return;

    const userMessage = input.trim();
    setInput("");

    // Optimistically add the user message immediately for instant feedback
    const optimisticId = `optimistic-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { id: optimisticId, role: "user", content: userMessage },
    ]);
    setIsTyping(true);

    try {
      let currentSessionId = searchParams.get("chat_id");

      if (!currentSessionId) {
        // Create the session BEFORE pushing to URL, so loadedChatIdRef
        // is set before the URL-change effect fires.
        const title =
          userMessage.length > 40
            ? userMessage.substring(0, 40) + "..."
            : userMessage;
        const res = await personalChatApi.createSession(title);
        currentSessionId = res.data.data.id;

        // Mark this session as already loaded to prevent the useEffect
        // from fetching it (which would overwrite our messages with an empty list).
        loadedChatIdRef.current = currentSessionId;

        // Update URL — this triggers the useEffect but loadedChatIdRef will
        // match so no fetch happens.
        router.push(`/personal?chat_id=${currentSessionId}`);

        // Refresh sidebar in background
        queryClient.invalidateQueries({ queryKey: ["personal_chat_sessions"] });
      }

      // Build question — prefix with attached file name if present
      const question = attachedFile
        ? `[Attached Document: ${attachedFile.name}]\n${userMessage}`
        : userMessage;

      // Build chat history from current messages (exclude the optimistic one)
      const history = messages.map((m) => ({ role: m.role, content: m.content }));

      const { data } = await personalChatApi.send(
        question,
        history,
        undefined,
        currentSessionId ?? undefined
      );
      const resp = data.data;

      // Clear the file chip after successful send
      setAttachedFile(null);

      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        {
          id: `ai-${Date.now()}`,
          role: "assistant",
          content: resp.answer,
          citations: resp.citations,
          confidence: resp.confidence_score,
          follow_up_questions: resp.follow_up_questions,
          provider: resp.provider,
          timestamp: Date.now() / 1000,
        },
      ]);

      // Refresh sidebar title in case backend updated it
      queryClient.invalidateQueries({ queryKey: ["personal_chat_sessions"] });
    } catch (err) {
      console.error(err);
      toast.error("Failed to get response from AI");
      setIsTyping(false);
      // Remove the optimistic user message on failure
      setMessages((prev) => prev.filter((m) => m.id !== optimisticId));
    }
  };

  // ── Render ───────────────────────────────────────────────────────────────────

  const chatId = searchParams.get("chat_id");
  const showWelcome = !isLoadingChat && messages.length === 0;

  return (
    <div className="flex flex-col h-full bg-bg text-text-primary selection:bg-primary/30 relative">

      {/* Mobile Header */}
      <div className="h-14 border-b border-border-default flex items-center justify-between px-4 bg-surface/80 backdrop-blur-xl sticky top-0 z-10 md:hidden shadow-sm">
        <div className="w-8" />
        <div className="flex justify-center">
          <ThemeToggle />
        </div>
        <div className="w-8" />
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth pb-40">
        <div className="max-w-3xl mx-auto space-y-8">

          {/* Loading State */}
          {isLoadingChat && (
            <div className="flex flex-col items-center justify-center min-h-[50vh] text-center space-y-4">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
              <p className="text-text-secondary text-sm">Loading conversation...</p>
            </div>
          )}

          {/* Welcome Screen — only when no chat_id AND no messages */}
          {!isLoadingChat && showWelcome && (
            <div className="flex flex-col items-center justify-center min-h-[50vh] text-center space-y-6 animate-fade-in mt-10">
              <div className="w-16 h-16 bg-surface-2 border border-border-default rounded-3xl flex items-center justify-center shadow-card relative overflow-hidden">
                <div className="absolute inset-0 bg-linear-to-br from-primary/10 to-accent/10 opacity-50" />
                <Bot className="w-8 h-8 text-foreground z-10" />
              </div>
              <div className="space-y-2">
                <h2 className="text-2xl font-bold text-text-primary">
                  How can I help you, {user?.full_name?.split(" ")[0]}?
                </h2>
                <p className="text-text-secondary max-w-md mx-auto text-sm">
                  Your personal AI assistant is ready. Ask questions, upload files, or explore your knowledge base.
                </p>
              </div>

              {/* Suggested Prompts */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl mt-8">
                {[
                  { title: "Summarize a PDF", desc: "Upload a document to extract key insights" },
                  { title: "Explain complex code", desc: "Paste your code to get a step-by-step breakdown" },
                  { title: "Generate a report", desc: "Format my notes into a professional document" },
                  { title: "Plan a schedule", desc: "Help me organize my tasks for the week" },
                ].map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(prompt.title)}
                    className="card-premium p-4 text-left group cursor-pointer"
                  >
                    <div className="text-sm font-semibold text-text-primary mb-1 group-hover:text-primary transition-colors">
                      {prompt.title}
                    </div>
                    <div className="text-xs text-text-secondary">{prompt.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Conversation Messages */}
          {!isLoadingChat && messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-4 ${msg.role === "assistant" ? "" : "justify-end"} animate-fade-in group`}
            >
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-lg bg-surface border border-border-default flex items-center justify-center shrink-0 shadow-sm">
                  <Bot className="w-4 h-4 text-foreground" />
                </div>
              )}

              <div className="flex flex-col gap-2 max-w-[85%]">
                <div
                  className={`px-5 py-3.5 rounded-2xl text-[15px] leading-relaxed shadow-sm overflow-hidden ${
                    msg.role === "user"
                      ? "bg-surface-2 border border-border-default text-text-primary rounded-tr-sm"
                      : "bg-transparent text-text-primary"
                  }`}
                >
                  {msg.role === "assistant" ? (
                    <div className="text-[15px] leading-relaxed wrap-break-word space-y-4">
                      <ReactMarkdown
                        components={{
                          p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                          pre: ({ node, ...props }) => (
                            <pre
                              className="bg-surface-2 border border-border-default rounded-xl p-4 my-3 overflow-x-auto text-sm font-mono text-text-primary shadow-inner"
                              {...props}
                            />
                          ),
                          code: ({ node, className, children, ...props }) => {
                            const match = /language-(\w+)/.exec(className || "");
                            return match ? (
                              <code className={className} {...props}>{children}</code>
                            ) : (
                              <code
                                className="bg-surface-2 border border-border-default px-1.5 py-0.5 rounded-md text-[13px] font-mono text-primary"
                                {...props}
                              >
                                {children}
                              </code>
                            );
                          },
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
                    <button
                      className="p-1.5 text-text-secondary hover:text-text-primary hover:bg-surface-2 rounded-md transition-colors"
                      title="Copy"
                      onClick={() => {
                        navigator.clipboard.writeText(msg.content);
                        toast.success("Copied to clipboard");
                      }}
                    >
                      <Copy className="w-3.5 h-3.5" />
                    </button>
                    <button className="p-1.5 text-text-secondary hover:text-text-primary hover:bg-surface-2 rounded-md transition-colors" title="Retry">
                      <RotateCcw className="w-3.5 h-3.5" />
                    </button>
                    <div className="w-px h-4 bg-border-default mx-1" />
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
                <div className="w-8 h-8 rounded-full bg-linear-to-br from-indigo-500 to-purple-600 flex items-center justify-center shrink-0 shadow-inner">
                  <span className="text-white text-xs font-bold">
                    {user?.full_name?.charAt(0).toUpperCase()}
                  </span>
                </div>
              )}
            </div>
          ))}

          {/* AI Thinking Indicator */}
          {isTyping && (
            <div className="flex gap-4 animate-fade-in">
              <div className="w-8 h-8 rounded-lg bg-surface border border-border-default flex items-center justify-center shrink-0 shadow-sm">
                <Bot className="w-4 h-4 text-foreground" />
              </div>
              <div className="px-5 py-4 bg-transparent flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} className="h-4" />
        </div>
      </div>

      {/* ── Input Area ─────────────────────────────────────────────────────────── */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-linear-to-t from-bg via-bg to-transparent pt-20 pointer-events-none">
        <div className="max-w-3xl mx-auto pointer-events-auto">
          <form
            onSubmit={handleSubmit}
            className="relative flex flex-col bg-[#2A2A2A] shadow-card rounded-4xl p-2 transition-all duration-300"
          >
            {/* Attached File Chip */}
            {attachedFile && (
              <div className="px-3 pt-2 pb-1">
                <div className="inline-flex items-center gap-3 bg-[#1A1A1A] border border-border-default rounded-xl p-2 pr-3 max-w-62.5">
                  <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center shrink-0">
                    <FileText className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex flex-col min-w-0 flex-1">
                    <span className="text-sm font-semibold text-text-primary truncate">{attachedFile.name}</span>
                    <span className="text-xs text-text-secondary">File • Ready</span>
                  </div>
                  <button
                    type="button"
                    onClick={removeAttachedFile}
                    className="w-5 h-5 bg-text-primary text-bg rounded-full flex items-center justify-center shrink-0 hover:bg-text-secondary transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              </div>
            )}

            {/* Upload progress chip */}
            {uploadMutation.isPending && (
              <div className="px-3 pt-2 pb-1">
                <div className="inline-flex items-center gap-2 bg-[#1A1A1A] border border-border-default rounded-xl p-2 pr-3">
                  <Loader2 className="w-4 h-4 animate-spin text-primary" />
                  <span className="text-xs text-text-secondary">Uploading & indexing...</span>
                </div>
              </div>
            )}

            <div className="flex items-end gap-2 px-2 py-1">
              <input
                type="file"
                className="hidden"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".pdf,.txt,.md,.csv,.docx"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadMutation.isPending}
                className="p-2.5 text-text-secondary hover:text-text-primary hover:bg-[#3A3A3A] rounded-full transition-colors shrink-0 disabled:opacity-50 mt-1"
                title="Attach a file"
              >
                <Plus className="w-6 h-6" />
              </button>

              <textarea
                rows={1}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  // Auto-grow
                  e.target.style.height = "auto";
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit();
                  }
                }}
                placeholder="Ask anything"
                className="flex-1 bg-transparent border-0 focus:ring-0 resize-none py-3 text-text-primary placeholder-text-secondary outline-none text-[16px] leading-relaxed self-center max-h-40 overflow-y-auto"
                style={{ minHeight: "48px" }}
              />

              <div className="flex items-center gap-1.5 shrink-0 mt-1">
                <button
                  type="button"
                  className="p-2.5 text-text-secondary hover:text-text-primary hover:bg-[#3A3A3A] rounded-full transition-colors"
                >
                  <Mic className="w-5 h-5" />
                </button>
                <button
                  type="submit"
                  disabled={!input.trim() || isTyping}
                  className={`p-2.5 rounded-full transition-all duration-300 disabled:opacity-50 ${
                    input.trim()
                      ? "bg-[#DE6F44] hover:bg-[#cc633a] text-white shadow-sm"
                      : "bg-[#3A3A3A] text-text-secondary"
                  }`}
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

// ─── Page Export ─────────────────────────────────────────────────────────────

export default function PersonalChatPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-full items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-text-secondary" />
        </div>
      }
    >
      <ChatContent />
    </Suspense>
  );
}
