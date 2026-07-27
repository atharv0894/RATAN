"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth-context";
import { Shield, Mail, Lock, ArrowRight } from "lucide-react";

export default function SuperAdminLogin() {
  const router = useRouter();
  const { loginSuperAdmin } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const { register, handleSubmit } = useForm();

  const onSubmit = async (data: any) => {
    setIsLoading(true);
    try {
      await loginSuperAdmin(data.email, data.password);
      toast.success("Welcome, Super Admin");
      router.push("/super-admin");
    } catch (err: any) {
      toast.error(err.response?.data?.error?.message || "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 bg-red-900/30 rounded-2xl flex items-center justify-center border border-red-500/30">
            <Shield className="w-8 h-8 text-red-500" />
          </div>
        </div>
        <h2 className="text-center text-3xl font-bold tracking-tight text-white">RATAN Platform Console</h2>
        <p className="mt-2 text-center text-sm text-red-400 font-medium tracking-widest uppercase">
          Super Admin Access Only
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-gray-950 py-8 px-4 shadow-2xl sm:rounded-2xl sm:px-10 border border-gray-900">
          <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
            <div>
              <label className="block text-sm font-medium text-gray-400">Admin Email</label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-600" />
                </div>
                <input
                  {...register("email", { required: true })}
                  type="email"
                  className="appearance-none block w-full pl-10 px-3 py-3 border border-gray-800 rounded-xl bg-gray-900 text-white placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-red-500 focus:border-red-500 sm:text-sm transition-all"
                  placeholder="superadmin@ratan.io"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400">Master Password</label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-600" />
                </div>
                <input
                  {...register("password", { required: true })}
                  type="password"
                  className="appearance-none block w-full pl-10 px-3 py-3 border border-gray-800 rounded-xl bg-gray-900 text-white placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-red-500 focus:border-red-500 sm:text-sm transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-xl shadow-lg text-sm font-bold text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 focus:ring-offset-black disabled:opacity-50 transition-all uppercase tracking-wider"
            >
              {isLoading ? "Authenticating..." : "Authorize"} <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="mt-8 text-center text-xs text-gray-700 font-mono">
            Unauthorized access is strictly prohibited and logged.
          </div>
        </div>
      </div>
    </div>
  );
}
