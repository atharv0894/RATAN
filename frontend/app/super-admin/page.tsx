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
    <div className="min-h-screen bg-black text-gray-100 p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold flex items-center gap-3 tracking-tight">
              <ShieldAlert className="w-8 h-8 text-blue-500 shrink-0" />
              Super Admin Control Plane
            </h1>
            <p className="text-gray-400 mt-2 text-sm max-w-2xl">
              Strictly isolated observability dashboard. Monitor system health, resource consumption, and enforce tenant-level suspensions globally.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 sm:gap-4 w-full md:w-auto">
            <div className="flex flex-1 md:flex-none items-center justify-center gap-2 bg-blue-500/10 text-blue-400 px-4 py-2 rounded-full text-sm font-medium border border-blue-500/20">
              <ActivitySquare className="w-4 h-4 animate-pulse shrink-0" />
              <span className="truncate">Live Telemetry Active</span>
            </div>
            <button
              onClick={() => {
                logout();
                router.push("/super-admin/login");
              }}
              className="flex flex-1 md:flex-none items-center justify-center gap-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 px-4 py-2 rounded-full text-sm font-medium border border-red-500/20 transition-colors"
            >
              <LogOut className="w-4 h-4 shrink-0" />
              Sign Out
            </button>
          </div>
        </div>

        {/* Real-time System Metrics */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-200">Infrastructure Health</h2>
          <SystemHealthCards />
        </div>

        {/* Tenant Resource Footprint */}
        <div className="space-y-4 pt-4">
          <TenantResourceTable />
        </div>

      </div>
    </div>
  );
}
