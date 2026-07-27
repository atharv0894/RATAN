"use client";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { Server, Database, Settings as SettingsIcon, Shield, Cloud, Activity, RefreshCw } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { dashboardApi } from "@/lib/api";
import { useEffect, useState } from "react";
import { toast } from "sonner";

interface SystemSetting {
  id: string;
  setting_value: string;
  description: string;
}

export default function SystemSettingsPage() {
  const { user } = useAuth();
  const [settings, setSettings] = useState<SystemSetting[]>([]);
  const [loading, setLoading] = useState(true);
  const [flushing, setFlushing] = useState(false);

  const loadSettings = async () => {
    try {
      const res = await dashboardApi.system();
      setSettings(res.data.data);
    } catch (err: any) {
      toast.error("Failed to load system settings");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const handleUpdate = async (id: string, currentValue: string) => {
    const newValue = window.prompt("Enter new configuration value:", currentValue);
    if (newValue && newValue !== currentValue) {
      try {
        await dashboardApi.updateSystemSetting(id, newValue);
        toast.success(`Setting '${id}' updated successfully`);
        loadSettings();
      } catch (err: any) {
        toast.error(err.response?.data?.error?.message || "Failed to update setting");
      }
    }
  };

  const handleFlushCache = async () => {
    if (!window.confirm("Are you sure you want to flush all system caches? This may temporarily impact performance.")) return;
    setFlushing(true);
    try {
      const res = await dashboardApi.flushSystemCache();
      toast.success(res.data.data.status);
    } catch (err: any) {
      toast.error("Failed to flush cache");
    } finally {
      setFlushing(false);
    }
  };

  const getSettingValue = (id: string) => {
    const s = settings.find(x => x.id === id);
    return s ? s.setting_value : "Unknown";
  };

  return (
    <DashboardLayout title="System Settings" subtitle="Platform administration and global configurations">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Banner */}
        <div className="card-premium p-6 border-l-4 border-l-primary relative overflow-hidden group">
          <div className="absolute inset-0 bg-primary/5 group-hover:bg-primary/10 transition-colors pointer-events-none" />
          <div className="relative z-10 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-foreground">Admin Console</h2>
              <p className="text-muted-foreground mt-1">
                You are logged in as <span className="font-semibold text-primary">{user?.role}</span>. Changes here affect the entire platform.
              </p>
            </div>
            <div className="p-3 bg-surface-2 rounded-lg border border-border-default">
              <Server className="w-6 h-6 text-primary" />
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center p-12">
            <RefreshCw className="w-6 h-6 text-primary animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <ConfigCard 
              icon={<Database className="w-5 h-5 text-accent" />}
              title="Database Configuration"
              status={getSettingValue('db_config')}
              description="Manage connection pools, backup schedules, and retention policies."
              onClick={() => handleUpdate('db_config', getSettingValue('db_config'))}
            />
            <ConfigCard 
              icon={<Cloud className="w-5 h-5 text-primary" />}
              title="Storage Provider"
              status={getSettingValue('storage_provider')}
              description="Configure bucket policies, CDN caching, and max file sizes."
              onClick={() => handleUpdate('storage_provider', getSettingValue('storage_provider'))}
            />
            <ConfigCard 
              icon={<Shield className="w-5 h-5 text-warning" />}
              title="Security & RBAC"
              status={getSettingValue('security_rbac')}
              description="Define roles, IP whitelists, and OAuth2/SAML SSO integrations."
              onClick={() => handleUpdate('security_rbac', getSettingValue('security_rbac'))}
            />
            <ConfigCard 
              icon={<SettingsIcon className="w-5 h-5 text-success" />}
              title="LLM Pipeline"
              status={getSettingValue('llm_pipeline')}
              description="Manage model fallback chains, temperature, and token limits."
              onClick={() => handleUpdate('llm_pipeline', getSettingValue('llm_pipeline'))}
            />
            <ConfigCard 
              icon={<Activity className="w-5 h-5 text-danger" />}
              title="Telemetry"
              status={getSettingValue('telemetry')}
              description="Configure audit log retention and performance tracing."
              onClick={() => handleUpdate('telemetry', getSettingValue('telemetry'))}
            />
          </div>
        )}

        {/* Global Action */}
        <div className="card-premium p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="font-semibold text-foreground">Flush Cache</h3>
            <p className="text-sm text-muted-foreground mt-1">Clears Redis cache for all tenants. Use during high memory pressure.</p>
          </div>
          <button 
            onClick={handleFlushCache}
            disabled={flushing}
            className="w-full sm:w-auto px-4 py-2 bg-danger/10 text-danger hover:bg-danger hover:text-white border border-danger/20 transition-colors rounded-lg text-sm font-medium disabled:opacity-50 flex justify-center items-center gap-2"
          >
            {flushing ? <RefreshCw className="w-4 h-4 animate-spin" /> : null}
            Clear All Caches
          </button>
        </div>

      </div>
    </DashboardLayout>
  );
}

function ConfigCard({ icon, title, description, status, onClick }: { icon: React.ReactNode, title: string, description: string, status: string, onClick: () => void }) {
  return (
    <div onClick={onClick} className="card-premium p-5 hover:border-primary/50 transition-colors cursor-pointer group flex flex-col h-full">
      <div className="flex items-start justify-between mb-4">
        <div className="p-2.5 bg-background border border-border-default rounded-xl group-hover:scale-110 transition-transform">
          {icon}
        </div>
        <span className="text-[10px] px-2 py-1 rounded-full bg-surface-2 border border-border-default font-medium text-muted-foreground truncate max-w-30">
          {status}
        </span>
      </div>
      <div>
        <h3 className="font-semibold text-foreground mb-1 group-hover:text-primary transition-colors">{title}</h3>
        <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
      </div>
      <div className="mt-auto pt-4 flex items-center text-xs font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity">
        Edit Configuration <span className="ml-1">→</span>
      </div>
    </div>
  );
}
