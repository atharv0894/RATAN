"use client";
import React, { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { MessageSquare, Database, Settings, User as UserIcon, LogOut, PanelLeftClose, PanelLeftOpen } from "lucide-react";

import { ThemeToggle } from "@/components/ThemeToggle";
import { useQuery } from "@tanstack/react-query";
import { personalChatApi } from "@/lib/api";

export default function PersonalLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mounted, setMounted] = useState(false);

  const { data: sessionsData, isLoading: sessionsLoading } = useQuery({
    queryKey: ["personal_chat_sessions"],
    queryFn: () => personalChatApi.listSessions(),
    enabled: !!user && user.account_type === "PERSONAL",
  });
  const sessions = sessionsData?.data?.data?.sessions || [];

  // Auth routes that should NOT be blocked by this layout
  const isAuthRoute = pathname.startsWith('/personal/login') || 
                      pathname.startsWith('/personal/register') || 
                      pathname.startsWith('/personal/verify-email') || 
                      pathname.startsWith('/personal/email-verified') || 
                      pathname.startsWith('/personal/google-callback');

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!isLoading && !isAuthRoute) {
      if (!user) {
        router.push("/");
      } else if (user.account_type === "ORGANIZATION") {
        router.push("/dashboard");
      } else if (user.account_type === "SUPER_ADMIN") {
        router.push("/super-admin");
      }
    }
  }, [user, isLoading, router, isAuthRoute]);

  if (isAuthRoute) {
    return <>{children}</>;
  }

  if (!mounted || isLoading || !user || user.account_type !== "PERSONAL") {
    return (
      <div className="h-screen bg-[var(--bg)] flex items-center justify-center text-[var(--text-primary)]">
        <div className="flex flex-col items-center gap-4 animate-fade-in">
          <div className="w-12 h-12 border-4 border-[var(--surface-2)] border-t-[var(--primary)] rounded-full animate-spin"></div>
          <p className="text-sm font-medium text-[var(--text-secondary)]">Loading Personal Workspace...</p>
        </div>
      </div>
    );
  }

  const handleLogout = async () => {
    await logout();
    router.push("/");
  };

  const navItems = [
    { label: "New Chat", href: "/personal", icon: MessageSquare },
    { label: "My Knowledge", href: "/personal/knowledge", icon: Database },
    { label: "Settings", href: "/personal/settings", icon: Settings },
  ];

  return (
    <div className="flex h-screen bg-[var(--bg)] text-[var(--text-primary)] overflow-hidden font-sans selection:bg-primary/30">
      
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/40 z-40 md:hidden backdrop-blur-sm transition-opacity" 
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside 
        className={`fixed md:relative z-50 h-full transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] flex flex-col bg-[var(--surface)] border-r border-[var(--border)] shrink-0 shadow-[var(--shadow-card)]
          ${sidebarOpen ? 'w-[280px] translate-x-0' : 'w-[280px] -translate-x-full md:w-0 md:-translate-x-full'}
        `}
      >
        <div className="h-14 px-4 flex items-center justify-between border-b border-[var(--border)] shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[var(--primary)] to-[var(--accent)] flex items-center justify-center shadow-md">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h1 className="text-sm font-bold tracking-wide">RATAN <span className="text-[var(--text-secondary)] font-medium">Personal</span></h1>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <button onClick={() => setSidebarOpen(false)} className="md:hidden p-1.5 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--surface-2)] transition-colors">
              <PanelLeftClose className="w-4 h-4" />
            </button>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          
          <div className="space-y-1">
            {navItems.map((item) => {
              const active = pathname === item.href;
              return (
                <button 
                  key={item.href}
                  onClick={() => {
                    router.push(item.href);
                    if (window.innerWidth < 768) setSidebarOpen(false);
                  }} 
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group ${
                    active ? 'bg-primary/10 text-primary border border-primary/20 shadow-sm' : 'text-text-secondary hover:bg-surface-2 hover:text-text-primary border border-transparent'
                  }`}
                >
                  <item.icon className={`w-4 h-4 shrink-0 ${active ? 'text-primary' : 'text-text-secondary group-hover:text-text-primary'}`} />
                  <span>{item.label}</span>
                </button>
              )
            })}
          </div>

          <div className="px-1">
            <div className="relative mb-4">
              <svg className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input type="text" placeholder="Search chats..." className="w-full bg-surface-2 border border-border-default rounded-lg pl-9 pr-3 py-1.5 text-xs text-text-primary outline-none focus:border-border-hover transition-colors" />
            </div>
          </div>
          
          <div>
            <div className="px-3 pb-2 text-[10px] font-semibold text-text-secondary uppercase tracking-wider flex justify-between items-center group cursor-pointer">
              <span>Pinned</span>
            </div>
            <div className="space-y-0.5">
              <button className="w-full flex items-center gap-3 px-3 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-surface-2 rounded-lg transition-colors text-left group">
                <div className="w-1.5 h-1.5 rounded-full bg-accent"></div>
                <span className="truncate">Q3 Manufacturing Report Analysis</span>
              </button>
            </div>
          </div>

          <div>
            <div className="px-3 pt-2 pb-2 text-[10px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider flex justify-between items-center group cursor-pointer">
              <span>Recent</span>
            </div>
            <div className="space-y-0.5">
              {sessionsLoading ? (
                <div className="px-3 py-2 text-sm text-[var(--text-secondary)]">Loading chats...</div>
              ) : sessions && sessions.length > 0 ? (
                sessions.map((session: any) => (
                  <button 
                    key={session.id} 
                    onClick={() => {
                      router.push(`/personal?chat_id=${session.id}`);
                      if (window.innerWidth < 768) setSidebarOpen(false);
                    }}
                    className="w-full flex items-center justify-between px-3 py-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-2)] rounded-lg transition-colors text-left group"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <MessageSquare className="w-3.5 h-3.5 shrink-0 opacity-60 group-hover:opacity-100" />
                      <span className="truncate">{session.title || "New Chat"}</span>
                    </div>
                  </button>
                ))
              ) : (
                <div className="px-3 py-2 text-sm text-[var(--text-secondary)]">No recent chats</div>
              )}
            </div>
          </div>
          
        </div>
        
        {/* User Menu */}
        <div className="p-4 border-t border-[var(--border)] shrink-0 bg-[var(--surface)]">
          <div className="flex items-center gap-3 p-2 rounded-xl hover:bg-[var(--surface-2)] transition-colors cursor-pointer group mb-2 border border-transparent hover:border-[var(--border)]">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shrink-0 shadow-inner">
              <span className="text-white text-sm font-bold">{user.full_name.charAt(0).toUpperCase()}</span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-[var(--text-primary)] truncate">{user.full_name}</div>
              <div className="text-xs text-[var(--text-secondary)] truncate">{user.email}</div>
            </div>
          </div>
          <button 
            onClick={handleLogout} 
            className="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm font-medium text-[var(--color-danger)] hover:bg-[var(--color-danger)]/10 rounded-xl transition-colors text-left"
          >
            <LogOut className="w-4 h-4 shrink-0" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
      
      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 bg-[var(--bg)] relative h-full transition-all">
        
        {/* Toggle Button when sidebar is closed */}
        {!sidebarOpen && (
          <button 
            onClick={() => setSidebarOpen(true)}
            className="absolute top-3 left-3 md:top-4 md:left-4 z-20 p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] bg-[var(--surface)]/80 hover:bg-[var(--surface)] border border-[var(--border)] shadow-sm rounded-xl transition-all backdrop-blur-md"
            title="Open sidebar"
          >
            <PanelLeftOpen className="w-4 h-4 md:w-5 md:h-5" />
          </button>
        )}
        
        <div className="flex-1 overflow-hidden">
          {children}
        </div>
      </main>
    </div>
  );
}
