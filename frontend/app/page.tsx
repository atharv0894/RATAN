"use client";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import {
  Cpu, Brain, FileText, Shield, Activity, ArrowRight,
  ChevronRight, Users, Building2, Database, Zap, Factory,
} from "lucide-react";

const FEATURES = [
  { icon: Brain, title: "AI Knowledge Assistant", desc: "Ask questions in plain language. Get cited, accurate answers from your indexed industrial documentation.", color: "text-primary" },
  { icon: Shield, title: "Enterprise Security & RBAC", desc: "Role-based access control at Organization, Plant, and Department level with a full immutable audit trail.", color: "text-accent" },
  { icon: FileText, title: "Document Lifecycle Management", desc: "Version-controlled documents with deduplication, soft-delete, restore, and full processing history.", color: "text-success" },
  { icon: Database, title: "Industrial RAG Pipeline", desc: "MMR semantic search with metadata filtering and server-side confidence scoring. Zero hallucinations.", color: "text-warning" },
  { icon: Activity, title: "Operations Dashboard", desc: "Real-time analytics on token usage, storage, processing queue, and system health.", color: "text-primary" },
  { icon: Zap, title: "Multi-LLM Orchestration", desc: "Primary Groq inference with automatic Gemini fallback via compensating transaction pattern.", color: "text-accent" },
];

const STATS = [
  { value: "99.9%", label: "Uptime SLA" },
  { value: "<800ms", label: "Avg. Response Time" },
  { value: "SOC 2", label: "Compliance Ready" },
  { value: "50MB", label: "Max Document Size" },
];

