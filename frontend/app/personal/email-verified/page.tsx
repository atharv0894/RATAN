"use client";

import Link from "next/link";
import { CheckCircle2 } from "lucide-react";

export default function EmailVerifiedPage() {
  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <div className="w-full max-w-md p-8 bg-gray-900 border border-gray-800 rounded-xl shadow-2xl flex flex-col items-center text-center space-y-6">
        <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center">
          <CheckCircle2 className="w-10 h-10 text-green-500" />
        </div>
        <h2 className="text-2xl font-bold text-white">Email Verified Successfully</h2>
        <p className="text-gray-400 max-w-sm">
          Your email has been verified successfully. You can now sign in and start using your Personal AI Workspace.
        </p>
        <Link 
          href="/personal/login" 
          className="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg transition-colors flex items-center justify-center"
        >
          Sign In Now
        </Link>
      </div>
    </div>
  );
}
