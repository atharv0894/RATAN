"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import Link from "next/link";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth-context";
import { Building2, Mail, Lock, ArrowRight } from "lucide-react";

import { ThemeToggle } from "@/components/ThemeToggle";

export default function EnterpriseLogin() {
  const router = useRouter();
  const { loginEnterprise } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const { register, handleSubmit } = useForm();

  const onSubmit = async (data: any) => {
    setIsLoading(true);
    try {
      await loginEnterprise(data.email, data.password);
      toast.success("Welcome back to RATAN Enterprise");
      router.push("/dashboard");
    } catch (err: any) {
      toast.error(err.response?.data?.error?.message || "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans selection:bg-primary/30 relative overflow-hidden">
      
      {/* Theme Toggle */}
      <div className="absolute top-4 right-4 z-50">
        <ThemeToggle />
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <Link href="/" className="flex justify-center mb-6">
          <div className="w-12 h-12 bg-surface-2 border border-border-default rounded-2xl flex items-center justify-center shadow-glow">
            <Building2 className="w-6 h-6 text-foreground" />
          </div>
        </Link>
        <h2 className="text-center text-3xl font-extrabold text-text-primary tracking-tight">Sign in to your Organization</h2>
        <p className="mt-2 text-center text-sm text-text-secondary font-medium">
          Access the Enterprise Knowledge Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="card-premium py-8 px-4 sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
            <div>
              <label className="block text-sm font-semibold text-text-primary mb-1.5">Work Email</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-text-secondary" />
                </div>
                <input
                  {...register("email", { required: true })}
                  type="email"
                  className="appearance-none block w-full pl-10 px-3 py-3 border border-border-default rounded-xl bg-surface-2 text-text-primary placeholder-text-secondary focus:outline-none focus:ring-1 focus:ring-border-hover focus:border-border-hover sm:text-sm transition-all shadow-sm"
                  placeholder="admin@company.com"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-sm font-semibold text-text-primary">Password</label>
                <Link href="/enterprise/forgot-password" className="text-xs font-medium text-text-secondary hover:text-text-primary transition-colors">
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-text-secondary" />
                </div>
                <input
                  {...register("password", { required: true })}
                  type="password"
                  className="appearance-none block w-full pl-10 px-3 py-3 border border-border-default rounded-xl bg-surface-2 text-text-primary placeholder-text-secondary focus:outline-none focus:ring-1 focus:ring-border-hover focus:border-border-hover sm:text-sm transition-all shadow-sm"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-medium text-background bg-primary hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-border-hover disabled:opacity-50 transition-all group"
            >
              {isLoading ? "Signing in..." : "Sign in to Organization"} 
              {!isLoading && <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />}
            </button>
          </form>

          <div className="mt-6">
            <div className="relative mb-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border-default" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-3 bg-surface text-text-secondary text-xs uppercase tracking-widest font-semibold">New to RATAN Enterprise?</span>
              </div>
            </div>

            <Link
              href="/enterprise/register"
              className="w-full flex items-center justify-center gap-3 py-3 px-4 border border-border-default rounded-xl shadow-sm text-sm font-medium text-text-primary bg-surface-2 hover:bg-surface-3 transition-all"
            >
              Register an Organization
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
