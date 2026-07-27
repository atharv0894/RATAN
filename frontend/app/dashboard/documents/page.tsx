"use client";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { documentsApi } from "@/lib/api";
import { Document } from "@/types";
import { useState } from "react";
import { cn, getStatusColor, truncate } from "@/lib/utils";
import { toast } from "sonner";
import {
  Search, Trash2, RotateCcw,
  FileText, ChevronLeft, ChevronRight, Eye,
} from "lucide-react";
import Link from "next/link";

function DocStatusBadge({ status }: { status: string }) {
  return <span className={cn("status-badge text-[11px]", getStatusColor(status))}>{status}</span>;
}

function SkeletonRow() {
  return (
    <tr className="border-b border-border-default">
      {Array.from({ length: 6 }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="skeleton h-4 rounded w-24" />
        </td>
      ))}
    </tr>
  );
}

export default function DocumentsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["documents", page],
    queryFn: () => documentsApi.list(page, 20).then((r) => r.data),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => documentsApi.delete(id),
    onSuccess: () => {
      toast.success("Document deleted");
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: () => toast.error("Failed to delete document"),
  });

  const restoreMut = useMutation({
    mutationFn: (id: string) => documentsApi.restore(id),
    onSuccess: () => {
      toast.success("Document restored");
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: () => toast.error("Failed to restore document"),
  });

  const docs: Document[] = data?.data ?? [];
  const meta = data?.meta;

  const filtered = docs.filter((d) => {
    const matchSearch = !search || d.filename.toLowerCase().includes(search.toLowerCase()) || d.title?.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === "all" || d.status === statusFilter;
    return matchSearch && matchStatus;
  });

  return (
    <DashboardLayout title="Document Explorer" subtitle="Manage your knowledge base documents">
      <div className="space-y-4 animate-fade-in">

        {/* Toolbar */}
        <div className="card-premium p-4 flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by filename or title..."
              className="input-field pl-10 h-9 text-sm"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input-field h-9 text-sm w-44"
          >
            <option value="all">All Status</option>
            <option value="READY">Ready</option>
            <option value="PROCESSING">Processing</option>
            <option value="FAILED">Failed</option>
            <option value="DELETED">Deleted</option>
          </select>
          <Link href="/dashboard/upload" className="btn-primary px-4 py-2 text-sm flex items-center gap-2 h-9">
            + Upload
          </Link>
        </div>

        {/* Document Table */}
        <div className="card-premium overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm whitespace-nowrap">
              <thead className="sticky top-0 bg-surface z-10">
                <tr className="border-b border-border-default bg-surface-2/50">
                  <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Document</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Status</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider hidden md:table-cell">Version</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider hidden lg:table-cell">Chunks</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider hidden sm:table-cell">Category</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider hidden sm:table-cell">Uploaded</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                {isLoading
                  ? Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i} className="border-b border-border-default">
                      <td className="px-4 py-3"><div className="skeleton h-4 rounded w-48" /></td>
                      <td className="px-4 py-3"><div className="skeleton h-4 rounded w-16" /></td>
                      <td className="px-4 py-3 hidden md:table-cell"><div className="skeleton h-4 rounded w-8" /></td>
                      <td className="px-4 py-3 hidden lg:table-cell"><div className="skeleton h-4 rounded w-12" /></td>
                      <td className="px-4 py-3 hidden sm:table-cell"><div className="skeleton h-4 rounded w-16" /></td>
                      <td className="px-4 py-3 hidden sm:table-cell"><div className="skeleton h-4 rounded w-16" /></td>
                      <td className="px-4 py-3"><div className="skeleton h-4 rounded w-12" /></td>
                    </tr>
                  ))
                  : filtered.length === 0
                  ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-16 text-center text-muted-foreground">
                        <div className="flex flex-col items-center gap-3">
                          <FileText className="w-10 h-10 text-muted-foreground/30" />
                          <p>No documents found. <Link href="/dashboard/upload" className="text-primary hover:underline">Upload your first document</Link></p>
                        </div>
                      </td>
                    </tr>
                  )
                  : filtered.map((doc) => (
                    <tr key={doc.id} className="border-b border-border-default/60 hover:bg-surface-2/30 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                            <FileText className="w-4 h-4 text-primary" />
                          </div>
                          <div className="flex flex-col min-w-0">
                            <p className="font-medium text-foreground truncate">{truncate(doc.title || doc.filename, 40)}</p>
                            <p className="text-[11px] text-muted-foreground truncate">{doc.filename}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <DocStatusBadge status={doc.status} />
                      </td>
                      <td className="px-4 py-3 text-muted-foreground text-xs hidden md:table-cell">v{doc.version_number}</td>
                      <td className="px-4 py-3 text-muted-foreground text-xs hidden lg:table-cell">{doc.chunks.toLocaleString()}</td>
                      <td className="px-4 py-3 hidden sm:table-cell">
                        {doc.category ? (
                          <span className="text-xs bg-accent/10 text-accent px-2 py-0.5 rounded-full">{doc.category}</span>
                        ) : <span className="text-muted-foreground/40 text-xs">—</span>}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground text-xs whitespace-nowrap hidden sm:table-cell">Recent</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <button onClick={() => setSelectedDoc(doc)} className="p-1.5 rounded-lg hover:bg-surface-2 text-muted-foreground hover:text-foreground transition-colors">
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                          {doc.status !== "DELETED" ? (
                            <button
                              onClick={() => { if (confirm("Delete this document?")) deleteMut.mutate(doc.id); }}
                              className="p-1.5 rounded-lg hover:bg-danger/10 text-muted-foreground hover:text-danger transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          ) : (
                            <button onClick={() => restoreMut.mutate(doc.id)} className="p-1.5 rounded-lg hover:bg-success/10 text-muted-foreground hover:text-success transition-colors">
                              <RotateCcw className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {meta && meta.total_pages > 1 && (
            <div className="px-4 py-3 border-t border-border-default flex items-center justify-between">
              <p className="text-xs text-muted-foreground">
                Showing {(page - 1) * 20 + 1}–{Math.min(page * 20, meta.total)} of {meta.total} documents
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-1.5 rounded-lg border border-border-default text-muted-foreground hover:text-foreground disabled:opacity-40 transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-xs text-muted-foreground px-2">Page {page} of {meta.total_pages}</span>
                <button
                  onClick={() => setPage((p) => Math.min(meta.total_pages, p + 1))}
                  disabled={page === meta.total_pages}
                  className="p-1.5 rounded-lg border border-border-default text-muted-foreground hover:text-foreground disabled:opacity-40 transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Document Detail Panel */}
        {selectedDoc && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setSelectedDoc(null)}>
            <div className="card-premium p-6 w-full max-w-lg space-y-4 animate-fade-in" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">{selectedDoc.title ?? selectedDoc.filename}</h3>
                    <p className="text-xs text-muted-foreground">{selectedDoc.filename}</p>
                  </div>
                </div>
                <button onClick={() => setSelectedDoc(null)} className="text-muted-foreground hover:text-foreground text-lg">✕</button>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: "Status", value: selectedDoc.status },
                  { label: "Version", value: `v${selectedDoc.version_number}` },
                  { label: "Chunks", value: selectedDoc.chunks },
                  { label: "Category", value: selectedDoc.category ?? "—" },
                  { label: "Equipment", value: selectedDoc.equipment ?? "—" },
                  { label: "Language", value: selectedDoc.language ?? "—" },
                  { label: "Author", value: selectedDoc.author ?? "—" },
                  { label: "Latest", value: selectedDoc.is_latest ? "Yes" : "No" },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-surface-2 rounded-xl p-3">
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</p>
                    <p className="text-sm font-medium text-foreground mt-0.5">{value}</p>
                  </div>
                ))}
              </div>
              {selectedDoc.description && (
                <div>
                  <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Description</p>
                  <p className="text-sm text-foreground-2">{selectedDoc.description}</p>
                </div>
              )}
              <div className="flex gap-2 pt-2">
                <button
                  onClick={() => { navigator.clipboard.writeText(selectedDoc.id); toast.success("ID copied!"); }}
                  className="btn-secondary flex-1 text-sm py-2 flex items-center justify-center gap-2"
                >
                  Copy ID
                </button>
                {selectedDoc.status !== "DELETED" ? (
                  <button
                    onClick={() => { setSelectedDoc(null); if (confirm("Delete this document?")) deleteMut.mutate(selectedDoc.id); }}
                    className="btn-secondary flex-1 text-sm py-2 text-danger hover:text-danger flex items-center justify-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" /> Delete
                  </button>
                ) : (
                  <button
                    onClick={() => { setSelectedDoc(null); restoreMut.mutate(selectedDoc.id); }}
                    className="btn-secondary flex-1 text-sm py-2 text-success hover:text-success flex items-center justify-center gap-2"
                  >
                    <RotateCcw className="w-4 h-4" /> Restore
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
