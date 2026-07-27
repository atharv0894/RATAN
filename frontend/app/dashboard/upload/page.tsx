"use client";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { useState, useCallback } from "react";
import { documentsApi } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Upload, FileText, X, CheckCircle, AlertCircle, Loader2 } from "lucide-react";

interface UploadFile {
  id: string;
  file: File;
  status: "pending" | "uploading" | "done" | "error" | "duplicate";
  progress: number;
  message?: string;
  docId?: string;
}

export default function UploadPage() {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [metadata, setMetadata] = useState({ category: "", equipment: "", language: "English", author: "" });
  const qc = useQueryClient();

  const addFiles = useCallback((incoming: FileList | File[]) => {
    const arr = Array.from(incoming);
    const allowed = [".pdf", ".docx", ".txt", ".md", ".csv"];
    const valid = arr.filter((f) => allowed.some((ext) => f.name.toLowerCase().endsWith(ext)));
    if (valid.length !== arr.length) toast.warning("Some files were skipped. Only PDF, DOCX, TXT, MD, CSV are allowed.");
    setFiles((prev) => [
      ...prev,
      ...valid.map((f) => ({ id: Math.random().toString(36).slice(2), file: f, status: "pending" as const, progress: 0 })),
    ]);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    addFiles(e.dataTransfer.files);
  }, [addFiles]);

  const uploadFile = async (uf: UploadFile) => {
    setFiles((prev) => prev.map((f) => f.id === uf.id ? { ...f, status: "uploading", progress: 30 } : f));
    try {
      const res = await documentsApi.upload(uf.file, {
        category: metadata.category,
        equipment: metadata.equipment,
        language: metadata.language,
        author: metadata.author,
      });
      const result = res.data.data;
      setFiles((prev) => prev.map((f) => f.id === uf.id ? {
        ...f,
        status: result.duplicate ? "duplicate" : "done",
        progress: 100,
        message: result.duplicate ? "Duplicate document detected (same content already exists)" : "Successfully indexed",
        docId: result.document_id,
      } : f));
      if (!result.duplicate) qc.invalidateQueries({ queryKey: ["documents"] });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Upload failed";
      setFiles((prev) => prev.map((f) => f.id === uf.id ? { ...f, status: "error", progress: 0, message: msg } : f));
    }
  };

  const uploadAll = async () => {
    const pending = files.filter((f) => f.status === "pending");
    for (const uf of pending) await uploadFile(uf);
  };

  const removeFile = (id: string) => setFiles((prev) => prev.filter((f) => f.id !== id));
  const clearDone = () => setFiles((prev) => prev.filter((f) => f.status === "pending" || f.status === "uploading"));

  const pendingCount = files.filter((f) => f.status === "pending").length;
  const doneCount = files.filter((f) => f.status === "done").length;

  return (
    <DashboardLayout title="Upload Center" subtitle="Add documents to your knowledge base">
      <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">

        {/* Drop Zone */}
        <div
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onClick={() => document.getElementById("file-input")?.click()}
          className={cn(
            "border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200",
            isDragging ? "border-primary bg-primary/5 scale-[1.01]" : "border-border-default hover:border-primary/50 hover:bg-surface-2/30"
          )}
        >
          <input
            id="file-input"
            type="file"
            multiple
            accept=".pdf,.docx,.txt,.md,.csv"
            className="hidden"
            onChange={(e) => e.target.files && addFiles(e.target.files)}
          />
          <div className="flex flex-col items-center gap-4">
            <div className={cn("w-16 h-16 rounded-2xl flex items-center justify-center transition-all", isDragging ? "bg-primary/20 border border-primary/40" : "bg-surface-2 border border-border-default")}>
              <Upload className={cn("w-7 h-7 transition-colors", isDragging ? "text-primary" : "text-muted-foreground")} />
            </div>
            <div>
              <p className="text-base font-semibold text-foreground">{isDragging ? "Drop files here" : "Drag & drop files or click to browse"}</p>
              <p className="text-sm text-muted-foreground mt-1">Supports PDF, DOCX, TXT, MD, CSV · Max 50MB per file</p>
            </div>
          </div>
        </div>

        {/* Metadata Form */}
        <div className="card-premium p-5 space-y-4">
          <h3 className="text-sm font-semibold text-foreground">Document Metadata <span className="text-muted-foreground font-normal">(optional — applies to all files)</span></h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              { key: "category", label: "Category", placeholder: "e.g. Maintenance Manual" },
              { key: "equipment", label: "Equipment", placeholder: "e.g. Hydraulic Press HX-200" },
              { key: "language", label: "Language", placeholder: "e.g. English" },
              { key: "author", label: "Author", placeholder: "e.g. Engineering Team" },
            ].map(({ key, label, placeholder }) => (
              <div key={key}>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">{label}</label>
                <input
                  value={metadata[key as keyof typeof metadata]}
                  onChange={(e) => setMetadata((m) => ({ ...m, [key]: e.target.value }))}
                  placeholder={placeholder}
                  className="input-field text-sm h-9"
                />
              </div>
            ))}
          </div>
        </div>

        {/* File Queue */}
        {files.length > 0 && (
          <div className="card-premium overflow-hidden">
            <div className="px-4 py-3 border-b border-border-default flex items-center justify-between">
              <p className="text-sm font-semibold text-foreground">Upload Queue ({files.length} files)</p>
              <div className="flex items-center gap-2">
                {doneCount > 0 && <button onClick={clearDone} className="text-xs text-muted-foreground hover:text-foreground transition-colors">Clear Done</button>}
                {pendingCount > 0 && (
                  <button onClick={uploadAll} className="btn-primary px-3 py-1.5 text-sm flex items-center gap-1.5">
                    <Upload className="w-3.5 h-3.5" /> Upload All ({pendingCount})
                  </button>
                )}
              </div>
            </div>
            <div className="divide-y divide-[#1E2D45]">
              {files.map((uf) => (
                <div key={uf.id} className="px-4 py-3 flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                    <FileText className="w-4 h-4 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium text-foreground truncate">{uf.file.name}</p>
                      <div className="flex items-center gap-1 shrink-0">
                        {uf.status === "pending" && (
                          <button onClick={() => uploadFile(uf)} className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-lg hover:bg-primary/20 transition-colors">Upload</button>
                        )}
                        {uf.status !== "uploading" && (
                          <button onClick={() => removeFile(uf.id)} className="p-1 text-muted-foreground hover:text-danger transition-colors">
                            <X className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      {uf.status === "uploading" && (
                        <>
                          <div className="flex-1 h-1 bg-border-default rounded-full overflow-hidden">
                            <div className="h-full bg-primary rounded-full transition-all animate-pulse" style={{ width: `${uf.progress}%` }} />
                          </div>
                          <Loader2 className="w-3 h-3 text-primary animate-spin shrink-0" />
                        </>
                      )}
                      {uf.status === "done" && <span className="text-xs text-success flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Indexed</span>}
                      {uf.status === "duplicate" && <span className="text-xs text-warning flex items-center gap-1"><AlertCircle className="w-3 h-3" /> Duplicate</span>}
                      {uf.status === "error" && <span className="text-xs text-danger flex items-center gap-1"><AlertCircle className="w-3 h-3" /> {uf.message}</span>}
                      {uf.status === "pending" && <span className="text-xs text-muted-foreground">{(uf.file.size / 1024 / 1024).toFixed(2)} MB</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {files.length === 0 && (
          <div className="text-center py-4">
            <p className="text-xs text-muted-foreground">Files added here will appear in your upload queue before being submitted.</p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
