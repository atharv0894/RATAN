"use client";

import { useEffect, Suspense } from "react";
import { useRouter } from "next/navigation";
import { setTokens } from "@/lib/api";
import { Loader2 } from "lucide-react";

/**
 * /personal/google-callback
 *
 * The backend redirects here after Google OAuth completes:
 *   /personal/google-callback#access_token=xxx&refresh_token=yyy
 *
 * This page reads the fragment, stores the tokens, and redirects to /personal
 */
function GoogleCallbackContent() {
  const router = useRouter();

  useEffect(() => {
    const hash = window.location.hash.substring(1); // strip leading #
    const params = new URLSearchParams(hash);
    const accessToken = params.get("access_token");
    const refreshToken = params.get("refresh_token");

    if (accessToken && refreshToken) {
      setTokens(accessToken, refreshToken);
      router.replace("/personal");
    } else {
      // Something went wrong — send back to login with error
      router.replace("/personal/login?error=google_failed");
    }
  }, [router]);

  return (
    <div className="flex flex-col items-center gap-4 text-white">
      <Loader2 className="w-10 h-10 animate-spin text-blue-500" />
      <p className="text-gray-400 text-sm">Completing Google sign-in...</p>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <Suspense fallback={
        <div className="flex items-center gap-3 text-white">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          <span className="text-gray-400">Loading...</span>
        </div>
      }>
        <GoogleCallbackContent />
      </Suspense>
    </div>
  );
}
