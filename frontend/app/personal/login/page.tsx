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
    <div className="min-h-screen bg-gray-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Link href="/" className="flex justify-center mb-6">
          <div className="w-12 h-12 bg-blue-600/20 rounded-xl flex items-center justify-center">
            <Bot className="w-6 h-6 text-blue-500" />
          </div>
        </Link>
        <h2 className="text-center text-3xl font-extrabold text-white">Welcome back</h2>
        <p className="mt-2 text-center text-sm text-gray-400">
          Sign in to your Personal AI Workspace
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-gray-900 py-8 px-4 shadow-2xl sm:rounded-2xl sm:px-10 border border-gray-800">
          <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
            <div>
              <label className="block text-sm font-medium text-gray-300">Email address</label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  {...register("email", { required: true })}
                  type="email"
                  className="appearance-none block w-full pl-10 px-3 py-3 border border-gray-700 rounded-xl bg-gray-800 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent sm:text-sm transition-all"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300">Password</label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  {...register("password", { required: true })}
                  type="password"
                  className="appearance-none block w-full pl-10 px-3 py-3 border border-gray-700 rounded-xl bg-gray-800 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent sm:text-sm transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="text-sm">
                <Link href="/personal/forgot-password" className="font-medium text-blue-400 hover:text-blue-300">
                  Forgot your password?
                </Link>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-all"
            >
              {isLoading ? "Signing in..." : "Sign in"} <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {unverifiedEmail && (
            <div className="mt-4">
              <button
                type="button"
                onClick={handleResend}
                disabled={isResending}
                className="w-full flex justify-center py-3 px-4 border border-blue-500/30 rounded-xl shadow-sm text-sm font-medium text-blue-400 bg-blue-500/10 hover:bg-blue-500/20 transition-all"
              >
                {isResending ? "Sending..." : "Resend Verification Email"}
              </button>
            </div>
          )}

          <div className="mt-6">
            {/* OR divider */}
            <div className="relative mb-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-700" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-3 bg-gray-900 text-gray-500 text-xs uppercase tracking-widest">or</span>
              </div>
            </div>

            {/* Google Sign-In button */}
            <button
              type="button"
              onClick={handleGoogleLogin}
              disabled={isGoogleLoading}
              className="w-full flex items-center justify-center gap-3 py-3 px-4 border border-gray-600 rounded-xl shadow-sm text-sm font-medium text-white bg-gray-800 hover:bg-gray-700 disabled:opacity-50 transition-all"
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

            {/* Don't have an account */}
            <div className="relative mt-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-700" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-gray-900 text-gray-400">Don't have an account?</span>
              </div>
            </div>

            <div className="mt-6">
              <Link
                href="/personal/register"
                className="w-full flex justify-center py-3 px-4 border border-gray-700 rounded-xl shadow-sm text-sm font-medium text-gray-300 bg-gray-800 hover:bg-gray-700 transition-all"
              >
                Create personal account
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
