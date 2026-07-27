"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import Link from "next/link";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth-context";
import { Building2, Mail, Lock, User as UserIcon, ArrowRight } from "lucide-react";

export default function EnterpriseRegister() {
  const router = useRouter();
  const { registerEnterprise } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const { register, handleSubmit, watch } = useForm();
  
  const password = watch("admin_password", "");

  const onSubmit = async (data: any) => {
    if (data.admin_password !== data.confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }
    
    setIsLoading(true);
    try {
      await registerEnterprise({
        org_name: data.org_name,
        admin_name: data.admin_name,
        admin_email: data.admin_email,
        admin_password: data.admin_password
      });
      toast.success("Organization created successfully! Please sign in.");
      router.push("/enterprise/login");
    } catch (err: any) {
      toast.error(err.response?.data?.error?.message || "Registration failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Link href="/" className="flex justify-center mb-6">
          <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
            <Building2 className="w-6 h-6 text-purple-600" />
          </div>
        </Link>
        <h2 className="text-center text-3xl font-extrabold text-gray-900">Register Organization</h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Create an enterprise account for your company
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-xl sm:rounded-2xl sm:px-10 border border-gray-100">
          <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Organization Name</label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Building2 className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  {...register("org_name", { required: true })}
                  type="text"
                  className="appearance-none block w-full pl-10 px-3 py-3 border border-gray-300 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent sm:text-sm transition-all"
                  placeholder="Acme Corp"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Admin Name</label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <UserIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  {...register("admin_name", { required: true })}
                  type="text"
                  className="appearance-none block w-full pl-10 px-3 py-3 border border-gray-300 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent sm:text-sm transition-all"
                  placeholder="Jane Smith"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Work Email</label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  {...register("admin_email", { required: true })}
                  type="email"
                  className="appearance-none block w-full pl-10 px-3 py-3 border border-gray-300 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent sm:text-sm transition-all"
                  placeholder="jane@acme.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Admin Password</label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  {...register("admin_password", { required: true })}
                  type="password"
                  className="appearance-none block w-full pl-10 px-3 py-3 border border-gray-300 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent sm:text-sm transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Confirm Password</label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  {...register("confirmPassword", { required: true })}
                  type="password"
                  className="appearance-none block w-full pl-10 px-3 py-3 border border-gray-300 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent sm:text-sm transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-gray-900 hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 transition-all"
            >
              {isLoading ? "Creating Organization..." : "Create Organization"} <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="mt-6">
            <div className="relative flex justify-center text-sm">
              <span className="text-gray-500">
                Already have an organization?{' '}
                <Link href="/enterprise/login" className="text-purple-600 hover:text-purple-500 font-medium">
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
