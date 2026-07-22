"use client";

import { useQuery } from "@tanstack/react-query";
import { entitiesApi } from "@/lib/api";
import { Boxes, Loader2, RefreshCw, X, FileText, Search } from "lucide-react";
import dynamic from "next/dynamic";
import { useState, useMemo } from "react";
import { toast } from "sonner";

// Dynamically import ForceGraph to prevent SSR errors (Canvas/window is not defined on server)
const DynamicForceGraph = dynamic(() => import("@/components/graph/ForceGraph"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[600px] bg-surface rounded-xl flex items-center justify-center border border-border-default">
      <div className="flex flex-col items-center gap-4 text-muted-foreground">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <p className="animate-pulse">Loading visualization engine...</p>
      </div>
    </div>
  ),
});

const LEGEND_ITEMS = [
  { group: 1, label: "Documents", color: "bg-blue-500", shadow: "shadow-[0_0_10px_rgba(59,130,246,0.8)]" },
  { group: 2, label: "Roles", color: "bg-amber-500", shadow: "shadow-[0_0_10px_rgba(245,158,11,0.8)]" },
  { group: 3, label: "Equipment", color: "bg-emerald-500", shadow: "shadow-[0_0_10px_rgba(16,185,129,0.8)]" },
  { group: 4, label: "Standards", color: "bg-purple-500", shadow: "shadow-[0_0_10px_rgba(168,85,247,0.8)]" },
  { group: 5, label: "Safety", color: "bg-red-500", shadow: "shadow-[0_0_10px_rgba(239,68,68,0.8)]" },
  { group: 6, label: "Tools", color: "bg-cyan-500", shadow: "shadow-[0_0_10px_rgba(6,182,212,0.8)]" },
  { group: 7, label: "Parameters", color: "bg-rose-500", shadow: "shadow-[0_0_10px_rgba(244,63,94,0.8)]" },
  { group: 8, label: "Organizations", color: "bg-violet-500", shadow: "shadow-[0_0_10px_rgba(139,92,246,0.8)]" },
  { group: 9, label: "Concepts", color: "bg-pink-500", shadow: "shadow-[0_0_10px_rgba(236,72,153,0.8)]" },
];

