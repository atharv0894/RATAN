import { ShieldCheck, Construction } from "lucide-react";

export default function RolesPage() {
  return (
    <div className="h-[80vh] flex flex-col items-center justify-center p-8 text-center space-y-6">
      <div className="w-20 h-20 rounded-3xl bg-surface border border-border-default flex items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 bg-primary/10 animate-pulse"></div>
        <ShieldCheck className="w-10 h-10 text-danger relative z-10" />
      </div>
      
      <div className="space-y-2 max-w-md">
        <h1 className="text-2xl font-bold text-white flex items-center justify-center gap-2">
          Roles & RBAC <Construction className="w-5 h-5 text-warning" />
        </h1>
        <p className="text-muted-foreground text-sm">
          Granular role-based access control and permissions administration is rolling out in the next update.
        </p>
      </div>
    </div>
  );
}
