"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminApi } from "@/lib/api";
import { AlertTriangle, Loader2 } from "lucide-react";

export default function TenantResourceTable() {
  const queryClient = useQueryClient();
  const [confirmModal, setConfirmModal] = useState<{ isOpen: boolean; tenant: any | null }>({
    isOpen: false,
    tenant: null,
  });

  const { data, isLoading, isError } = useQuery({
    queryKey: ["admin", "telemetry", "tenants"],
    queryFn: async () => {
      const res = await adminApi.telemetryTenants();
      return res.data.data.tenants;
    },
    // Longer polling interval for heavy aggregation query
    refetchInterval: 30000, 
  });

  const toggleMutation = useMutation({
    mutationFn: async (org_id: string) => {
      const res = await adminApi.toggleTenantStatus(org_id);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "telemetry", "tenants"] });
      setConfirmModal({ isOpen: false, tenant: null });
    },
  });

  if (isLoading) {
    return (
      <div className="w-full bg-gray-900 rounded-xl border border-gray-800 p-8 flex justify-center items-center">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="p-4 bg-red-900/20 border border-red-800 rounded-xl text-red-400">
        Failed to load tenant telemetry.
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden relative">
      <div className="p-5 border-b border-gray-800 flex justify-between items-center bg-gray-900/50">
        <h2 className="text-lg font-semibold text-white">Tenant Resource Footprint</h2>
        <span className="text-xs text-gray-500 bg-gray-800 px-3 py-1 rounded-full">Refreshes every 30s</span>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left whitespace-nowrap">
          <thead className="text-xs text-gray-400 uppercase bg-gray-800/50 border-b border-gray-800 sticky top-0">
            <tr>
              <th className="px-6 py-4 font-medium">Organization Name</th>
              <th className="px-6 py-4 font-medium hidden sm:table-cell">Active Users</th>
              <th className="px-6 py-4 font-medium hidden md:table-cell">Total Documents</th>
              <th className="px-6 py-4 font-medium">Status</th>
              <th className="px-6 py-4 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {data.map((tenant: any) => (
              <tr key={tenant.org_id} className="hover:bg-gray-800/30 transition-colors">
                <td className="px-6 py-4 font-medium text-white">{tenant.org_name}</td>
                <td className="px-6 py-4 text-gray-300 hidden sm:table-cell">{tenant.active_users}</td>
                <td className="px-6 py-4 text-gray-300 hidden md:table-cell">{tenant.total_documents}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${
                    tenant.status === "Active" 
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
                      : "bg-red-500/10 text-red-400 border-red-500/20"
                  }`}>
                    {tenant.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  <button 
                    onClick={() => setConfirmModal({ isOpen: true, tenant })}
                    className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                      tenant.status === "Active"
                        ? "bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20"
                        : "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/20"
                    }`}
                  >
                    {tenant.status === "Active" ? "Suspend" : "Reactivate"}
                  </button>
                </td>
              </tr>
            ))}
            {data.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                  No organizations found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Confirmation Modal Safeguard */}
      {confirmModal.isOpen && confirmModal.tenant && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 max-w-md w-full shadow-2xl relative">
            <div className="flex items-center gap-3 mb-4 text-amber-500">
              <AlertTriangle className="w-6 h-6" />
              <h3 className="text-lg font-bold text-white">Confirm Action</h3>
            </div>
            <p className="text-gray-300 text-sm mb-6">
              Are you sure you want to {confirmModal.tenant.status === "Active" ? "suspend" : "reactivate"} 
              <strong className="text-white mx-1">{confirmModal.tenant.org_name}</strong>?
              {confirmModal.tenant.status === "Active" && (
                <span className="block mt-2 text-red-400">
                  This will instantly revoke {confirmModal.tenant.active_users} active user sessions.
                </span>
              )}
            </p>
            <div className="flex justify-end gap-3">
              <button 
                onClick={() => setConfirmModal({ isOpen: false, tenant: null })}
                disabled={toggleMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={() => toggleMutation.mutate(confirmModal.tenant.org_id)}
                disabled={toggleMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors flex items-center gap-2"
              >
                {toggleMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
