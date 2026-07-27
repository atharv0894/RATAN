"use client";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { useQuery } from "@tanstack/react-query";
import { jobsApi } from "@/lib/api";
import { ProcessingJob } from "@/types";
import { cn, formatRelativeTime, getStatusColor } from "@/lib/utils";
import { Loader2, RotateCcw } from "lucide-react";
import { useState } from "react";

export default function JobsPage() {
  const [statusFilter, setStatusFilter] = useState("all");
  const [page, setPage] = useState(1);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["jobs", page, statusFilter],
    queryFn: () => jobsApi.list(page, 30, statusFilter === "all" ? undefined : statusFilter).then((r) => r.data),
    refetchInterval: 10000,
  });

  const jobs: ProcessingJob[] = data?.data ?? [];
  const meta = data?.meta;

  return (
    <DashboardLayout title="Processing Queue" subtitle="Monitor document indexing and processing jobs">
      <div className="space-y-4 animate-fade-in">
        <div className="flex items-center gap-3">
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="input-field h-9 text-sm w-44">
            {["all", "QUEUED", "PROCESSING", "EMBEDDING", "INDEXING", "COMPLETED", "FAILED", "CANCELLED"].map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button onClick={() => refetch()} className="btn-secondary h-9 px-3 flex items-center gap-2 text-sm">
            <RotateCcw className="w-3.5 h-3.5" /> Refresh
          </button>
          <span className="text-xs text-muted-foreground ml-auto">Auto-refresh every 10s</span>
        </div>

        <div className="card-premium overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm whitespace-nowrap">
              <thead className="sticky top-0 bg-surface z-10">
                <tr className="border-b border-border-default bg-surface-2/50">
                  <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Job ID</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider hidden sm:table-cell">Type</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider hidden md:table-cell">Target</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider hidden lg:table-cell">Retries</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider hidden sm:table-cell">Started</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i} className="border-b border-border-default">
                      <td className="px-4 py-3"><div className="skeleton h-4 rounded w-20" /></td>
                      <td className="px-4 py-3 hidden sm:table-cell"><div className="skeleton h-4 rounded w-16" /></td>
                      <td className="px-4 py-3 hidden md:table-cell"><div className="skeleton h-4 rounded w-20" /></td>
                      <td className="px-4 py-3"><div className="skeleton h-4 rounded w-20" /></td>
                      <td className="px-4 py-3 hidden lg:table-cell"><div className="skeleton h-4 rounded w-8" /></td>
                      <td className="px-4 py-3 hidden sm:table-cell"><div className="skeleton h-4 rounded w-16" /></td>
                    </tr>
                  ))
                ) : jobs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-12 text-center text-muted-foreground">
                      <Loader2 className="w-8 h-8 mx-auto mb-2 opacity-30" />
                      No processing jobs
                    </td>
                  </tr>
                ) : jobs.map((job) => (
                  <tr key={job.id} className="border-b border-border-default/60 hover:bg-surface-2/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{job.id.slice(0, 8)}...</td>
                    <td className="px-4 py-3 text-xs text-accent hidden sm:table-cell">{job.target_type}</td>
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground hidden md:table-cell">{job.target_id.slice(0, 8)}...</td>
                    <td className="px-4 py-3">
                      <span className={cn("status-badge text-[11px]", getStatusColor(job.status))}>
                        {job.status === "PROCESSING" && <Loader2 className="w-2.5 h-2.5 inline mr-1 animate-spin" />}
                        {job.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground text-center hidden lg:table-cell">{job.retry_count}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground whitespace-nowrap hidden sm:table-cell">
                      {job.started_at ? formatRelativeTime(job.started_at) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {meta && (
            <div className="px-4 py-3 border-t border-border-default flex justify-between items-center">
              <p className="text-xs text-muted-foreground">Total: {meta.total} jobs</p>
              <div className="flex gap-2">
                <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="text-xs btn-secondary px-3 py-1.5 disabled:opacity-40">Previous</button>
                <button onClick={() => setPage((p) => p + 1)} disabled={page === meta.total_pages} className="text-xs btn-secondary px-3 py-1.5 disabled:opacity-40">Next</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
