"use client";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/lib/api";
import { formatDateTime, cn } from "@/lib/utils";
import { useState } from "react";
import { Activity, Search } from "lucide-react";

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={cn("status-badge text-[11px]", status === "success" ? "bg-success/10 text-success" : status === "error" ? "bg-danger/10 text-danger" : "bg-muted/10 text-muted-foreground")}>
      {status}
    </span>
  );
}

export default function AuditLogsPage() {
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState("");
  const limit = 30;

  const { data, isLoading } = useQuery({
    queryKey: ["audit-logs", page],
    queryFn: () => adminApi.listAuditLogs(page * limit, limit).then((r) => r.data.data),
    refetchInterval: 15000,
  });

  const logs: {
    id: string; user_id: string | null; endpoint: string; action: string;
    resource: string; status: string; ip_address: string; execution_time_ms: number; created_at: number;
  }[] = data ?? [];

  const filtered = search
    ? logs.filter((l) => l.action.includes(search.toUpperCase()) || l.resource.toLowerCase().includes(search.toLowerCase()) || l.endpoint?.includes(search))
    : logs;

  return (
    <DashboardLayout title="Audit Logs" subtitle="Immutable record of all system actions">
      <div className="space-y-4 animate-fade-in">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search logs..." className="input-field pl-10 h-9 text-sm" />
          </div>
          <div className="text-xs text-muted-foreground bg-surface-2 px-3 py-2 rounded-xl border border-border-default">
            Auto-refresh 15s
          </div>
        </div>

        <div className="card-premium overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-default bg-surface-2/50">
                  {["Time", "Action", "Resource", "Endpoint", "Status", "Latency", "IP"].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  Array.from({ length: 10 }).map((_, i) => (
                    <tr key={i} className="border-b border-border-default">
                      {Array.from({ length: 7 }).map((_, j) => <td key={j} className="px-4 py-3"><div className="skeleton h-4 rounded w-20" /></td>)}
                    </tr>
                  ))
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-12 text-center text-muted-foreground">
                      <Activity className="w-8 h-8 mx-auto mb-2 opacity-30" />
                      No logs found
                    </td>
                  </tr>
                ) : filtered.map((log) => (
                  <tr key={log.id} className="border-b border-border-default/50 hover:bg-surface-2/30 transition-colors font-mono text-xs">
                    <td className="px-4 py-2.5 text-muted-foreground whitespace-nowrap">{formatDateTime(log.created_at)}</td>
                    <td className="px-4 py-2.5">
                      <span className="font-medium text-accent">{log.action}</span>
                    </td>
                    <td className="px-4 py-2.5 max-w-40 truncate text-foreground-2">{log.resource}</td>
                    <td className="px-4 py-2.5 text-muted-foreground max-w-50 truncate">{log.endpoint}</td>
                    <td className="px-4 py-2.5"><StatusBadge status={log.status} /></td>
                    <td className="px-4 py-2.5 text-muted-foreground">{log.execution_time_ms}ms</td>
                    <td className="px-4 py-2.5 text-muted-foreground">{log.ip_address}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-3 border-t border-border-default flex justify-between items-center">
            <p className="text-xs text-muted-foreground">{filtered.length} entries</p>
            <div className="flex gap-2">
              <button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0} className="text-xs btn-secondary px-3 py-1.5 disabled:opacity-40">Previous</button>
              <button onClick={() => setPage((p) => p + 1)} disabled={logs.length < limit} className="text-xs btn-secondary px-3 py-1.5 disabled:opacity-40">Next</button>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
