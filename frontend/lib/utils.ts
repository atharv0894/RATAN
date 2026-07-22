import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatBytes(bytes: number, decimals = 2): string {
  if (!bytes) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`;
}

export function formatDate(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleDateString("en-US", {
    year: "numeric", month: "short", day: "numeric",
  });
}

export function formatDateTime(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleString("en-US", {
    year: "numeric", month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export function formatRelativeTime(timestamp: number): string {
  const diff = Date.now() / 1000 - timestamp;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export function truncate(str: string, length: number): string {
  if (!str) return "";
  return str.length > length ? str.slice(0, length) + "..." : str;
}

export function getStatusColor(status: string): string {
  const map: Record<string, string> = {
    READY: "text-success bg-success/10",
    COMPLETED: "text-success bg-success/10",
    Active: "text-success bg-success/10",
    PROCESSING: "text-warning bg-warning/10",
    EMBEDDING: "text-warning bg-warning/10",
    INDEXING: "text-warning bg-warning/10",
    QUEUED: "text-accent bg-accent/10",
    FAILED: "text-danger bg-danger/10",
    DELETED: "text-muted-foreground bg-muted/10",
    CANCELLED: "text-muted-foreground bg-muted/10",
  };
  return map[status] || "text-muted-foreground bg-muted/10";
}

export function getRoleColor(role: string): string {
  const map: Record<string, string> = {
    SuperAdmin: "text-danger bg-danger/10",
    Admin: "text-primary bg-primary/10",
    "Plant Manager": "text-accent bg-accent/10",
    User: "text-muted-foreground bg-muted/10",
  };
  return map[role] || "text-muted-foreground bg-muted/10";
}
