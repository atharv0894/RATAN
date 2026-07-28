"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import Link from "next/link";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth-context";
import { Bot, Mail, Lock, ArrowRight, Loader2 } from "lucide-react";

export default function PersonalLogin() {
  const router = useRouter();
  const { loginPersonal } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [unverifiedEmail, setUnverifiedEmail] = useState("");
  const { register, handleSubmit } = useForm();

  const onSubmit = async (data: any) => {
    setIsLoading(true);
    try {
      setUnverifiedEmail("");
      await loginPersonal(data.email, data.password);
      toast.success("Welcome back!");
      router.push("/personal");
    } catch (err: any) {
      const errorMsg = err.response?.data?.error?.message || err.response?.data?.detail || "Login failed";
      if (errorMsg === "Please verify your email before signing in.") {
        setUnverifiedEmail(data.email);
      }
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    setIsResending(true);
    try {
      const { authApi } = await import("@/lib/api");
      await authApi.resend_verification(unverifiedEmail);
      toast.success("If your email is registered, a verification link has been sent.");
    } catch (err: any) {
      toast.error("Failed to resend verification email.");
    } finally {
      setIsResending(false);
    }
  };

  const handleGoogleLogin = async () => {
    setIsGoogleLoading(true);
    try {
      const { authApi } = await import("@/lib/api");
      const res = await authApi.google_oauth_start();
      const url = res.data?.data?.url;
      if (url) window.location.href = url;
    } catch {
      toast.error("Failed to start Google sign-in.");
      setIsGoogleLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans selection:bg-primary/30 relative overflow-hidden">
      {/* Background Decorators */}
      <div className="absolute -top-40 -right-40 w-96 h-96 bg-accent/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <Link href="/" className="flex justify-center mb-6">
          <div className="w-12 h-12 bg-linear-to-br from-primary to-accent rounded-2xl flex items-center justify-center shadow-glow">
            <Bot className="w-6 h-6 text-primary-foreground" />
          </div>
        </Link>
        <h2 className="text-center text-3xl font-extrabold text-text-primary tracking-tight">Welcome back</h2>
        <p className="mt-2 text-center text-sm text-text-secondary font-medium">
          Sign in to your Personal AI Workspace
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="card-premium py-8 px-4 sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
            <div>
              <label className="block text-sm font-semibold text-text-primary mb-1.5">Email address</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-text-secondary" />
                </div>
                <input
                  {...register("email", { required: true })}
                  type="email"
                  className="appearance-none block w-full pl-10 px-3 py-3 border border-border-default rounded-xl bg-surface-2 text-text-primary placeholder-text-secondary focus:outline-none focus:ring-1 focus:ring-border-hover focus:border-border-hover sm:text-sm transition-all shadow-sm"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-sm font-semibold text-text-primary">Password</label>
                <Link href="/personal/forgot-password" className="text-xs font-medium text-text-secondary hover:text-text-primary transition-colors">
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
              className="w-full flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-medium text-primary-foreground bg-primary hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-border-hover disabled:opacity-50 transition-all group"
            >
              {isLoading ? "Signing in..." : "Sign in"} 
              {!isLoading && <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />}
            </button>
          </form>

          {unverifiedEmail && (
            <div className="mt-4">
              <button
                type="button"
                onClick={handleResend}
                disabled={isResending}
                className="w-full flex justify-center py-3 px-4 border border-accent/30 rounded-xl shadow-sm text-sm font-medium text-accent bg-accent/10 hover:bg-accent/20 transition-all"
              >
                {isResending ? "Sending..." : "Resend Verification Email"}
              </button>
            </div>
          )}

          <div className="mt-6">
            <div className="relative mb-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border-default" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-3 bg-surface text-text-secondary text-xs uppercase tracking-widest font-semibold">or</span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleGoogleLogin}
              disabled={isGoogleLoading}
              className="w-full flex items-center justify-center gap-3 py-3 px-4 border border-border-default rounded-xl shadow-sm text-sm font-medium text-text-primary bg-surface-2 hover:bg-surface-3 disabled:opacity-50 transition-all"
            >
              {isGoogleLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
              )}
              Continue with Google
            </button>

            <div className="mt-6 text-center text-sm font-medium text-text-secondary">
              Don't have an account?{" "}
              <Link href="/personal/register" className="text-text-primary hover:underline transition-all">
                Create one
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
