"use client";
import React from "react";
import { Database, UploadCloud } from "lucide-react";

export default function PersonalKnowledgePage() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center h-full p-8 text-center">
      <div className="w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-6 border border-blue-500/20">
        <Database className="w-8 h-8 text-blue-400" />
      </div>
      <h1 className="text-2xl font-bold text-white mb-3">My Knowledge</h1>
      <p className="text-gray-400 max-w-md mb-8">
        This is where you will manage your personal files, documents, and data for the AI to contextually learn from.
      </p>
      
      <button className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-colors font-medium">
        <UploadCloud className="w-4 h-4" />
        Upload Documents
      </button>
      
      <div className="mt-12 w-full max-w-3xl border border-gray-800 rounded-2xl bg-gray-900/50 p-8 flex flex-col items-center justify-center border-dashed">
        <p className="text-gray-500">No knowledge sources added yet.</p>
      </div>
    </div>
  );
}
