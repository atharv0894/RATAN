"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { authApi } from "@/lib/api";
import { CheckCircle2, XCircle, Loader2, Mail } from "lucide-react";
import Link from "next/link";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const router = useRouter();
  
  const [status, setStatus] = useState<"loading" | "success" | "error" | "waiting">("waiting");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (token) {
      setStatus("loading");
      authApi.verify_email(token)
        .then(() => {
          setStatus("success");
          setTimeout(() => {
            router.push("/personal/email-verified");
          }, 1500);
        })
        .catch((err) => {
          setStatus("error");
          setErrorMessage(err.response?.data?.detail || "Verification failed. The link may be invalid or expired.");
        });
    }
  }, [token, router]);

  if (status === "loading") {
    return (
      <div className="flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
        <h2 className="text-xl font-semibold text-white">Verifying your email...</h2>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="flex flex-col items-center text-center space-y-4">
        <XCircle className="w-16 h-16 text-red-500" />
        <h2 className="text-2xl font-bold text-white">Verification Failed</h2>
        <p className="text-red-400 max-w-sm">{errorMessage}</p>
        <Link href="/personal/login" className="mt-6 bg-gray-800 text-white px-6 py-2 rounded-md hover:bg-gray-700 transition-colors">
          Return to Login
        </Link>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="flex flex-col items-center text-center space-y-4">
        <CheckCircle2 className="w-16 h-16 text-green-500" />
        <h2 className="text-2xl font-bold text-white">Email Verified!</h2>
        <p className="text-gray-400">Redirecting to login...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center text-center space-y-6">
      <div className="w-20 h-20 bg-blue-500/20 rounded-full flex items-center justify-center">
        <Mail className="w-10 h-10 text-blue-400" />
      </div>
      <h2 className="text-2xl font-bold text-white">Check your email</h2>
      <p className="text-gray-400 max-w-sm">
        We've sent a verification link to your email. Please verify your account before signing in.
      </p>
      <Link href="/personal/login" className="mt-4 text-blue-400 hover:text-blue-300 font-medium text-sm transition-colors">
        Return to login
      </Link>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <div className="w-full max-w-md p-8 bg-gray-900 border border-gray-800 rounded-xl shadow-2xl">
        <Suspense fallback={<div className="flex justify-center"><Loader2 className="w-8 h-8 text-blue-500 animate-spin" /></div>}>
          <VerifyEmailContent />
        </Suspense>
      </div>
    </div>
  );
}
