"use client";
import React, { useState, useRef } from "react";
import { Database, UploadCloud, Folder, Search, Filter, List, Grid, FileText, MoreVertical, Trash2, Loader2 } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { personalFilesApi } from "@/lib/api";
import { toast } from "sonner";

function formatRelativeTime(timestamp: number) {
  const diff = Date.now() - timestamp;
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;
  const days = Math.floor(hours / 24);
  return `${days} days ago`;
}

interface PersonalFile {
  id: string;
  filename: string;
  file_size: number;
  mime_type: string;
  created_at: number;
}

export default function PersonalKnowledgePage() {
  const [view, setView] = useState<'grid' | 'list'>('list');
  const [search, setSearch] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["personal_files"],
    queryFn: () => personalFilesApi.list().then((res) => res.data.data.files as PersonalFile[]),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => personalFilesApi.upload(file),
    onSuccess: () => {
      toast.success("File uploaded successfully");
      queryClient.invalidateQueries({ queryKey: ["personal_files"] });
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error?.message || "Upload failed");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => personalFilesApi.delete(id),
    onSuccess: () => {
      toast.success("File deleted");
      queryClient.invalidateQueries({ queryKey: ["personal_files"] });
    },
    onError: () => toast.error("Failed to delete file"),
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      Array.from(e.target.files).forEach((file) => {
        uploadMutation.mutate(file);
      });
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      Array.from(e.dataTransfer.files).forEach((file) => {
        uploadMutation.mutate(file);
      });
    }
  };

  const files = data || [];
  const filteredFiles = files.filter(f => f.filename.toLowerCase().includes(search.toLowerCase()));

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-bg text-text-primary overflow-y-auto selection:bg-primary/30">
      
      {/* Header */}
      <div className="h-16 md:h-20 border-b border-border-default flex items-center justify-between px-4 md:px-8 bg-bg sticky top-0 z-10 pt-4 md:pt-0">
        <div className="ml-10 md:ml-0 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-glow">
            <Database className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-text-primary tracking-tight">My Knowledge</h1>
            <p className="text-xs text-text-secondary hidden sm:block">Manage documents and data sources for your personal AI</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <button className="hidden sm:flex items-center gap-2 px-4 py-2 bg-surface-2 hover:bg-surface border border-border-default text-text-primary rounded-xl transition-all shadow-sm text-sm font-medium">
            <Folder className="w-4 h-4 text-text-secondary" />
            New Folder
          </button>
          <input type="file" multiple className="hidden" ref={fileInputRef} onChange={handleFileChange} />
          <button 
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-xl transition-all shadow-sm text-sm font-medium disabled:opacity-50"
          >
            {uploadMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <UploadCloud className="w-4 h-4" />}
            <span className="hidden sm:inline">{uploadMutation.isPending ? "Uploading..." : "Upload Files"}</span>
            <span className="sm:hidden">Upload</span>
          </button>
        </div>
      </div>

      <div className="p-4 md:p-8 max-w-[1600px] mx-auto w-full space-y-6">
        
        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="relative w-full sm:w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
            <input 
              type="text" 
              placeholder="Search files, folders, or content..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-surface border border-border-default rounded-xl text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all shadow-sm text-text-primary placeholder-text-secondary"
            />
          </div>
          
          <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-2 sm:pb-0">
            <button className="px-3 py-2 bg-surface border border-border-default rounded-xl text-sm font-medium text-text-secondary hover:text-text-primary flex items-center gap-2 shrink-0">
              <Filter className="w-4 h-4" /> Filter
            </button>
            <div className="h-6 w-px bg-border-default mx-1"></div>
            <div className="bg-surface border border-border-default rounded-xl flex items-center p-1 shrink-0">
              <button 
                onClick={() => setView('list')}
                className={`p-1.5 rounded-lg transition-colors ${view === 'list' ? 'bg-surface-2 text-text-primary shadow-sm' : 'text-text-secondary hover:text-text-primary'}`}
              >
                <List className="w-4 h-4" />
              </button>
              <button 
                onClick={() => setView('grid')}
                className={`p-1.5 rounded-lg transition-colors ${view === 'grid' ? 'bg-surface-2 text-text-primary shadow-sm' : 'text-text-secondary hover:text-text-primary'}`}
              >
                <Grid className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Upload Zone (Drag & Drop) */}
        <div 
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className="w-full border-2 border-dashed border-border-default hover:border-primary/50 bg-surface/50 hover:bg-surface rounded-2xl p-8 flex flex-col items-center justify-center transition-all cursor-pointer group"
        >
          <div className="w-12 h-12 bg-surface-2 rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            {uploadMutation.isPending ? <Loader2 className="w-6 h-6 animate-spin text-primary" /> : <UploadCloud className="w-6 h-6 text-text-secondary group-hover:text-primary transition-colors" />}
          </div>
          <p className="text-sm font-medium text-text-primary mb-1">Click to upload or drag and drop</p>
          <p className="text-xs text-text-secondary">PDF, DOCX, TXT, CSV up to 50MB</p>
        </div>

        {/* Data View */}
        {view === 'list' ? (
          <div className="card-premium overflow-hidden flex flex-col bg-surface shadow-card">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse whitespace-nowrap">
                <thead className="sticky top-0 bg-surface/95 backdrop-blur-md z-10">
                  <tr className="border-b border-border-default">
                    <th className="px-4 py-3 font-semibold w-10 text-center"><input type="checkbox" className="rounded border-border-default bg-surface text-primary focus:ring-primary/20 transition-all cursor-pointer" /></th>
                    <th className="px-4 py-3 text-[11px] font-semibold text-text-secondary uppercase tracking-wider">Document Name</th>
                    <th className="px-4 py-3 text-[11px] font-semibold text-text-secondary uppercase tracking-wider hidden md:table-cell">Size</th>
                    <th className="px-4 py-3 text-[11px] font-semibold text-text-secondary uppercase tracking-wider hidden sm:table-cell">Uploaded</th>
                    <th className="px-4 py-3 text-[11px] font-semibold text-text-secondary uppercase tracking-wider text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="text-sm divide-y divide-border-default/50">
                  {isLoading ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-16 text-center text-text-secondary">
                        <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
                        <p>Loading files...</p>
                      </td>
                    </tr>
                  ) : filteredFiles.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-16 text-center text-text-secondary">
                        <p>No files found. Upload your first document!</p>
                      </td>
                    </tr>
                  ) : filteredFiles.map((file) => (
                    <tr key={file.id} className="hover:bg-surface-2/60 transition-colors group">
                      <td className="px-4 py-3.5 text-center"><input type="checkbox" className="rounded border-border-default bg-surface text-primary focus:ring-primary/20 transition-all cursor-pointer opacity-0 group-hover:opacity-100" /></td>
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-primary/5 border border-primary/10 flex items-center justify-center shrink-0">
                            <FileText className="w-4 h-4 text-primary" />
                          </div>
                          <span className="font-medium text-text-primary group-hover:text-primary transition-colors truncate max-w-xs">{file.filename}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3.5 text-text-secondary text-xs hidden md:table-cell font-mono">{formatSize(file.file_size)}</td>
                      <td className="px-4 py-3.5 text-text-secondary text-xs hidden sm:table-cell">{formatRelativeTime(file.created_at * 1000)}</td>
                      <td className="px-4 py-3.5 text-right flex items-center justify-end gap-1">
                        <button 
                          onClick={() => { if(confirm("Delete file?")) deleteMutation.mutate(file.id); }}
                          className="p-1.5 text-text-secondary hover:bg-danger/10 border border-transparent hover:border-danger/20 hover:text-danger rounded-md opacity-0 group-hover:opacity-100 transition-all shadow-sm"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {isLoading ? (
               <div className="col-span-full py-16 text-center text-text-secondary">
                 <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
                 <p>Loading files...</p>
               </div>
            ) : filteredFiles.length === 0 ? (
               <div className="col-span-full py-16 text-center text-text-secondary">
                 <p>No files found. Upload your first document!</p>
               </div>
            ) : filteredFiles.map((file) => (
              <div key={file.id} className="card-premium p-5 flex flex-col gap-4 group cursor-pointer relative overflow-hidden">
                <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button 
                    onClick={() => { if(confirm("Delete file?")) deleteMutation.mutate(file.id); }}
                    className="p-1.5 bg-surface shadow-sm border border-border-default text-text-secondary hover:text-danger rounded-md"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center border border-primary/20">
                  <FileText className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-text-primary truncate mb-1" title={file.filename}>{file.filename}</h3>
                  <div className="flex items-center gap-2 text-xs text-text-secondary">
                    <span>{file.mime_type.split('/').pop()?.toUpperCase() || 'FILE'}</span>
                    <span>•</span>
                    <span>{formatSize(file.file_size)}</span>
                  </div>
                </div>
                <div className="mt-auto pt-4 flex items-center justify-between border-t border-border-default">
                  <span className="text-[10px] text-text-secondary">{formatRelativeTime(file.created_at * 1000)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
