"use client";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminApi, usersApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { formatRelativeTime, cn, getRoleColor } from "@/lib/utils";
import { toast } from "sonner";
import { useState } from "react";
import { Search, Pencil, Trash2, X, Check, Loader2 } from "lucide-react";

export default function UsersPage() {
  const { user: me } = useAuth();
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [editUser, setEditUser] = useState<{ id: string; full_name: string; status: string } | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["users-list", me?.role],
    queryFn: () => {
      if (me?.role === "SuperAdmin" || me?.role === "SYSTEM_ADMIN") {
        return adminApi.listUsers(0, 100).then((r) => r.data.data);
      }
      return usersApi.list(0, 100).then((r) => r.data.data);
    },
    enabled: !!me
  });

  const updateMut = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Record<string, string> }) => {
      if (me?.role === "SuperAdmin" || me?.role === "SYSTEM_ADMIN") {
        return adminApi.updateUser(id, payload);
      }
      return usersApi.update(id, payload);
    },
    onSuccess: () => { toast.success("User updated"); qc.invalidateQueries({ queryKey: ["users-list", me?.role] }); setEditUser(null); },
    onError: () => toast.error("Failed to update user"),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => {
      if (me?.role === "SuperAdmin" || me?.role === "SYSTEM_ADMIN") {
        return adminApi.deleteUser(id);
      }
      return usersApi.delete(id);
    },
    onSuccess: () => { toast.success("User deleted"); qc.invalidateQueries({ queryKey: ["users-list", me?.role] }); },
    onError: () => toast.error("Failed to delete user"),
  });

  const users: { id: string; email: string; full_name: string; role: string; status: string; created_at: number }[] = data ?? [];
  const filtered = search ? users.filter((u) => u.full_name.toLowerCase().includes(search.toLowerCase()) || u.email.toLowerCase().includes(search.toLowerCase())) : users;

  return (
    <DashboardLayout title="Users" subtitle="Manage platform users">
      <div className="space-y-4 animate-fade-in">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by name or email..." className="input-field pl-10 h-9 text-sm" />
          </div>
          <p className="text-xs text-muted-foreground">{filtered.length} users</p>
        </div>

        <div className="card-premium overflow-x-auto hide-scrollbar">
          <table className="w-full text-sm min-w-[700px]">
            <thead>
              <tr className="border-b border-border-default bg-surface-2/50">
                {["User", "Email", "Role", "Status", "Joined", "Actions"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="border-b border-border-default">
                    {Array.from({ length: 6 }).map((_, j) => <td key={j} className="px-4 py-3"><div className="skeleton h-4 rounded w-24" /></td>)}
                  </tr>
                ))
              ) : filtered.map((user) => (
                <tr key={user.id} className="border-b border-border-default/60 hover:bg-surface-2/30 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-linear-to-br from-primary/30 to-accent/30 flex items-center justify-center text-xs font-bold text-white">
                        {user.full_name?.charAt(0) ?? "U"}
                      </div>
                      <span className="font-medium text-foreground">{user.full_name}</span>
                      {user.id === me?.id && <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded-full">You</span>}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground text-xs">{user.email}</td>
                  <td className="px-4 py-3">
                    <span className={cn("status-badge text-[11px]", getRoleColor(user.role))}>{user.role}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn("status-badge text-[11px]", user.status === "Active" ? "bg-success/10 text-success" : "bg-danger/10 text-danger")}>{user.status}</span>
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">{user.created_at ? formatRelativeTime(user.created_at) : "—"}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      <button onClick={() => setEditUser({ id: user.id, full_name: user.full_name, status: user.status })} className="p-1.5 rounded-lg hover:bg-surface-2 text-muted-foreground hover:text-foreground">
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      {user.id !== me?.id && (
                        <button onClick={() => { if (confirm("Delete this user?")) deleteMut.mutate(user.id); }} className="p-1.5 rounded-lg hover:bg-danger/10 text-muted-foreground hover:text-danger">
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {editUser && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setEditUser(null)}>
          <div className="card-premium p-6 w-full max-w-sm space-y-4 animate-fade-in" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-white">Edit User</h3>
              <button onClick={() => setEditUser(null)}><X className="w-4 h-4 text-muted-foreground" /></button>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground-2 mb-1.5">Full Name</label>
              <input value={editUser.full_name} onChange={(e) => setEditUser((u) => u && ({ ...u, full_name: e.target.value }))} className="input-field" />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground-2 mb-1.5">Status</label>
              <select value={editUser.status} onChange={(e) => setEditUser((u) => u && ({ ...u, status: e.target.value }))} className="input-field">
                <option value="Active">Active</option>
                <option value="Inactive">Inactive</option>
              </select>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setEditUser(null)} className="btn-secondary flex-1 py-2.5 text-sm">Cancel</button>
              <button
                onClick={() => updateMut.mutate({ id: editUser.id, payload: { full_name: editUser.full_name, status: editUser.status } })}
                disabled={updateMut.isPending}
                className="btn-primary flex-1 py-2.5 text-sm flex items-center justify-center gap-2"
              >
                {updateMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
