"use client";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Bot, Building2, Cpu, ArrowRight, ShieldCheck } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function LandingPage() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      if (user.account_type === "PERSONAL") router.push("/personal");
      else if (user.account_type === "SUPER_ADMIN") router.push("/super-admin");
      else router.push("/dashboard");
    }
  }, [isAuthenticated, isLoading, user, router]);

  return (
    <div className="min-h-screen bg-bg text-text-primary flex flex-col relative overflow-hidden font-sans selection:bg-primary/30">
      
      {/* Premium Background Gradients */}
      <div className="absolute top-0 inset-x-0 h-[500px] bg-gradient-to-b from-primary/10 to-transparent pointer-events-none" />
      <div className="absolute -top-[300px] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] opacity-20 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-accent via-transparent to-transparent pointer-events-none blur-3xl" />
      
      {/* Navbar */}
      <nav className="w-full flex items-center justify-between px-6 py-5 max-w-7xl mx-auto relative z-20">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-linear-to-br from-primary to-accent flex items-center justify-center shadow-glow">
            <Cpu className="w-4 h-4 text-primary-foreground" />
          </div>
          <span className="font-bold tracking-tight text-lg">RATAN</span>
        </div>
        <div className="flex items-center gap-4 text-sm font-medium">
          <ThemeToggle />
          <Link href="/personal/login" className="text-text-secondary hover:text-text-primary transition-colors">
            Personal Login
          </Link>
          <Link href="/enterprise/login" className="text-text-secondary hover:text-text-primary transition-colors">
            Enterprise Login
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 relative z-10 -mt-10">
        <div className="text-center mb-16 space-y-6 max-w-3xl animate-slide-in-down">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-2 border border-border-default shadow-sm text-xs font-semibold tracking-wide text-text-secondary mb-4">
            <ShieldCheck className="w-3.5 h-3.5 text-accent" />
            <span>ENTERPRISE AI PLATFORM</span>
          </div>
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tighter text-text-primary leading-[1.1]">
            Intelligence for <br className="hidden md:block" />
            <span className="bg-gradient-to-r from-text-primary via-text-secondary to-text-primary bg-clip-text text-transparent">Every Scale.</span>
          </h1>
          <p className="text-lg md:text-xl text-text-secondary max-w-2xl mx-auto leading-relaxed font-medium">
            Deploy industrial-grade knowledge intelligence. Choose your workspace and experience the future of secure AI.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 max-w-5xl w-full animate-fade-in" style={{ animationDelay: '100ms' }}>
          
          {/* Personal AI Card */}
          <div className="card-premium p-8 group hover:border-accent/50 transition-all duration-500 hover:shadow-card-hover relative overflow-hidden flex flex-col h-full bg-surface/50 backdrop-blur-xl">
            <div className="absolute inset-0 bg-gradient-to-br from-accent/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="relative z-10 flex flex-col h-full items-start text-left">
              <div className="w-12 h-12 rounded-2xl bg-surface-2 border border-border-default flex items-center justify-center mb-6 shadow-sm group-hover:scale-110 transition-transform duration-500 group-hover:border-accent/30 group-hover:shadow-glow">
                <Bot className="w-6 h-6 text-foreground" />
              </div>
              <h2 className="text-2xl font-bold mb-3 tracking-tight text-text-primary">RATAN Personal</h2>
              <p className="text-text-secondary mb-8 leading-relaxed font-medium flex-1">
                Your private AI assistant. Ask questions, analyze documents, and build a localized knowledge base effortlessly.
              </p>
              <Link href="/personal/login" className="w-full bg-primary hover:bg-primary-hover text-primary-foreground font-medium py-3.5 px-6 rounded-xl transition-all duration-300 flex items-center justify-center gap-2 group/btn shadow-sm">
                Get Started <ArrowRight className="w-4 h-4 group-hover/btn:translate-x-1 transition-transform" />
              </Link>
            </div>
          </div>

          {/* Enterprise Card */}
          <div className="card-premium p-8 group hover:border-primary/50 transition-all duration-500 hover:shadow-card-hover relative overflow-hidden flex flex-col h-full bg-surface/50 backdrop-blur-xl">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="relative z-10 flex flex-col h-full items-start text-left">
              <div className="w-12 h-12 rounded-2xl bg-surface-2 border border-border-default flex items-center justify-center mb-6 shadow-sm group-hover:scale-110 transition-transform duration-500 group-hover:border-primary/30 group-hover:shadow-glow">
                <Building2 className="w-6 h-6 text-foreground" />
              </div>
              <h2 className="text-2xl font-bold mb-3 tracking-tight text-text-primary">RATAN Enterprise</h2>
              <p className="text-text-secondary mb-8 leading-relaxed font-medium flex-1">
                Industrial knowledge platform. Manage teams, complex workflows, multi-tenant architectures, and stringent access controls.
              </p>
              <Link href="/enterprise/login" className="w-full bg-surface-2 hover:bg-surface-3 border border-border-default text-text-primary font-medium py-3.5 px-6 rounded-xl transition-all duration-300 flex items-center justify-center gap-2 group/btn shadow-sm">
                Access Enterprise <ArrowRight className="w-4 h-4 group-hover/btn:translate-x-1 transition-transform" />
              </Link>
            </div>
          </div>

        </div>
      </main>

      <footer className="w-full text-center py-8 z-10 text-xs text-text-secondary/60 font-medium tracking-widest uppercase">
        © {new Date().getFullYear()} RATAN PLATFORM. ALL RIGHTS RESERVED.
      </footer>
    </div>
  );
}
