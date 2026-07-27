"use client";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Bot, Building2, Cpu, ArrowRight } from "lucide-react";

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
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6 relative overflow-hidden">
      
      {/* Background decoration */}
      <div className="absolute top-1/3 left-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-1/3 right-1/4 w-96 h-96 bg-purple-600/20 rounded-full blur-[100px] pointer-events-none" />

      <div className="z-10 text-center mb-16 space-y-4 max-w-2xl">
        <div className="inline-flex items-center justify-center p-3 bg-white/5 rounded-2xl mb-4 border border-white/10 shadow-xl">
          <Cpu className="w-8 h-8 text-blue-400" />
        </div>
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
          Welcome to RATAN
        </h1>
        <p className="text-lg text-gray-400">
          Choose how you want to experience the platform.
        </p>
      </div>

      <div className="z-10 grid md:grid-cols-2 gap-6 max-w-4xl w-full">
        
        {/* Personal AI Card */}
        <div className="group bg-gray-900/50 backdrop-blur-xl border border-gray-800 hover:border-blue-500/50 rounded-3xl p-8 transition-all hover:shadow-2xl hover:shadow-blue-500/10 flex flex-col items-center text-center">
          <div className="w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
            <Bot className="w-8 h-8 text-blue-400" />
          </div>
          <h2 className="text-2xl font-bold mb-3">RATAN Personal</h2>
          <p className="text-gray-400 mb-8 flex-1">
            Your private AI assistant. Chat, upload documents, and build your personal knowledge base.
          </p>
          <Link href="/personal/login" className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 px-6 rounded-xl transition-colors flex items-center justify-center gap-2">
            Continue as Individual <ArrowRight className="w-4 h-4" />
          </Link>
          <div className="mt-4 text-sm text-gray-500">
            No account? <Link href="/personal/register" className="text-blue-400 hover:underline">Sign up</Link>
          </div>
        </div>

        {/* Enterprise Card */}
        <div className="group bg-gray-900/50 backdrop-blur-xl border border-gray-800 hover:border-purple-500/50 rounded-3xl p-8 transition-all hover:shadow-2xl hover:shadow-purple-500/10 flex flex-col items-center text-center">
          <div className="w-16 h-16 bg-purple-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
            <Building2 className="w-8 h-8 text-purple-400" />
          </div>
          <h2 className="text-2xl font-bold mb-3">RATAN Enterprise</h2>
          <p className="text-gray-400 mb-8 flex-1">
            Industrial knowledge platform. Manage teams, workflows, multi-tenant RAG, and audits.
          </p>
          <Link href="/enterprise/login" className="w-full bg-white text-black hover:bg-gray-200 font-medium py-3 px-6 rounded-xl transition-colors flex items-center justify-center gap-2">
            Continue to Enterprise <ArrowRight className="w-4 h-4" />
          </Link>
          <div className="mt-4 text-sm text-gray-500">
            New Organization? <Link href="/enterprise/register" className="text-purple-400 hover:underline">Register</Link>
          </div>
        </div>

      </div>

      <div className="mt-20 text-center z-10 text-xs text-gray-600 font-medium tracking-wide">
        © 2026 RATAN AI. SECURE ENTERPRISE CLOUD.
      </div>
    </div>
  );
}