export default function GraphPage() {
  const [selectedEntity, setSelectedEntity] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["knowledgeGraph"],
    queryFn: async () => {
      const res = await entitiesApi.graph();
      return res.data.data;
    },
    refetchInterval: 10000, // Poll every 10 seconds for live updates
  });

  const handleNodeClick = async (node: any) => {
    // If it's an entity node (group > 1)
    if (node.group > 1) {
      setIsLoadingDetails(true);
      try {
        const res = await entitiesApi.getDetails(node.id);
        setSelectedEntity(res.data.data);
      } catch (err) {
        toast.error("Failed to load entity details");
      } finally {
        setIsLoadingDetails(false);
      }
    } else {
      // It's a document node (group === 1)
      // Could potentially link to document viewer here
      toast.info(`Document: ${node.name}`);
    }
  };

  const filteredData = useMemo(() => {
    if (!data) return { nodes: [], edges: [], statistics: {} };
    if (!searchQuery.trim()) return data;

    const lowerQuery = searchQuery.toLowerCase();
    const filteredNodes = data.nodes.filter((n: any) => 
      n.label?.toLowerCase().includes(lowerQuery) || 
      n.type?.toLowerCase().includes(lowerQuery)
    );
    
    const validNodeIds = new Set(filteredNodes.map((n: any) => n.id));
    
    // Only include edges where both source and target still exist in the filtered nodes
    const filteredEdges = data.edges.filter((e: any) => 
      validNodeIds.has(e.source) && validNodeIds.has(e.target)
    );

    return { ...data, nodes: filteredNodes, edges: filteredEdges };
  }, [data, searchQuery]);

  return (
    <div className="animate-fade-in flex flex-col" style={{ height: 'calc(100vh - 80px)' }}>
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Boxes className="w-6 h-6 text-primary" />
            Knowledge Graph
          </h1>
          <p className="text-muted-foreground text-sm">
            Interactive visualization of extracted entities, components, and documents.
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="relative w-64">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search graph..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-surface border border-border-default rounded-lg pl-9 pr-4 py-2 text-sm text-foreground focus:outline-none focus:border-primary transition-colors"
            />
          </div>
          <button 
            onClick={() => refetch()} 
            disabled={isLoading}
            className="px-4 py-2 bg-surface hover:bg-surface-2 border border-border-default rounded-lg text-sm text-foreground flex items-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      <div className="flex-1 min-h-0 relative">
        {isLoading ? (
          <div className="w-full h-full bg-surface rounded-xl flex items-center justify-center border border-border-default">
            <div className="flex flex-col items-center gap-4 text-muted-foreground">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
              <p className="animate-pulse">Querying relationship data...</p>
            </div>
          </div>
        ) : isError ? (
          <div className="w-full h-full bg-surface/50 rounded-xl flex items-center justify-center border border-danger/50 p-6 text-center">
            <div className="max-w-md space-y-4">
              <div className="w-16 h-16 bg-danger/10 text-danger rounded-full flex items-center justify-center mx-auto">
                <Boxes className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-medium text-danger">Failed to load graph</h3>
              <p className="text-sm text-muted-foreground">
                There was an error communicating with the backend API. Ensure the /entities/graph endpoint is functioning correctly.
              </p>
              <button 
                onClick={() => refetch()}
                className="px-4 py-2 bg-danger text-white rounded-lg hover:bg-danger-hover transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        ) : data?.nodes?.length === 0 ? (
          <div className="w-full h-full bg-surface rounded-xl flex items-center justify-center border border-border-default p-6 text-center">
            <div className="max-w-md space-y-4">
              <div className="w-16 h-16 bg-primary/10 text-primary rounded-full flex items-center justify-center mx-auto">
                <Boxes className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-medium text-foreground">Graph is Empty</h3>
              <p className="text-sm text-muted-foreground">
                No documents or entities have been processed yet. Upload and process industrial manuals to see the automated relationship graph.
              </p>
            </div>
          </div>
        ) : (
          <div className="w-full h-full flex flex-col gap-4">
            <div className="flex items-center justify-between px-4 py-3 bg-surface-2 border border-border-default rounded-lg text-sm overflow-x-auto whitespace-nowrap">
              <div className="flex items-center gap-5">
                {LEGEND_ITEMS.filter(item => data?.nodes?.some((n: any) => n.group === item.group)).map(item => (
                  <div key={item.group} className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${item.color} ${item.shadow}`} />
                    {item.label}
                  </div>
                ))}
              </div>
              <div className="text-muted-foreground ml-4 shrink-0 font-mono">
                Nodes: {filteredData.nodes.length} | Edges: {filteredData.edges.length}
              </div>
            </div>
            
            <div className="flex gap-4">
               {/* Live Statistics Panel */}
               <div className="w-full grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2">
                 {data?.statistics && Object.entries(data.statistics).map(([key, val]) => (
                   <div key={key} className="bg-surface-2 border border-border-default rounded-md p-2 text-center shadow-sm">
                     <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold truncate">{key}</p>
                     <p className="text-sm font-bold text-foreground mt-0.5">{val as React.ReactNode}</p>
                   </div>
                 ))}
               </div>
            </div>
            
            <div className="flex-1 flex gap-4 overflow-hidden relative" style={{ minHeight: 0 }}>
              <div className="flex-1 rounded-xl overflow-hidden" style={{ minHeight: 0 }}>
                <DynamicForceGraph data={filteredData} onNodeClick={handleNodeClick} />
              </div>
              
              {/* Sliding Side Panel */}
              {selectedEntity && (
                <div className="w-80 bg-surface border border-border-default rounded-xl flex flex-col animate-slide-in-right overflow-hidden shadow-xl absolute right-0 top-0 bottom-0 z-10">
                  <div className="p-4 border-b border-border-default flex items-center justify-between bg-surface-2">
                    <h3 className="font-semibold text-foreground truncate pr-2">{selectedEntity.entity_value}</h3>
                    <button 
                      onClick={() => setSelectedEntity(null)}
                      className="p-1 hover:bg-surface-2 rounded-full transition-colors text-muted-foreground hover:text-foreground"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <div className="p-4 bg-background">
                    <div className="text-xs uppercase tracking-wider text-muted-foreground font-semibold mb-1">Entity Type</div>
                    <div className="inline-block px-2.5 py-1 rounded-md text-xs font-medium bg-primary/20 text-primary border border-primary/30">
                      {selectedEntity.entity_type}
                    </div>
                  </div>
                  
                  <div className="flex-1 overflow-y-auto p-4 border-t border-border-default">
                    <h4 className="text-sm font-medium text-foreground mb-3">Mentioned in Documents ({selectedEntity.mentions.length})</h4>
                    
                    {isLoadingDetails ? (
                      <div className="flex justify-center p-4">
                        <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {selectedEntity.mentions.map((mention: any, idx: number) => (
                          <div key={idx} className="bg-surface-2 border border-border-default rounded-lg p-3 hover:border-primary/50 transition-colors group cursor-pointer">
                            <div className="flex items-start gap-2 mb-2">
                              <FileText className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                              <p className="text-sm font-medium text-foreground line-clamp-2 leading-snug group-hover:text-primary transition-colors">
                                {mention.filename}
                              </p>
                            </div>
                            <div className="flex items-center gap-3 text-xs text-muted-foreground">
                              <span className="bg-background px-2 py-0.5 rounded border border-border-default">Pg: {mention.page_number}</span>
                              <span className="truncate">Sec: {mention.section}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
