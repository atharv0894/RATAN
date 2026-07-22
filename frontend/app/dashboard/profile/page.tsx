"use client";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { useAuth } from "@/lib/auth-context";
import { authApi } from "@/lib/api";
import { useState } from "react";
import { toast } from "sonner";
import { cn, getRoleColor } from "@/lib/utils";
import { User, Lock, Mail, Shield, Building2, Loader2, Check } from "lucide-react";

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [isChangingPw, setIsChangingPw] = useState(false);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPw !== confirmPw) { toast.error("Passwords don't match"); return; }
    if (newPw.length < 8) { toast.error("New password must be at least 8 characters"); return; }
    setIsChangingPw(true);
    try {
      await authApi.changePassword(oldPw, newPw);
      toast.success("Password changed. Please log in again.");
      setTimeout(logout, 1500);
    } catch {
      toast.error("Incorrect old password");
    } finally {
      setIsChangingPw(false);
    }
  };

  return (
    <DashboardLayout title="My Profile" subtitle="Manage your account settings">
      <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">

        {/* Profile card */}
        <div className="card-premium p-6 flex items-center gap-6">
          <div className="w-20 h-20 rounded-2xl bg-linear-to-br from-primary to-accent flex items-center justify-center text-white text-3xl font-bold shrink-0">
            {user?.full_name?.charAt(0) ?? "U"}
          </div>
          <div className="flex-1 space-y-1">
            <h2 className="text-xl font-bold text-white">{user?.full_name}</h2>
            <p className="text-muted-foreground text-sm">{user?.email}</p>
            <div className="flex items-center gap-2 mt-2">
              <span className={cn("status-badge text-xs", getRoleColor(user?.role ?? ""))}>{user?.role}</span>
            </div>
          </div>
        </div>

        {/* Account Details */}
        <div className="card-premium p-5 space-y-4">
          <h3 className="text-sm font-semibold text-foreground">Account Information</h3>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Full Name", value: user?.full_name, icon: User },
              { label: "Email", value: user?.email, icon: Mail },
              { label: "Role", value: user?.role, icon: Shield },
              { label: "Organization ID", value: user?.org_id ? user.org_id.slice(0, 8) + "..." : "—", icon: Building2 },
              { label: "User ID", value: user?.id ? user.id.slice(0, 8) + "..." : "—", icon: User },
              { label: "Status", value: "Active", icon: Check },
            ].map(({ label, value, icon: Icon }) => (
              <div key={label} className="bg-surface-2 rounded-xl p-3 flex items-center gap-3">
                <Icon className="w-4 h-4 text-muted-foreground shrink-0" />
                <div>
                  <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</p>
                  <p className="text-sm font-medium text-foreground mt-0.5">{value ?? "—"}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Change Password */}
        <div className="card-premium p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold text-foreground">Change Password</h3>
          </div>
          <form onSubmit={handleChangePassword} className="space-y-3">
            {[
              { label: "Current Password", value: oldPw, onChange: setOldPw, placeholder: "Enter current password" },
              { label: "New Password", value: newPw, onChange: setNewPw, placeholder: "Min. 8 characters" },
              { label: "Confirm New Password", value: confirmPw, onChange: setConfirmPw, placeholder: "Re-enter new password" },
            ].map(({ label, value, onChange, placeholder }) => (
              <div key={label}>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">{label}</label>
                <input type="password" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} className="input-field text-sm h-9" />
              </div>
            ))}
            <button type="submit" disabled={isChangingPw || !oldPw || !newPw || !confirmPw} className="btn-primary w-full py-2.5 text-sm flex items-center justify-center gap-2">
              {isChangingPw ? <><Loader2 className="w-4 h-4 animate-spin" /> Changing...</> : <><Check className="w-4 h-4" /> Change Password</>}
            </button>
          </form>
        </div>

        {/* Danger Zone */}
        <div className="card-premium p-5 border-danger/10">
          <h3 className="text-sm font-semibold text-danger mb-3">Danger Zone</h3>
          <button onClick={logout} className="btn-secondary text-sm py-2 px-4 text-danger hover:bg-danger/5 hover:text-danger border-danger/20">
            Sign Out of All Sessions
          </button>
        </div>
      </div>
    </DashboardLayout>
  );
}
