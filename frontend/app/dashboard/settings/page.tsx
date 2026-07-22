"use client";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { useAuth } from "@/lib/auth-context";
import { User, Shield, Key, Bell, Palette, Database } from "lucide-react";

export default function SettingsPage() {
  const { user } = useAuth();

  return (
    <DashboardLayout title="Platform Settings" subtitle="Manage your account, preferences, and security">
      <div className="max-w-4xl mx-auto space-y-6">
        
        {/* Profile Section */}
        <div className="card-premium p-6">
          <div className="flex items-start gap-4">
            <div className="w-16 h-16 rounded-full bg-linear-to-br from-primary to-accent flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-primary/20">
              {user?.full_name?.charAt(0) ?? "U"}
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-foreground">{user?.full_name}</h2>
              <p className="text-muted-foreground">{user?.email}</p>
              <div className="flex gap-2 mt-3">
                <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-primary/10 text-primary border border-primary/20">
                  {user?.role}
                </span>
                <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-surface-2 text-muted-foreground border border-border-default">
                  Plant {user?.plant_id}
                </span>
              </div>
            </div>
            <button className="px-4 py-2 bg-surface-2 hover:bg-surface-3 transition-colors border border-border-default rounded-lg text-sm font-medium">
              Edit Profile
            </button>
          </div>
        </div>

        {/* Settings Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SettingsCard 
            icon={<Shield className="w-5 h-5 text-accent" />}
            title="Security & Auth"
            description="Manage passwords, 2FA, and active sessions"
          />
          <SettingsCard 
            icon={<Bell className="w-5 h-5 text-warning" />}
            title="Notifications"
            description="Configure email alerts and system push notifications"
          />
          <SettingsCard 
            icon={<Database className="w-5 h-5 text-success" />}
            title="Data Management"
            description="Manage knowledge graph embeddings and caching"
          />
          <SettingsCard 
            icon={<Palette className="w-5 h-5 text-primary" />}
            title="Appearance"
            description="Customize UI themes and layout densities"
          />
        </div>

        {/* API Keys (Mock) */}
        <div className="card-premium p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Key className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">API Keys</h3>
              <p className="text-sm text-muted-foreground">Manage keys for external API integrations</p>
            </div>
          </div>
          
          <div className="flex items-center justify-between p-4 bg-background border border-border-default rounded-lg">
            <div>
              <p className="text-sm font-medium text-foreground">Production API Key</p>
              <p className="text-xs text-muted-foreground font-mono mt-1">sk-live-••••••••••••••••</p>
            </div>
            <button className="text-sm text-primary hover:text-primary-hover font-medium">Revoke</button>
          </div>
          <button className="mt-4 px-4 py-2 bg-primary hover:bg-primary-hover text-white transition-colors rounded-lg text-sm font-medium w-full md:w-auto">
            Generate New Key
          </button>
        </div>

      </div>
    </DashboardLayout>
  );
}

function SettingsCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <div className="card-premium p-5 hover:border-primary/50 transition-colors cursor-pointer group">
      <div className="flex items-start gap-4">
        <div className="p-2.5 bg-background border border-border-default rounded-xl group-hover:scale-110 transition-transform">
          {icon}
        </div>
        <div>
          <h3 className="font-semibold text-foreground mb-1 group-hover:text-primary transition-colors">{title}</h3>
          <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
        </div>
      </div>
    </div>
  );
}
