"use client";
import React from "react";
import { Settings, Shield, User, Key, Bell, CreditCard, Monitor, Cpu } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export default function PersonalSettingsPage() {
  const { user } = useAuth();
  
  return (
    <div className="flex-1 flex flex-col h-full bg-(--bg) text-(--text-primary) overflow-y-auto selection:bg-primary/30">
      
      {/* Header */}
      <div className="h-16 md:h-20 border-b border-(--border) flex items-center justify-between px-4 md:px-8 bg-(--bg) sticky top-0 z-10 pt-4 md:pt-0">
        <div className="ml-10 md:ml-0 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-[var(--shadow-glow)]">
            <Settings className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-(--text-primary) tracking-tight">Settings</h1>
            <p className="text-xs text-(--text-secondary) hidden sm:block">Manage your personal account preferences</p>
          </div>
        </div>
      </div>

      <div className="p-4 md:p-8 max-w-4xl mx-auto w-full flex flex-col md:flex-row gap-8 pb-20">
        
        {/* Navigation Sidebar (Desktop) */}
        <div className="hidden md:flex flex-col w-64 shrink-0 space-y-1 sticky top-28 h-fit">
          <div className="text-xs font-semibold text-(--text-secondary) uppercase tracking-wider mb-2 px-3">Account</div>
          <button className="flex items-center gap-3 px-3 py-2 bg-(--primary)/10 text-(--primary) rounded-xl font-medium text-sm transition-colors text-left border border-(--primary)/20">
            <User className="w-4 h-4" /> Profile
          </button>
          <button className="flex items-center gap-3 px-3 py-2 text-(--text-secondary) hover:text-(--text-primary) hover:bg-(--surface-2) rounded-xl font-medium text-sm transition-colors text-left">
            <Shield className="w-4 h-4" /> Security
          </button>
          <button className="flex items-center gap-3 px-3 py-2 text-(--text-secondary) hover:text-(--text-primary) hover:bg-(--surface-2) rounded-xl font-medium text-sm transition-colors text-left">
            <Bell className="w-4 h-4" /> Notifications
          </button>
          
          <div className="text-xs font-semibold text-(--text-secondary) uppercase tracking-wider mt-6 mb-2 px-3">Workspace</div>
          <button className="flex items-center gap-3 px-3 py-2 text-(--text-secondary) hover:text-(--text-primary) hover:bg-(--surface-2) rounded-xl font-medium text-sm transition-colors text-left">
            <Monitor className="w-4 h-4" /> Appearance
          </button>
          <button className="flex items-center gap-3 px-3 py-2 text-(--text-secondary) hover:text-(--text-primary) hover:bg-(--surface-2) rounded-xl font-medium text-sm transition-colors text-left">
            <Cpu className="w-4 h-4" /> AI Models
          </button>
          <button className="flex items-center gap-3 px-3 py-2 text-(--text-secondary) hover:text-(--text-primary) hover:bg-(--surface-2) rounded-xl font-medium text-sm transition-colors text-left">
            <Key className="w-4 h-4" /> API Keys
          </button>
          <button className="flex items-center gap-3 px-3 py-2 text-(--text-secondary) hover:text-(--text-primary) hover:bg-(--surface-2) rounded-xl font-medium text-sm transition-colors text-left">
            <CreditCard className="w-4 h-4" /> Billing
          </button>
        </div>
        
        {/* Mobile Navigation (Horizontal Scroll) */}
        <div className="md:hidden flex overflow-x-auto gap-2 pb-2 -mx-4 px-4 hide-scrollbar">
          <button className="shrink-0 px-4 py-2 bg-(--primary) text-white rounded-xl font-medium text-sm shadow-md">Profile</button>
          <button className="shrink-0 px-4 py-2 bg-(--surface-2) text-(--text-secondary) hover:text-(--text-primary) rounded-xl font-medium text-sm border border-(--border)">Security</button>
          <button className="shrink-0 px-4 py-2 bg-(--surface-2) text-(--text-secondary) hover:text-(--text-primary) rounded-xl font-medium text-sm border border-(--border)">Appearance</button>
          <button className="shrink-0 px-4 py-2 bg-(--surface-2) text-(--text-secondary) hover:text-(--text-primary) rounded-xl font-medium text-sm border border-(--border)">AI Models</button>
        </div>
        
        {/* Main Settings Content */}
        <div className="flex-1 space-y-8 animate-fade-in">
          
          <div className="card-premium overflow-hidden">
            <div className="p-6 border-b border-(--border)">
              <h2 className="text-lg font-semibold text-(--text-primary) flex items-center gap-2">
                <User className="w-5 h-5 text-(--text-secondary)" />
                Profile Details
              </h2>
              <p className="text-sm text-(--text-secondary) mt-1">Manage your personal information and how it's displayed.</p>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Avatar section */}
              <div className="flex items-center gap-6">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-indigo-500/20 shrink-0">
                  {user?.full_name?.charAt(0) ?? "U"}
                </div>
                <div className="space-y-3">
                  <div className="flex gap-2">
                    <button className="px-4 py-2 bg-(--primary) hover:bg-(--primary-hover) text-white rounded-lg text-sm font-medium transition-colors shadow-sm">Upload new</button>
                    <button className="px-4 py-2 bg-(--surface-2) hover:bg-[var(--surface-2)]/80 text-(--text-primary) border border-(--border) rounded-lg text-sm font-medium transition-colors">Remove</button>
                  </div>
                  <p className="text-xs text-(--text-secondary)">Recommended size: 256x256px. Max 2MB.</p>
                </div>
              </div>
              
              <div className="grid grid-cols-1 gap-6">
                <div>
                  <label className="block text-sm font-medium text-(--text-primary) mb-2">Full Name</label>
                  <input type="text" className="input-field" defaultValue={user?.full_name} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-(--text-primary) mb-2">Email Address</label>
                  <div className="flex relative">
                    <input type="email" className="input-field bg-(--surface-2)/50 text-(--text-secondary) pr-20" defaultValue={user?.email} disabled />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-medium text-[var(--success)] bg-[var(--success)]/10 px-2 py-0.5 rounded">Verified</span>
                  </div>
                  <p className="text-xs text-(--text-secondary) mt-1.5">To change your email, please contact support.</p>
                </div>
              </div>
            </div>
            
            <div className="bg-(--surface-2)/30 p-4 border-t border-(--border) flex justify-end">
              <button className="px-5 py-2 bg-(--primary) hover:bg-(--primary-hover) text-white rounded-xl text-sm font-medium transition-colors shadow-sm">
                Save Changes
              </button>
            </div>
          </div>
          
          <div className="card-premium overflow-hidden">
            <div className="p-6 border-b border-(--border)">
              <h2 className="text-lg font-semibold text-(--text-primary) flex items-center gap-2">
                <Shield className="w-5 h-5 text-(--text-secondary)" />
                Security
              </h2>
              <p className="text-sm text-(--text-secondary) mt-1">Keep your account secure with authentication settings.</p>
            </div>
            
            <div className="p-6 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-(--surface-2)/50 border border-(--border) rounded-xl">
                <div>
                  <div className="font-medium text-(--text-primary)">Password</div>
                  <div className="text-sm text-(--text-secondary) mt-0.5">You last changed your password 2 weeks ago</div>
                </div>
                <button className="px-4 py-2 bg-(--surface) hover:bg-(--surface-2) text-(--text-primary) border border-(--border) rounded-lg text-sm font-medium transition-colors shadow-sm whitespace-nowrap">
                  Change Password
                </button>
              </div>
              
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-(--surface-2)/50 border border-(--border) rounded-xl">
                <div>
                  <div className="font-medium text-(--text-primary) flex items-center gap-2">
                    Two-Factor Authentication
                    <span className="text-[10px] bg-[var(--warning)]/10 text-[var(--warning)] px-1.5 py-0.5 rounded border border-[var(--warning)]/20">Recommended</span>
                  </div>
                  <div className="text-sm text-(--text-secondary) mt-0.5">Add an extra layer of security to your account</div>
                </div>
                <button className="px-4 py-2 bg-(--primary) hover:bg-(--primary-hover) text-white rounded-lg text-sm font-medium transition-colors shadow-sm whitespace-nowrap">
                  Enable 2FA
                </button>
              </div>
              
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-[var(--danger)]/5 border border-[var(--danger)]/20 rounded-xl">
                <div>
                  <div className="font-medium text-[var(--danger)]">Danger Zone</div>
                  <div className="text-sm text-(--text-secondary) mt-0.5">Permanently delete your account and all data</div>
                </div>
                <button className="px-4 py-2 bg-transparent hover:bg-[var(--danger)]/10 text-[var(--danger)] border border-[var(--danger)]/30 rounded-lg text-sm font-medium transition-colors whitespace-nowrap">
                  Delete Account
                </button>
              </div>
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}
