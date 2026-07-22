"use client";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/lib/api";
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import { formatBytes } from "@/lib/utils";
import { BarChart3, Brain, HardDrive, Activity } from "lucide-react";

const COLORS = ["#2563EB", "#06B6D4", "#22C55E", "#F59E0B", "#EF4444", "#8B5CF6"];

// mockData removed - now using live data from backend

const ChartCard = ({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: React.ReactNode }) => (
  <div className="card-premium p-5">
    <div className="flex items-center gap-2 mb-4">
      <Icon className="w-4 h-4 text-primary" />
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
    </div>
    {children}
  </div>
);

export default function AnalyticsPage() {
  const { data: docData } = useQuery({ queryKey: ["dash-docs"], queryFn: () => dashboardApi.documents().then((r) => r.data.data) });
  const { data: aiData } = useQuery({ queryKey: ["dash-ai"], queryFn: () => dashboardApi.ai().then((r) => r.data.data) });
  const { data: storageData } = useQuery({ queryKey: ["dash-storage"], queryFn: () => dashboardApi.storage().then((r) => r.data.data) });
  const { data: searchData } = useQuery({ queryKey: ["dash-search"], queryFn: () => dashboardApi.search().then((r) => r.data.data) });

  const categoryData = docData?.by_category?.map((c: { category: string; count: number }) => ({ name: c.category || "Uncategorized", value: c.count })) ?? [];
  const uploadTrends = docData?.upload_trends ?? [];
  const queryTrends = aiData?.query_trends ?? [];

  return (
    <DashboardLayout title="Analytics" subtitle="Platform-wide performance and usage metrics">
      <div className="space-y-6 animate-fade-in">

        {/* KPI Row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: "Total Documents", value: docData?.total ?? "—", unit: "docs", icon: BarChart3, color: "text-primary" },
            { label: "AI Messages", value: aiData?.total_messages?.toLocaleString() ?? "—", unit: "messages", icon: Brain, color: "text-accent" },
            { label: "Avg. Confidence", value: aiData?.avg_confidence ? `${(aiData.avg_confidence * 100).toFixed(1)}%` : "—", unit: "", icon: Activity, color: "text-success" },
            { label: "Storage Used", value: storageData ? formatBytes(storageData.total_storage_bytes) : "—", unit: "", icon: HardDrive, color: "text-warning" },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="card-premium p-4">
              <div className="flex items-center gap-2 mb-2">
                <Icon className={cn("w-4 h-4", color)} />
                <span className="text-xs text-muted-foreground">{label}</span>
              </div>
              <p className="text-2xl font-bold text-foreground">{value}</p>
            </div>
          ))}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ChartCard title="Document Uploads (14 Days)" icon={BarChart3}>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={uploadTrends}>
                <XAxis dataKey="day" stroke="#374151" tick={{ fill: "#9CA3AF", fontSize: 10 }} />
                <YAxis stroke="#374151" tick={{ fill: "#9CA3AF", fontSize: 10 }} />
                <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border-default)", borderRadius: "8px", fontSize: "11px", color: "var(--foreground)" }} />
                <Bar dataKey="uploads" fill="#2563EB" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="AI Query Volume (14 Days)" icon={Brain}>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={queryTrends}>
                <defs>
                  <linearGradient id="gQ" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#06B6D4" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" stroke="#374151" tick={{ fill: "#9CA3AF", fontSize: 10 }} />
                <YAxis stroke="#374151" tick={{ fill: "#9CA3AF", fontSize: 10 }} />
                <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border-default)", borderRadius: "8px", fontSize: "11px", color: "var(--foreground)" }} />
                <Area type="monotone" dataKey="queries" stroke="#06B6D4" fill="url(#gQ)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Documents by Category" icon={BarChart3}>
            {categoryData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={categoryData} cx="50%" cy="50%" outerRadius={70} dataKey="value" fontSize={10}>
                    {categoryData.map((_: unknown, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border-default)", borderRadius: "8px", fontSize: "11px", color: "var(--foreground)" }} />
                  <Legend iconSize={8} wrapperStyle={{ fontSize: "11px" }} />
                </PieChart>
              </ResponsiveContainer>
            ) : <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">No category data</div>}
          </ChartCard>

          <ChartCard title="Response Latency (14 Days)" icon={Activity}>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={queryTrends}>
                <defs>
                  <linearGradient id="gL" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#F59E0B" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" stroke="#374151" tick={{ fill: "#9CA3AF", fontSize: 10 }} />
                <YAxis stroke="#374151" tick={{ fill: "#9CA3AF", fontSize: 10 }} />
                <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border-default)", borderRadius: "8px", fontSize: "11px", color: "var(--foreground)" }} />
                <Area type="monotone" dataKey="latency" stroke="#F59E0B" fill="url(#gL)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Storage & Vectors */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {[
            { label: "Total Storage", value: storageData ? formatBytes(storageData.total_storage_bytes) : "—" },
            { label: "Document Versions", value: storageData?.total_versions?.toLocaleString() ?? "—" },
            { label: "Total Chunks", value: storageData?.total_chunks?.toLocaleString() ?? "—" },
            { label: "Total Vectors", value: storageData?.total_vectors?.toLocaleString() ?? "—" },
            { label: "Total AI Tokens", value: aiData?.total_tokens?.toLocaleString() ?? "—" },
            { label: "Search Queries", value: searchData?.total_searches?.toLocaleString() ?? "—" },
          ].map(({ label, value }) => (
            <div key={label} className="card-premium p-4">
              <p className="text-xs text-muted-foreground uppercase tracking-wider">{label}</p>
              <p className="text-2xl font-bold text-foreground mt-1">{value}</p>
            </div>
          ))}
        </div>

      </div>
    </DashboardLayout>
  );
}

function cn(...args: (string | boolean | undefined)[]) {
  return args.filter(Boolean).join(" ");
}
