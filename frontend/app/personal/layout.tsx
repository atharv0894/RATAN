"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { MessageSquare, Database, Settings, User as UserIcon, LogOut, PanelLeftClose, PanelLeftOpen } from "lucide-react";

export default function PersonalLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!isLoading) {
      if (!user) {
        router.push("/auth/login");
      } else if (user.account_type === "ORGANIZATION") {
        router.push("/dashboard");
      } else if (user.account_type === "SUPER_ADMIN") {
        router.push("/super-admin");
      }
    }
  }, [user, isLoading, router]);

  if (!mounted || isLoading || !user || user.account_type !== "PERSONAL") {
    return <div className="h-screen bg-black flex items-center justify-center text-white">Loading Personal Workspace...</div>;
  }

  const handleLogout = async () => {
    await logout();
    router.push("/auth/login");
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white overflow-hidden">
      {/* Sidebar */}
      <div 
        className={`${sidebarOpen ? 'w-64' : 'w-0'} transition-all duration-300 bg-gray-950 flex flex-col shrink-0 border-r border-gray-800 relative`}
      >
        <div className="p-4 overflow-hidden whitespace-nowrap">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">RATAN Personal</h1>
        </div>
        
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
          <button onClick={() => router.push("/personal")} className="w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-800 rounded-md transition-colors text-left">
            <MessageSquare className="w-4 h-4 shrink-0" />
            <span>New Chat</span>
          </button>
          
          <div className="pt-4 pb-2 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Workspace</div>
          
          <button onClick={() => router.push("/personal/knowledge")} className="w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-800 rounded-md transition-colors text-left">
            <Database className="w-4 h-4 shrink-0" />
            <span>My Knowledge</span>
          </button>
          
          <button onClick={() => router.push("/personal/settings")} className="w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-800 rounded-md transition-colors text-left">
            <Settings className="w-4 h-4 shrink-0" />
            <span>Settings</span>
          </button>
        </div>
        
        <div className="p-3 border-t border-gray-800 overflow-hidden">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
              {user.full_name.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate">{user.full_name}</div>
              <div className="text-xs text-gray-500 truncate">{user.email}</div>
            </div>
          </div>
          <button onClick={handleLogout} className="w-full mt-2 flex items-center gap-3 px-3 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-gray-800 rounded-md transition-colors text-left">
            <LogOut className="w-4 h-4 shrink-0" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 bg-gray-900 relative">
        <button 
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="absolute top-4 left-4 z-10 p-2 text-gray-400 hover:text-white bg-gray-800/50 hover:bg-gray-800 rounded-md transition-colors backdrop-blur-sm"
        >
          {sidebarOpen ? <PanelLeftClose className="w-5 h-5" /> : <PanelLeftOpen className="w-5 h-5" />}
        </button>
        {children}
      </div>
    </div>
  );
}
