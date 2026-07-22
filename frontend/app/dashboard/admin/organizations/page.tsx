"use client";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminApi } from "@/lib/api";
import { useState } from "react";
import { toast } from "sonner";
import { cn, formatDateTime, getStatusColor } from "@/lib/utils";
import { Building2, Plus, Pencil, Trash2, Loader2, X, Check } from "lucide-react";

function OrgCard({ org, onEdit, onDelete }: { org: { id: string; name: string; status: string; created_at: number }; onEdit: () => void; onDelete: () => void }) {
  return (
    <div className="card-premium p-4 flex items-center gap-4">
      <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
        <Building2 className="w-5 h-5 text-primary" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-foreground">{org.name}</p>
        <p className="text-xs text-muted-foreground mt-0.5">Created: {formatDateTime(org.created_at)}</p>
      </div>
      <span className={cn("status-badge", getStatusColor(org.status))}>{org.status}</span>
      <div className="flex items-center gap-1">
        <button onClick={onEdit} className="p-1.5 rounded-lg hover:bg-surface-2 text-muted-foreground hover:text-foreground transition-colors">
          <Pencil className="w-3.5 h-3.5" />
        </button>
        <button onClick={onDelete} className="p-1.5 rounded-lg hover:bg-danger/10 text-muted-foreground hover:text-danger transition-colors">
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

export default function AdminOrgsPage() {
  const qc = useQueryClient();
  const [modal, setModal] = useState<"create" | "edit" | null>(null);
  const [editOrg, setEditOrg] = useState<{ id: string; name: string } | null>(null);
  const [orgName, setOrgName] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-orgs"],
    queryFn: () => adminApi.listOrgs().then((r) => r.data.data),
  });

  const createMut = useMutation({
    mutationFn: () => adminApi.createOrg(orgName),
    onSuccess: () => { toast.success("Organization created"); qc.invalidateQueries({ queryKey: ["admin-orgs"] }); setModal(null); setOrgName(""); },
    onError: () => toast.error("Failed to create organization"),
  });

  const updateMut = useMutation({
    mutationFn: () => adminApi.updateOrg(editOrg!.id, orgName),
    onSuccess: () => { toast.success("Organization updated"); qc.invalidateQueries({ queryKey: ["admin-orgs"] }); setModal(null); },
    onError: () => toast.error("Failed to update organization"),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => adminApi.deleteOrg(id),
    onSuccess: () => { toast.success("Organization deleted"); qc.invalidateQueries({ queryKey: ["admin-orgs"] }); },
    onError: () => toast.error("Failed to delete organization"),
  });

  const orgs = data ?? [];

  return (
    <DashboardLayout title="Organizations" subtitle="Manage all tenants in the RATAN platform">
      <div className="space-y-4 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{orgs.length} total organizations</p>
          </div>
          <button onClick={() => { setModal("create"); setOrgName(""); }} className="btn-primary flex items-center gap-2 text-sm">
            <Plus className="w-4 h-4" /> New Organization
          </button>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => <div key={i} className="card-premium p-4 h-16 skeleton" />)}
          </div>
        ) : orgs.length === 0 ? (
          <div className="card-premium p-12 text-center">
            <Building2 className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
            <p className="text-muted-foreground">No organizations found.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {orgs.map((org: { id: string; name: string; status: string; created_at: number }) => (
              <OrgCard
                key={org.id}
                org={org}
                onEdit={() => { setEditOrg({ id: org.id, name: org.name }); setOrgName(org.name); setModal("edit"); }}
                onDelete={() => { if (confirm(`Delete "${org.name}"? This cannot be undone.`)) deleteMut.mutate(org.id); }}
              />
            ))}
          </div>
        )}
      </div>

      {/* Modal */}
      {modal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setModal(null)}>
          <div className="card-premium p-6 w-full max-w-md space-y-4 animate-fade-in" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-white">{modal === "create" ? "Create Organization" : "Edit Organization"}</h3>
              <button onClick={() => setModal(null)} className="text-muted-foreground hover:text-foreground"><X className="w-4 h-4" /></button>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground-2 mb-1.5">Organization Name</label>
              <input value={orgName} onChange={(e) => setOrgName(e.target.value)} placeholder="Acme Industrial" className="input-field" autoFocus />
            </div>
            <div className="flex gap-2">
              <button onClick={() => setModal(null)} className="btn-secondary flex-1 py-2.5 text-sm">Cancel</button>
              <button
                onClick={() => modal === "create" ? createMut.mutate() : updateMut.mutate()}
                disabled={!orgName.trim() || createMut.isPending || updateMut.isPending}
                className="btn-primary flex-1 py-2.5 text-sm flex items-center justify-center gap-2"
              >
                {(createMut.isPending || updateMut.isPending) ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                {modal === "create" ? "Create" : "Save Changes"}
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
