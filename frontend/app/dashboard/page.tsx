"use client";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { cn, formatBytes, formatRelativeTime, formatUptime } from "@/lib/utils";
import {
  FileText, Users, MessageSquare, HardDrive, Cpu, Activity,
  AlertTriangle, Database, Zap, Brain,
  TrendingUp, ArrowUpRight, Upload,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell
} from "recharts";
import Link from "next/link";

function StatCard({ label, value, sub, icon: Icon, trend, color = "primary" }: {
  label: string; value: string | number; sub?: string;
  icon: React.ElementType; trend?: string; color?: "primary" | "accent" | "success" | "warning" | "danger";
}) {
  const colors = {
    primary: "from-primary/20 to-primary/5 border-primary/20",
    accent: "from-accent/20 to-accent/5 border-accent/20",
    success: "from-success/20 to-success/5 border-success/20",
    warning: "from-warning/20 to-warning/5 border-warning/20",
    danger: "from-danger/20 to-danger/5 border-danger/20",
  };
  const iconColors = { primary: "text-primary", accent: "text-accent", success: "text-success", warning: "text-warning", danger: "text-danger" };

  return (
    <div className={cn("card-premium p-5 bg-linear-to-br", colors[color], "border")}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">{label}</p>
          <p className="text-3xl font-bold text-white mt-2">{value}</p>
          {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
        </div>
        <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center", `bg-${color}/10`)}>
          <Icon className={cn("w-5 h-5", iconColors[color])} />
        </div>
      </div>
      {trend && (
        <div className="mt-3 flex items-center gap-1 text-success text-xs">
          <TrendingUp className="w-3 h-3" />
          <span>{trend}</span>
        </div>
      )}
    </div>
  );
}

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span className={cn("inline-block w-2 h-2 rounded-full", ok ? "bg-success" : "bg-danger")} />
  );
}

const COLORS = ["#2563EB", "#06B6D4", "#22C55E", "#F59E0B", "#EF4444", "#8B5CF6"];

