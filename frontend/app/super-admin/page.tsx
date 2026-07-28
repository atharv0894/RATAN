"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import SystemHealthCards from "./components/SystemHealthCards";
import TenantResourceTable from "./components/TenantResourceTable";
import { ShieldAlert, ActivitySquare, LogOut } from "lucide-react";

export default function SystemAdminPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!isLoading && user && user.role !== "SuperAdmin") {
      router.push("/dashboard");
    }
  }, [user, isLoading, router]);

  if (!mounted || isLoading || !user || user.role !== "SuperAdmin") {
    return null; // Don't flash UI to unauthorized users
  }

  return (
    <div className="min-h-screen bg-bg text-text-primary p-4 md:p-8 font-sans selection:bg-primary/30">
      <div className="max-w-[1600px] mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-surface border border-border-default p-6 rounded-2xl shadow-card relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-accent/5 rounded-full blur-3xl pointer-events-none"></div>
          <div className="relative z-10">
            <h1 className="text-2xl md:text-3xl font-bold flex items-center gap-3 tracking-tight text-foreground">
              <div className="w-10 h-10 rounded-xl bg-linear-to-br from-primary to-accent flex items-center justify-center shadow-md">
                <ShieldAlert className="w-5 h-5 text-white" />
              </div>
              Platform Operations Center
            </h1>
            <p className="text-text-secondary mt-2 text-sm max-w-2xl">
              Strictly isolated observability dashboard. Monitor system health, queue statuses, resource consumption, and enforce platform-wide policies.
            </p>
          </div>
          <div className="flex items-center gap-4 relative z-10">
            <div className="hidden md:flex items-center gap-2 bg-success/10 text-success px-4 py-2 rounded-xl text-sm font-medium border border-success/20">
              <ActivitySquare className="w-4 h-4 animate-pulse" />
              Live Telemetry Active
            </div>
            <button
              onClick={() => {
                logout();
                router.push("/super-admin/login");
              }}
              className="flex items-center gap-2 bg-danger/10 hover:bg-danger/20 text-danger px-4 py-2 rounded-xl text-sm font-medium border border-danger/20 transition-all hover:shadow-glow"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </div>

        {/* Real-time System Metrics */}
        <div className="space-y-4">
          <div className="flex items-center justify-between px-2">
            <h2 className="text-lg font-semibold text-text-primary tracking-tight">Infrastructure Health</h2>
            <span className="text-xs text-text-secondary">Auto-refreshing every 15s</span>
          </div>
          <SystemHealthCards />
        </div>

        {/* Tenant Resource Footprint */}
        <div className="space-y-4 pt-4">
          <div className="flex items-center justify-between px-2">
            <h2 className="text-lg font-semibold text-text-primary tracking-tight">Tenant Resource Footprint</h2>
          </div>
          <TenantResourceTable />
        </div>

      </div>
    </div>
  );
}
