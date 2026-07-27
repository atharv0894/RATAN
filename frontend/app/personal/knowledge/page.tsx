"use client";
import React, { useState } from "react";
import { Database, UploadCloud, Folder, Search, Filter, List, Grid, FileText, MoreVertical } from "lucide-react";

export default function PersonalKnowledgePage() {
  const [view, setView] = useState<'grid' | 'list'>('list');
  const [search, setSearch] = useState("");

  const dummyFiles = [
    { id: 1, name: "Q3_Financial_Report.pdf", type: "PDF", size: "2.4 MB", uploaded: "2 hours ago", status: "Processed", chunks: 142 },
    { id: 2, name: "Employee_Handbook_2026.docx", type: "DOCX", size: "1.1 MB", uploaded: "Yesterday", status: "Processing", chunks: 0 },
    { id: 3, name: "Product_Roadmap.csv", type: "CSV", size: "450 KB", uploaded: "3 days ago", status: "Failed", chunks: 0 },
    { id: 4, name: "Marketing_Strategy_v2.pdf", type: "PDF", size: "5.7 MB", uploaded: "Last week", status: "Processed", chunks: 315 },
  ];

  return (
    <div className="flex-1 flex flex-col h-full bg-(--bg) text-(--text-primary) overflow-y-auto selection:bg-primary/30">
      
      {/* Header */}
      <div className="h-16 md:h-20 border-b border-(--border) flex items-center justify-between px-4 md:px-8 bg-(--bg) sticky top-0 z-10 pt-4 md:pt-0">
        <div className="ml-10 md:ml-0 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-(--primary) to-(--accent) flex items-center justify-center shadow-[var(--shadow-glow)]">
            <Database className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-(--text-primary) tracking-tight">My Knowledge</h1>
            <p className="text-xs text-(--text-secondary) hidden sm:block">Manage documents and data sources for your personal AI</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <button className="hidden sm:flex items-center gap-2 px-4 py-2 bg-(--surface-2) hover:bg-(--surface) border border-(--border) text-(--text-primary) rounded-xl transition-all shadow-sm text-sm font-medium">
            <Folder className="w-4 h-4 text-(--text-secondary)" />
            New Folder
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-(--primary) hover:bg-(--primary-hover) text-white rounded-xl transition-all shadow-sm text-sm font-medium">
            <UploadCloud className="w-4 h-4" />
            <span className="hidden sm:inline">Upload Files</span>
            <span className="sm:hidden">Upload</span>
          </button>
        </div>
      </div>

      <div className="p-4 md:p-8 max-w-[1600px] mx-auto w-full space-y-6">
        
        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="relative w-full sm:w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-(--text-secondary)" />
            <input 
              type="text" 
              placeholder="Search files, folders, or content..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-(--surface) border border-(--border) rounded-xl text-sm focus:border-(--primary) focus:ring-1 focus:ring-(--primary) outline-none transition-all shadow-sm text-(--text-primary) placeholder-(--text-secondary)"
            />
          </div>
          
          <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-2 sm:pb-0">
            <button className="px-3 py-2 bg-(--surface) border border-(--border) rounded-xl text-sm font-medium text-(--text-secondary) hover:text-(--text-primary) flex items-center gap-2 shrink-0">
              <Filter className="w-4 h-4" /> Filter
            </button>
            <div className="h-6 w-px bg-(--border) mx-1"></div>
            <div className="bg-(--surface) border border-(--border) rounded-xl flex items-center p-1 shrink-0">
              <button 
                onClick={() => setView('list')}
                className={`p-1.5 rounded-lg transition-colors ${view === 'list' ? 'bg-(--surface-2) text-(--text-primary) shadow-sm' : 'text-(--text-secondary) hover:text-(--text-primary)'}`}
              >
                <List className="w-4 h-4" />
              </button>
              <button 
                onClick={() => setView('grid')}
                className={`p-1.5 rounded-lg transition-colors ${view === 'grid' ? 'bg-(--surface-2) text-(--text-primary) shadow-sm' : 'text-(--text-secondary) hover:text-(--text-primary)'}`}
              >
                <Grid className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Upload Zone (Drag & Drop) */}
        <div className="w-full border-2 border-dashed border-(--border) hover:border-(--primary)/50 bg-(--surface)/50 hover:bg-(--surface) rounded-2xl p-8 flex flex-col items-center justify-center transition-all cursor-pointer group">
          <div className="w-12 h-12 bg-(--surface-2) rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            <UploadCloud className="w-6 h-6 text-(--text-secondary) group-hover:text-(--primary) transition-colors" />
          </div>
          <p className="text-sm font-medium text-(--text-primary) mb-1">Click to upload or drag and drop</p>
          <p className="text-xs text-(--text-secondary)">PDF, DOCX, TXT, CSV up to 50MB</p>
        </div>

        {/* Data View */}
        {view === 'list' ? (
          <div className="bg-(--surface) border border-(--border) rounded-2xl shadow-sm overflow-hidden flex flex-col">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse whitespace-nowrap">
                <thead>
                  <tr className="border-b border-(--border) bg-(--surface-2)/50 text-(--text-secondary) text-xs uppercase tracking-wider">
                    <th className="p-4 font-semibold w-10 text-center"><input type="checkbox" className="rounded border-(--border) bg-(--bg)" /></th>
                    <th className="p-4 font-semibold">Name</th>
                    <th className="p-4 font-semibold hidden md:table-cell">Size</th>
                    <th className="p-4 font-semibold hidden sm:table-cell">Uploaded</th>
                    <th className="p-4 font-semibold hidden lg:table-cell">Chunks</th>
                    <th className="p-4 font-semibold">Status</th>
                    <th className="p-4 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="text-sm divide-y divide-(--border)">
                  {dummyFiles.map((file) => (
                    <tr key={file.id} className="hover:bg-(--surface-2)/50 transition-colors group">
                      <td className="p-4 text-center"><input type="checkbox" className="rounded border-(--border) bg-(--bg)" /></td>
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <FileText className="w-5 h-5 text-(--primary)" />
                          <span className="font-medium text-(--text-primary)">{file.name}</span>
                        </div>
                      </td>
                      <td className="p-4 text-(--text-secondary) hidden md:table-cell">{file.size}</td>
                      <td className="p-4 text-(--text-secondary) hidden sm:table-cell">{file.uploaded}</td>
                      <td className="p-4 text-(--text-secondary) hidden lg:table-cell">{file.chunks > 0 ? file.chunks : '-'}</td>
                      <td className="p-4">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border
                          ${file.status === 'Processed' ? 'bg-[var(--success)]/10 text-[var(--success)] border-[var(--success)]/20' : 
                            file.status === 'Processing' ? 'bg-[var(--warning)]/10 text-[var(--warning)] border-[var(--warning)]/20' : 
                            'bg-[var(--danger)]/10 text-[var(--danger)] border-[var(--danger)]/20'
                          }
                        `}>
                          {file.status === 'Processing' && <span className="w-1.5 h-1.5 rounded-full bg-[var(--warning)] animate-pulse" />}
                          {file.status === 'Processed' && <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)]" />}
                          {file.status === 'Failed' && <span className="w-1.5 h-1.5 rounded-full bg-[var(--danger)]" />}
                          {file.status}
                        </span>
                      </td>
                      <td className="p-4 text-right">
                        <button className="p-1.5 text-(--text-secondary) hover:text-(--text-primary) rounded-md opacity-0 group-hover:opacity-100 transition-opacity">
                          <MoreVertical className="w-4 h-4" />
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
            {dummyFiles.map((file) => (
              <div key={file.id} className="card-premium p-5 flex flex-col gap-4 group cursor-pointer relative overflow-hidden">
                <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button className="p-1.5 bg-(--surface) shadow-sm border border-(--border) text-(--text-secondary) hover:text-(--text-primary) rounded-md">
                    <MoreVertical className="w-4 h-4" />
                  </button>
                </div>
                <div className="w-12 h-12 bg-(--primary)/10 rounded-xl flex items-center justify-center border border-(--primary)/20">
                  <FileText className="w-6 h-6 text-(--primary)" />
                </div>
                <div>
                  <h3 className="font-semibold text-(--text-primary) truncate mb-1" title={file.name}>{file.name}</h3>
                  <div className="flex items-center gap-2 text-xs text-(--text-secondary)">
                    <span>{file.type}</span>
                    <span>•</span>
                    <span>{file.size}</span>
                  </div>
                </div>
                <div className="mt-auto pt-4 flex items-center justify-between border-t border-(--border)">
                  <span className={`inline-flex items-center gap-1.5 text-xs font-medium
                    ${file.status === 'Processed' ? 'text-[var(--success)]' : 
                      file.status === 'Processing' ? 'text-[var(--warning)]' : 
                      'text-[var(--danger)]'
                    }
                  `}>
                    {file.status}
                  </span>
                  <span className="text-[10px] text-(--text-secondary)">{file.uploaded}</span>
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
