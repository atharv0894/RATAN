"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { authApi } from "@/lib/api";
import { toast } from "sonner";
import { Cpu, Building2, User, Mail, Lock, ArrowRight, Loader2, CheckCircle } from "lucide-react";

const schema = z.object({
  org_name: z.string().min(2, "Organization name must be at least 2 characters"),
  admin_name: z.string().min(2, "Your name must be at least 2 characters"),
  admin_email: z.string().email("Please enter a valid email address"),
  admin_password: z.string().min(8, "Password must be at least 8 characters"),
  confirm_password: z.string(),
}).refine((data) => data.admin_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
});

type FormData = z.infer<typeof schema>;

export default function RegisterPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setIsLoading(true);
    try {
      await authApi.register({
        org_name: data.org_name,
        admin_email: data.admin_email,
        admin_password: data.admin_password,
        admin_name: data.admin_name,
      });
      setSuccess(true);
      toast.success("Organization registered! You can now log in.");
      setTimeout(() => router.push("/auth/login"), 2000);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      toast.error(axiosError?.response?.data?.detail ?? "Registration failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-8">
      <div className="w-full max-w-lg space-y-8">
        <div className="text-center space-y-3">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-linear-to-br from-primary to-accent flex items-center justify-center">
              <Cpu className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">RATAN</span>
          </div>
          <h1 className="text-2xl font-bold text-white">Create your organization</h1>
          <p className="text-muted-foreground">Set up RATAN for your industrial enterprise</p>
        </div>

        {success ? (
          <div className="card-premium p-8 text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-success/10 flex items-center justify-center mx-auto">
              <CheckCircle className="w-8 h-8 text-success" />
            </div>
            <h2 className="text-lg font-semibold text-white">Organization Created!</h2>
            <p className="text-muted-foreground text-sm">Redirecting you to login...</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="card-premium p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground-2 mb-1.5">Organization Name</label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input {...register("org_name")} placeholder="Acme Manufacturing Co." className="input-field pl-10!" />
              </div>
              {errors.org_name && <p className="text-danger text-xs mt-1">{errors.org_name.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground-2 mb-1.5">Your Full Name</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input {...register("admin_name")} placeholder="John Smith" className="input-field pl-10!" />
              </div>
              {errors.admin_name && <p className="text-danger text-xs mt-1">{errors.admin_name.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground-2 mb-1.5">Admin Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input {...register("admin_email")} type="email" placeholder="admin@company.com" className="input-field pl-10!" />
              </div>
              {errors.admin_email && <p className="text-danger text-xs mt-1">{errors.admin_email.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground-2 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input {...register("admin_password")} type="password" placeholder="Min. 8 characters" className="input-field pl-10!" />
              </div>
              {errors.admin_password && <p className="text-danger text-xs mt-1">{errors.admin_password.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground-2 mb-1.5">Confirm Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input {...register("confirm_password")} type="password" placeholder="Re-enter password" className="input-field pl-10!" />
              </div>
              {errors.confirm_password && <p className="text-danger text-xs mt-1">{errors.confirm_password.message}</p>}
            </div>

            <button type="submit" disabled={isLoading} className="btn-primary w-full py-3 flex items-center justify-center gap-2 mt-2">
              {isLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating...</> : <>Create Organization <ArrowRight className="w-4 h-4" /></>}
            </button>
          </form>
        )}

        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/auth/login" className="text-primary hover:text-accent transition-colors font-medium">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
