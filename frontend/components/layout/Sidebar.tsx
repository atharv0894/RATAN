"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { cn, getRoleColor } from "@/lib/utils";
import {
  LayoutDashboard, FileText, UploadCloud, Building2,
  Factory, Users, ShieldCheck, ClipboardCheck, Settings, LogOut,
  Cpu, MessageSquare, ChevronRight, Search, Network, BrainCircuit,
  LoaderCircle, BarChart3, Wrench, Building, Sun, Moon, X, Menu
} from "lucide-react";
import { useTheme } from "next-themes";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
  adminOnly?: boolean;
}

const NAV_SECTIONS: { title: string; items: NavItem[] }[] = [
  {
    title: "Core",
    items: [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
      { label: "AI Assistant", href: "/dashboard/chat", icon: MessageSquare },
      { label: "Search", href: "/dashboard/search", icon: Search },
    ],
  },
  {
    title: "Knowledge",
    items: [
      { label: "Documents", href: "/dashboard/documents", icon: FileText },
      { label: "Upload Center", href: "/dashboard/upload", icon: UploadCloud },
      { label: "Knowledge Graph", href: "/dashboard/graph", icon: Network },
      { label: "Entities", href: "/dashboard/entities", icon: BrainCircuit },
    ],
  },
  {
    title: "Operations",
    items: [
      { label: "Processing Queue", href: "/dashboard/jobs", icon: LoaderCircle },
      { label: "Analytics", href: "/dashboard/analytics", icon: BarChart3 },
    ],
  },
  {
    title: "Organization",
    items: [
      { label: "Users", href: "/dashboard/users", icon: Users },
      { label: "Plants", href: "/dashboard/plants", icon: Factory },
      { label: "Departments", href: "/dashboard/departments", icon: Building },
    ],
  },
  {
    title: "Administration",
    items: [
      { label: "Organizations", href: "/dashboard/admin/organizations", icon: Building2, adminOnly: true },
      { label: "Roles & RBAC", href: "/dashboard/admin/roles", icon: ShieldCheck, adminOnly: true },
      { label: "Audit Logs", href: "/dashboard/admin/audit", icon: ClipboardCheck, adminOnly: true },
      { label: "Maintenance", href: "/dashboard/admin/maintenance", icon: Wrench, adminOnly: true },
      { label: "System Settings", href: "/dashboard/admin/settings", icon: Settings, adminOnly: true },
    ],
  },
];

export function Sidebar({ isOpen, setIsOpen }: { isOpen?: boolean; setIsOpen?: (v: boolean) => void }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const isAdmin = user?.role === "Admin" || user?.role === "SuperAdmin";

  return (
    <>
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-20 md:hidden backdrop-blur-sm" 
          onClick={() => setIsOpen?.(false)}
        />
      )}
      <aside className={cn(
        "w-64 h-screen flex flex-col bg-surface border-r border-border-default fixed left-0 top-0 z-30 transition-transform duration-300 md:translate-x-0",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        {/* Workspace Switcher */}
        <div className="px-3 py-3 border-b border-border-default flex items-center justify-between">
          <button className="flex-1 flex items-center gap-2 px-2 py-1.5 hover:bg-surface-2 rounded-lg transition-colors group text-left">
            <div className="w-6 h-6 rounded-md bg-linear-to-br from-primary to-accent flex items-center justify-center shadow-lg shadow-primary/20 shrink-0">
              <Cpu className="w-3.5 h-3.5 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-foreground truncate">RATAN Enterprise</p>
            </div>
            <div className="opacity-0 group-hover:opacity-100 transition-opacity p-1">
              <span className="text-[10px] font-mono text-muted-foreground bg-surface border border-border-default px-1.5 py-0.5 rounded">⌘K</span>
            </div>
          </button>
          <button 
            className="md:hidden p-1.5 ml-1 rounded-lg text-muted-foreground hover:bg-surface-2 transition-colors shrink-0"
            onClick={() => setIsOpen?.(false)}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto space-y-5">
        {NAV_SECTIONS.map((section) => {
          const visible = section.items.filter((i) => !i.adminOnly || isAdmin);
          if (!visible.length) return null;
          return (
            <div key={section.title}>
              <p className="text-[10px] uppercase tracking-widest text-muted-foreground/60 px-3 mb-1.5 font-semibold">
                {section.title}
              </p>
              <ul className="space-y-0.5">
                {visible.map((item) => {
                  const active = pathname === item.href || pathname.startsWith(item.href + "/");
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        className={cn("sidebar-link group", active && "active")}
                      >
                        <item.icon className={cn("w-4 h-4 shrink-0", active ? "text-primary" : "text-muted-foreground group-hover:text-foreground")} />
                        <span className="flex-1">{item.label}</span>
                        {item.badge && (
                          <span className="text-[10px] bg-primary/20 text-primary px-1.5 py-0.5 rounded-full font-medium">
                            {item.badge}
                          </span>
                        )}
                        {active && <ChevronRight className="w-3 h-3 text-primary ml-auto" />}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </nav>

      {/* User Profile */}
      <div className="border-t border-border-default p-3 space-y-1">
        <Link href="/dashboard/profile" className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-surface-2 transition-all group">
          <div className="w-8 h-8 rounded-full bg-linear-to-br from-primary to-accent flex items-center justify-center text-white text-xs font-bold shrink-0">
            {user?.full_name?.charAt(0) ?? "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">{user?.full_name}</p>
            <p className={cn("text-[10px] px-1.5 py-0.5 rounded-full inline-block font-medium mt-0.5", getRoleColor(user?.role ?? ""))}>
              {user?.role}
            </p>
          </div>
        </Link>
        <button
          onClick={logout}
          className="sidebar-link w-full text-danger/70 hover:text-danger hover:bg-danger/5"
        >
          <LogOut className="w-4 h-4 shrink-0" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
    </>
  );
}

export function TopBar({ title, subtitle, onMenuClick }: { title?: string; subtitle?: string; onMenuClick?: () => void }) {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();

  return (
    <header className="h-14 border-b border-border-default px-4 md:px-6 flex items-center justify-between bg-background/80 backdrop-blur-xl sticky top-0 z-20">
      <div className="flex items-center gap-3">
        <button 
          className="md:hidden p-1.5 -ml-1 rounded-lg text-muted-foreground hover:bg-surface-2 transition-colors"
          onClick={onMenuClick}
        >
          <Menu className="w-5 h-5" />
        </button>
        <div>
          {title && <h1 className="text-sm font-semibold text-foreground">{title}</h1>}
          {subtitle && <p className="text-[10px] md:text-xs text-muted-foreground hidden sm:block">{subtitle}</p>}
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          className="p-1.5 rounded-lg text-muted-foreground hover:bg-surface-2 transition-colors"
          title="Toggle theme"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
        <div className="w-7 h-7 rounded-full bg-linear-to-br from-primary to-accent flex items-center justify-center text-white text-xs font-bold shadow-md">
          {user?.full_name?.charAt(0) ?? "U"}
        </div>
      </div>
    </header>
  );
}