export default function LandingPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated) router.push("/dashboard");
  }, [isAuthenticated, isLoading, router]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Nav */}
      <nav className="border-b border-border-default px-6 py-4 flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-linear-to-br from-primary to-accent flex items-center justify-center">
            <Cpu className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-white text-sm tracking-wide">RATAN</span>
          <span className="text-muted-foreground/40 text-xs ml-2 hidden sm:block">Enterprise Knowledge Platform</span>
        </div>
        <div className="flex items-center gap-2 md:gap-3">
          <Link href="/auth/login" className="btn-secondary text-xs md:text-sm px-3 md:px-4 py-1.5 md:py-2">Sign In</Link>
          <Link href="/auth/register" className="btn-primary text-xs md:text-sm px-3 md:px-4 py-1.5 md:py-2">Get Started</Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-24 pb-20 px-6 text-center max-w-5xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-[10px] md:text-xs font-medium mb-6">
          <Cpu className="w-3 h-3" />
          Enterprise AI Platform for Industrial Organizations
        </div>
        <h1 className="text-4xl md:text-5xl lg:text-7xl font-bold text-white leading-tight mb-6">
          Your Industrial Knowledge,<br />
          <span className="gradient-text">Intelligently Unlocked</span>
        </h1>
        <p className="text-base md:text-xl text-muted-foreground max-w-3xl mx-auto mb-10 leading-relaxed px-2 md:px-0">
          RATAN transforms terabytes of disconnected PDFs, manuals, and SOPs into an
          AI-powered knowledge base. Ask questions in plain language and receive
          cited, accurate answers grounded in your own documentation.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 md:gap-4 justify-center px-4 md:px-0">
          <Link href="/auth/register" className="btn-primary text-sm md:text-base px-6 md:px-8 py-3 md:py-3.5 flex items-center justify-center gap-2 w-full sm:w-auto">
            Start Free Trial <ArrowRight className="w-4 h-4" />
          </Link>
          <Link href="/auth/login" className="btn-secondary text-sm md:text-base px-6 md:px-8 py-3 md:py-3.5 flex items-center justify-center w-full sm:w-auto">
            View Demo
          </Link>
        </div>
      </section>

      {/* Stats */}
      <section className="py-12 border-y border-border-default bg-surface/50">
        <div className="max-w-5xl mx-auto px-6 grid grid-cols-2 lg:grid-cols-4 gap-8 text-center">
          {STATS.map(({ value, label }) => (
            <div key={label}>
              <p className="text-3xl font-bold gradient-text">{value}</p>
              <p className="text-sm text-muted-foreground mt-1">{label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Problem Statement */}
      <section className="py-20 px-6 max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white">The Problem We Solve</h2>
          <p className="text-muted-foreground mt-3 text-lg">Manufacturing plants generate thousands of documents. Finding information takes hours.</p>
        </div>
        <div className="grid lg:grid-cols-3 gap-6">
          {[
            { stat: "73%", label: "of engineers waste time searching for information", color: "text-danger" },
            { stat: "4.5hrs", label: "average time to find critical technical specs", color: "text-warning" },
            { stat: "$2.5M", label: "annual productivity loss per mid-size plant", color: "text-accent" },
          ].map(({ stat, label, color }) => (
            <div key={label} className="card-premium p-6 text-center space-y-2">
              <p className={`text-4xl font-bold ${color}`}>{stat}</p>
              <p className="text-muted-foreground text-sm leading-relaxed">{label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6 max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white">Enterprise-Grade Capabilities</h2>
          <p className="text-muted-foreground mt-3">Built for Fortune 500 manufacturing organizations</p>
        </div>
        <div className="grid lg:grid-cols-3 gap-5">
          {FEATURES.map(({ icon: Icon, title, desc, color }) => (
            <div key={title} className="card-premium p-5 space-y-3">
              <div className="w-10 h-10 rounded-xl bg-surface-2 border border-border-default flex items-center justify-center">
                <Icon className={`w-5 h-5 ${color}`} />
              </div>
              <h3 className="font-semibold text-white">{title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture */}
      <section className="py-20 px-6 max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white">Multi-Tenant Architecture</h2>
          <p className="text-muted-foreground mt-3">Strict data isolation across your entire enterprise hierarchy</p>
        </div>
        <div className="card-premium p-8">
          <div className="flex flex-col lg:flex-row items-center justify-center gap-3 text-sm flex-wrap">
            {[
              { icon: Building2, label: "Organization", sub: "Top-level tenant" },
              { icon: ChevronRight, label: "" },
              { icon: Factory, label: "Plants", sub: "Facilities" },
              { icon: ChevronRight, label: "" },
              { icon: Users, label: "Departments", sub: "Teams" },
              { icon: ChevronRight, label: "" },
              { icon: FileText, label: "Documents", sub: "Knowledge assets" },
            ].map(({ icon: Icon, label, sub }, i) =>
              label === "" ? (
                <ChevronRight key={i} className="w-5 h-5 text-muted-foreground/40" />
              ) : (
                <div key={label} className="bg-surface-2 border border-border-default rounded-xl p-4 text-center min-w-27.5">
                  <Icon className="w-5 h-5 text-primary mx-auto mb-1" />
                  <p className="font-medium text-foreground text-xs">{label}</p>
                  <p className="text-[10px] text-muted-foreground">{sub}</p>
                </div>
              )
            )}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6 text-center">
        <div className="max-w-2xl mx-auto card-premium p-10 space-y-6 bg-linear-to-br from-primary/10 to-accent/10 border-primary/20">
          <h2 className="text-3xl font-bold text-white">Ready to Transform Your Operations?</h2>
          <p className="text-muted-foreground">Join manufacturing organizations worldwide using RATAN to unlock the knowledge hidden in their documentation.</p>
          <Link href="/auth/register" className="btn-primary text-base px-8 py-3.5 inline-flex items-center gap-2">
            Register Your Organization <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border-default py-8 px-6 text-center">
        <div className="flex items-center justify-center gap-3 mb-3">
          <div className="w-6 h-6 rounded-lg bg-linear-to-br from-primary to-accent flex items-center justify-center">
            <Cpu className="w-3 h-3 text-white" />
          </div>
          <span className="font-bold text-white text-sm">RATAN</span>
        </div>
        <p className="text-xs text-muted-foreground">Retrieval-Augmented Technology for Asset Networks · Enterprise Industrial Knowledge Platform</p>
        <p className="text-xs text-muted-foreground/50 mt-1">© 2026 RATAN. Built for the industrial future.</p>
      </footer>
    </div>
  );
}
