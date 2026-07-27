"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import Link from "next/link";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth-context";
import { Bot, Mail, Lock, User as UserIcon, ArrowRight } from "lucide-react";

export default function PersonalRegister() {
  const router = useRouter();
  const { registerPersonal } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const { register, handleSubmit, watch } = useForm();
  
  const password = watch("password", "");

  const onSubmit = async (data: any) => {
    if (data.password !== data.confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }
    
    setIsLoading(true);
    try {
      await registerPersonal({
        full_name: data.full_name,
        email: data.email,
        password: data.password
      });
      toast.success("Account created! Please sign in.");
      router.push("/personal/login");
    } catch (err: any) {
      toast.error(err.response?.data?.error?.message || "Registration failed");
    } finally {
      setIsLoading(false);
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
        <h2 className="text-center text-3xl font-extrabold text-white">Create Account</h2>
        <p className="mt-2 text-center text-sm text-gray-400">
          Get started with your Personal AI
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-gray-900 py-8 px-4 shadow-2xl sm:rounded-2xl sm:px-10 border border-gray-800">
          <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
            <div>
              <label className="block text-sm font-medium text-gray-300">Full Name</label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <UserIcon className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  {...register("full_name", { required: true })}
                  type="text"
                  className="appearance-none block w-full pl-10 px-3 py-3 border border-gray-700 rounded-xl bg-gray-800 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent sm:text-sm transition-all"
                  placeholder="John Doe"
                />
              </div>
            </div>

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

            <div>
              <label className="block text-sm font-medium text-gray-300">Confirm Password</label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  {...register("confirmPassword", { required: true })}
                  type="password"
                  className="appearance-none block w-full pl-10 px-3 py-3 border border-gray-700 rounded-xl bg-gray-800 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent sm:text-sm transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-all"
            >
              {isLoading ? "Creating account..." : "Sign up"} <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="mt-6">
            <div className="relative flex justify-center text-sm">
              <span className="text-gray-400">
                Already have an account?{' '}
                <Link href="/personal/login" className="text-blue-400 hover:text-blue-300 font-medium">
                  Log in
                </Link>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
