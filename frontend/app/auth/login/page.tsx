"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { authApi, setTokens } from "@/lib/api";
import { toast } from "sonner";
import { Eye, EyeOff, Cpu, ArrowRight, Lock, Mail, Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

const schema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type FormData = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setIsLoading(true);
    try {
      await login(data.email, data.password);
      toast.success("Welcome back!");
      router.push("/dashboard");
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      toast.error(axiosError?.response?.data?.detail ?? "Invalid credentials");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left panel */}
      <div className="hidden lg:flex w-1/2 bg-[#080F1A] border-r border-border-default flex-col justify-between p-10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-linear-to-br from-primary to-accent flex items-center justify-center">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <span className="text-lg font-bold text-white">RATAN</span>
        </div>

        <div className="space-y-6">
          <div className="w-12 h-1 bg-linear-to-r from-primary to-accent rounded-full" />
          <h2 className="text-4xl font-bold text-white leading-tight">
            Industrial Knowledge<br />
            <span className="gradient-text">Intelligence Platform</span>
          </h2>
          <p className="text-muted-foreground text-lg leading-relaxed">
            Transform raw industrial documents into a searchable, AI-powered knowledge base for your organization.
          </p>
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: "Documents Indexed", value: "50K+" },
              { label: "Queries/Day", value: "10K+" },
              { label: "Avg. Confidence", value: "94%" },
              { label: "Organizations", value: "500+" },
            ].map((stat) => (
              <div key={stat.label} className="card-premium p-4">
                <p className="text-2xl font-bold gradient-text">{stat.value}</p>
                <p className="text-xs text-muted-foreground mt-1">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>

        <p className="text-xs text-muted-foreground/50">
          © 2026 RATAN Enterprise Platform
        </p>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md space-y-8">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-8 h-8 rounded-lg bg-linear-to-br from-primary to-accent flex items-center justify-center">
              <Cpu className="w-4 h-4 text-white" />
            </div>
            <span className="text-base font-bold text-white">RATAN</span>
          </div>

          <div>
            <h1 className="text-2xl font-bold text-white">Sign in to RATAN</h1>
            <p className="text-muted-foreground mt-1">Access your organization&apos;s knowledge base</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground-2 mb-1.5">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  {...register("email")}
                  type="email"
                  placeholder="you@company.com"
                  className="input-field pl-10!"
                  autoComplete="email"
                />
              </div>
              {errors.email && <p className="text-danger text-xs mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground-2 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  {...register("password")}
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  className="input-field pl-10! pr-10!"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && <p className="text-danger text-xs mt-1">{errors.password.message}</p>}
            </div>

            <div className="flex items-center justify-end">
              <Link href="/auth/forgot-password" className="text-sm text-primary hover:text-accent transition-colors">
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full py-3 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Signing in...</>
              ) : (
                <>Sign In <ArrowRight className="w-4 h-4" /></>
              )}
            </button>
          </form>

          <p className="text-center text-sm text-muted-foreground">
            New to RATAN?{" "}
            <Link href="/auth/register" className="text-primary hover:text-accent transition-colors font-medium">
              Register your organization
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
