"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Search, Folder, MessageSquare, UploadCloud, Settings, Database, BrainCircuit, X } from "lucide-react";

export function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const router = useRouter();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsOpen((open) => !open);
      }
      if (e.key === "Escape") {
        setIsOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  if (!isOpen) return null;

  const commands = [
    { label: "New Chat", href: "/dashboard/chat", icon: MessageSquare, shortcut: "C" },
    { label: "Upload Documents", href: "/dashboard/upload", icon: UploadCloud, shortcut: "U" },
    { label: "Search Knowledge Base", href: "/dashboard/documents", icon: Database, shortcut: "K" },
    { label: "Platform Settings", href: "/dashboard/admin/settings", icon: Settings, shortcut: "S" },
    { label: "Manage Entities", href: "/dashboard/entities", icon: BrainCircuit, shortcut: "E" },
  ];

  const filteredCommands = search 
    ? commands.filter(c => c.label.toLowerCase().includes(search.toLowerCase()))
    : commands;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 sm:pt-32 px-4 pointer-events-none">
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity animate-fade-in pointer-events-auto" 
        onClick={() => setIsOpen(false)}
      />
      <div className="relative w-full max-w-xl bg-surface border border-border-default rounded-2xl shadow-2xl overflow-hidden animate-slide-in-down ring-1 ring-white/10 pointer-events-auto">
        <div className="flex items-center px-4 py-3 border-b border-border-default">
          <Search className="w-5 h-5 text-muted-foreground mr-3" />
          <input
            autoFocus
            className="flex-1 bg-transparent border-none outline-none text-foreground placeholder-muted-foreground text-sm font-medium"
            placeholder="Type a command or search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button 
            onClick={() => setIsOpen(false)}
            className="p-1 rounded-md hover:bg-surface-2 text-muted-foreground transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="max-h-80 overflow-y-auto p-2">
          {filteredCommands.length > 0 ? (
            <div className="space-y-1">
              <p className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Suggestions
              </p>
              {filteredCommands.map((cmd) => (
                <button
                  key={cmd.label}
                  onClick={() => {
                    setIsOpen(false);
                    router.push(cmd.href);
                  }}
                  className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-primary/10 hover:text-primary text-foreground transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-1.5 rounded-lg bg-surface-2 group-hover:bg-primary/20 text-muted-foreground group-hover:text-primary transition-colors">
                      <cmd.icon className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-medium">{cmd.label}</span>
                  </div>
                  {cmd.shortcut && (
                    <span className="text-[10px] font-mono text-muted-foreground bg-surface-2 group-hover:bg-primary/10 px-2 py-1 rounded-md border border-border-default">
                      ⌘ {cmd.shortcut}
                    </span>
                  )}
                </button>
              ))}
            </div>
          ) : (
            <div className="px-4 py-12 text-center text-muted-foreground text-sm">
              No results found for "{search}"
            </div>
          )}
        </div>
        <div className="bg-surface-2 px-4 py-3 border-t border-border-default flex items-center justify-between">
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 rounded-md bg-surface border border-border-default font-mono">↑</kbd>
              <kbd className="px-1.5 py-0.5 rounded-md bg-surface border border-border-default font-mono">↓</kbd>
              to navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 rounded-md bg-surface border border-border-default font-mono">↵</kbd>
              to select
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 rounded-md bg-surface border border-border-default font-mono">esc</kbd>
              to close
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
