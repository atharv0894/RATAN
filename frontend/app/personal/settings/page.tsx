"use client";
import React from "react";
import { Settings, Shield, User } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export default function PersonalSettingsPage() {
  const { user } = useAuth();
  
  return (
    <div className="flex-1 flex flex-col h-full p-8 overflow-y-auto">
      <div className="max-w-3xl mx-auto w-full">
        <h1 className="text-2xl font-bold text-white mb-8">Account Settings</h1>
        
        <div className="space-y-6">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-gray-200 mb-4 flex items-center gap-2">
              <User className="w-5 h-5 text-gray-400" />
              Profile Details
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">Full Name</label>
                <div className="text-gray-200 bg-gray-800 px-4 py-2 rounded-lg">{user?.full_name}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 mb-1">Email Address</label>
                <div className="text-gray-200 bg-gray-800 px-4 py-2 rounded-lg">{user?.email}</div>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-gray-200 mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5 text-gray-400" />
              Security
            </h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-800 rounded-xl">
                <div>
                  <div className="font-medium text-gray-200">Password</div>
                  <div className="text-sm text-gray-500">Update your password to keep your account secure</div>
                </div>
                <button className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm font-medium transition-colors">
                  Change
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