export default function DashboardPage() {
  const { user } = useAuth();

  const { data: overviewData } = useQuery({ queryKey: ["dashboard-overview"], queryFn: () => dashboardApi.overview().then(r => r.data.data) });
  const { data: storageData } = useQuery({ queryKey: ["dashboard-storage"], queryFn: () => dashboardApi.storage().then(r => r.data.data) });
  const { data: aiData } = useQuery({ queryKey: ["dashboard-ai"], queryFn: () => dashboardApi.ai().then(r => r.data.data) });
  const { data: processingData } = useQuery({ queryKey: ["dashboard-processing"], queryFn: () => dashboardApi.processing().then(r => r.data.data) });
  const { data: systemData } = useQuery({ queryKey: ["dashboard-system"], queryFn: () => dashboardApi.system().then(r => r.data.data), refetchInterval: 30000 });
  const { data: activityData } = useQuery({ queryKey: ["dashboard-activity"], queryFn: () => dashboardApi.activity(15).then(r => r.data.data.activity) });
  const { data: alertsData } = useQuery({ queryKey: ["dashboard-alerts"], queryFn: () => dashboardApi.alerts().then(r => r.data.data.alerts) });
  const { data: docData } = useQuery({ queryKey: ["dashboard-docs"], queryFn: () => dashboardApi.documents().then(r => r.data.data) });

  const statusChartData = docData?.by_status?.map((s: { status: string; count: number }) => ({ name: s.status, value: s.count })) ?? [];

  const mockAreaData = [
    { day: "Mon", queries: 120, uploads: 15 },
    { day: "Tue", queries: 140, uploads: 12 },
    { day: "Wed", queries: 110, uploads: 18 },
    { day: "Thu", queries: 90, uploads: 10 },
    { day: "Fri", queries: 150, uploads: 22 },
    { day: "Sat", queries: 180, uploads: 25 },
    { day: "Sun", queries: 130, uploads: 14 },
  ];

  return (
    <DashboardLayout title="Dashboard" subtitle={`Welcome back, ${user?.full_name?.split(" ")[0] ?? "User"}`}>
      <div className="space-y-6 animate-fade-in">

        {/* Alerts */}
        {alertsData && alertsData.length > 0 && (
          <div className="space-y-2">
            {alertsData.map((alert: { severity: string; message: string }, i: number) => (
              <div key={i} className={cn("flex items-center gap-3 px-4 py-3 rounded-xl border text-sm", alert.severity === "Critical" ? "bg-danger/5 border-danger/20 text-danger" : "bg-warning/5 border-warning/20 text-warning")}>
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{alert.message}</span>
              </div>
            ))}
          </div>
        )}

        {/* Stat Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Documents" value={overviewData?.total_documents ?? "—"} icon={FileText} color="primary" trend="Knowledge base" />
          <StatCard label="Active Users" value={overviewData?.active_users ?? "—"} icon={Users} color="accent" />
          <StatCard label="AI Chats" value={overviewData?.total_chats ?? "—"} icon={MessageSquare} color="success" />
          <StatCard label="Storage Used" value={formatBytes((storageData?.total_storage_bytes ?? 0))} icon={HardDrive} color="warning" />
        </div>

        {/* AI & Vector Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Total Chunks" value={storageData?.total_chunks?.toLocaleString() ?? "—"} icon={Database} color="accent" />
          <StatCard label="Vectors" value={storageData?.total_vectors?.toLocaleString() ?? "—"} icon={Cpu} color="primary" />
          <StatCard label="AI Messages" value={aiData?.total_messages?.toLocaleString() ?? "—"} icon={Brain} color="success" />
          <StatCard label="Tokens Used" value={aiData?.total_tokens?.toLocaleString() ?? "—"} icon={Zap} color="warning" />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Area Chart */}
          <div className="lg:col-span-2 card-premium p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Platform Activity (7 Days)</h3>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={mockAreaData}>
                <defs>
                  <linearGradient id="gQueries" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563EB" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gUploads" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#06B6D4" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" stroke="#374151" tick={{ fill: "#9CA3AF", fontSize: 11 }} />
                <YAxis stroke="#374151" tick={{ fill: "#9CA3AF", fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#111827", border: "1px solid #1E2D45", borderRadius: "8px", fontSize: "12px" }} />
                <Area type="monotone" dataKey="queries" stroke="#2563EB" fill="url(#gQueries)" strokeWidth={2} />
                <Area type="monotone" dataKey="uploads" stroke="#06B6D4" fill="url(#gUploads)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Pie Chart */}
          <div className="card-premium p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Document Status</h3>
            {statusChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={statusChartData} cx="50%" cy="50%" outerRadius={70} dataKey="value" label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`} labelLine={false} fontSize={10} fill="#8884d8">
                    {statusChartData.map((_: unknown, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#111827", border: "1px solid #1E2D45", borderRadius: "8px", fontSize: "12px" }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">No data yet</div>
            )}
          </div>
        </div>

        {/* System Health + Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* System Health */}
          <div className="card-premium p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground">System Health</h3>
              <span className={cn("status-badge", systemData?.status === "Healthy" ? "status-ready" : "status-failed")}>
                {systemData?.status ?? "Unknown"}
              </span>
            </div>
            <div className="space-y-3">
              {[
                { label: "CPU Usage", value: systemData?.cpu_percent ?? 0, suffix: "%" },
                { label: "Memory Usage", value: systemData?.memory_percent ?? 0, suffix: "%" },
              ].map(({ label, value, suffix }) => (
                <div key={label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">{label}</span>
                    <span className="text-foreground-2 font-medium">{value.toFixed(1)}{suffix}</span>
                  </div>
                  <div className="h-1.5 bg-border-default rounded-full overflow-hidden">
                    <div className={cn("h-full rounded-full transition-all", value > 80 ? "bg-danger" : value > 60 ? "bg-warning" : "bg-primary")} style={{ width: `${value}%` }} />
                  </div>
                </div>
              ))}
              <div className="grid grid-cols-2 gap-3 pt-2">
                {[
                  { label: "Database", ok: true, detail: "TiDB Cloud" },
                  { label: "Qdrant", ok: systemData?.qdrant_status === "Connected", detail: systemData?.qdrant_status },
                  { label: "Backblaze B2", ok: systemData?.b2_status === "Connected", detail: systemData?.b2_status },
                  { label: "Uptime", ok: true, detail: formatUptime(systemData?.uptime_seconds ?? 0) },
                ].map(({ label, ok, detail }) => (
                  <div key={label} className="bg-surface-2 rounded-xl p-3 flex items-center gap-2">
                    <StatusDot ok={ok} />
                    <div>
                      <p className="text-xs font-medium text-foreground">{label}</p>
                      <p className="text-[10px] text-muted-foreground">{detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="card-premium p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-foreground">Recent Activity</h3>
              <Link href="/dashboard/admin/audit" className="text-xs text-primary hover:text-accent flex items-center gap-1">
                View all <ArrowUpRight className="w-3 h-3" />
              </Link>
            </div>
            <div className="space-y-1">
              {activityData?.slice(0, 8).map((act: { action: string; resource: string; status: string; created_at: number; user_name?: string }, i: number) => (
                <div key={i} className="flex items-center gap-3 py-2 border-b border-border-default/50 last:border-0">
                  <div className={cn("w-1.5 h-1.5 rounded-full shrink-0", act.status === "success" ? "bg-success" : act.status === "error" ? "bg-danger" : "bg-muted-foreground")} />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-foreground truncate">
                      {act.action} — <span className="text-muted-foreground">{act.resource}</span>
                    </p>
                    <p className="text-[10px] text-muted-foreground/60">{act.user_name ?? "System"}</p>
                  </div>
                  <span className="text-[10px] text-muted-foreground shrink-0">{formatRelativeTime(act.created_at)}</span>
                </div>
              )) ?? (
                <div className="py-8 text-center text-muted-foreground text-sm">No recent activity</div>
              )}
            </div>
          </div>
        </div>

        {/* Processing Queue Summary */}
        <div className="card-premium p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground">Processing Queue</h3>
            <Link href="/dashboard/jobs" className="text-xs text-primary hover:text-accent flex items-center gap-1">
              Manage <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              { label: "Queued", value: processingData?.queued ?? 0, color: "text-accent", bg: "bg-accent/10" },
              { label: "Processing", value: processingData?.processing ?? 0, color: "text-warning", bg: "bg-warning/10" },
              { label: "Completed", value: processingData?.completed ?? 0, color: "text-success", bg: "bg-success/10" },
              { label: "Failed", value: processingData?.failed ?? 0, color: "text-danger", bg: "bg-danger/10" },
            ].map(({ label, value, color, bg }) => (
              <div key={label} className={cn("rounded-xl p-4 text-center", bg)}>
                <p className={cn("text-2xl font-bold", color)}>{value}</p>
                <p className="text-xs text-muted-foreground mt-1">{label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="card-premium p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              { label: "Upload Document", href: "/dashboard/upload", icon: Upload, color: "text-primary" },
              { label: "Ask AI Assistant", href: "/dashboard/chat", icon: Brain, color: "text-accent" },
              { label: "View Documents", href: "/dashboard/documents", icon: FileText, color: "text-success" },
              { label: "Analytics", href: "/dashboard/analytics", icon: Activity, color: "text-warning" },
            ].map(({ label, href, icon: Icon, color }) => (
              <Link key={href} href={href} className="card-premium p-4 flex items-center gap-3 hover:border-primary/30 transition-all">
                <Icon className={cn("w-5 h-5", color)} />
                <span className="text-sm font-medium text-foreground-2">{label}</span>
              </Link>
            ))}
          </div>
        </div>

      </div>
    </DashboardLayout>
  );
}
