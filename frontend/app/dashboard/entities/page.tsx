"use client";
import { useState } from "react";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { useQuery } from "@tanstack/react-query";
import { entitiesApi } from "@/lib/api";
import { Search, Tag, FileText, X, Loader2, ArrowRight } from "lucide-react";

interface Entity {
  id: string;
  type: string;
  value: string;
}

interface EntityMention {
  document_id: string;
  filename: string;
  page_number: number;
  section: string;
}

interface EntityDetail {
  entity_value: string;
  entity_type: string;
  mentions: EntityMention[];
}

export default function EntitiesPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);

  const { data: entitiesData, isLoading } = useQuery({
    queryKey: ["entities-list"],
    queryFn: () => entitiesApi.list().then((r) => r.data.data as Entity[]),
  });

  const { data: entityDetails, isLoading: isDetailsLoading } = useQuery({
    queryKey: ["entity-details", selectedEntity?.value],
    queryFn: () => entitiesApi.getDetails(selectedEntity!.value).then((r) => r.data.data as EntityDetail),
    enabled: !!selectedEntity,
  });

  const entities = entitiesData || [];
  
  const types = ["ALL", ...Array.from(new Set(entities.map(e => e.type)))].sort();

  const filteredEntities = entities.filter(e => {
    const matchesSearch = e.value.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = selectedType === "ALL" || e.type === selectedType;
    return matchesSearch && matchesType;
  });

  const getTypeColor = (type: string) => {
    const map: Record<string, string> = {
      EQUIPMENT: "bg-blue-500/10 text-blue-400 border-blue-500/20",
      ROLE: "bg-purple-500/10 text-purple-400 border-purple-500/20",
      PARAMETER: "bg-green-500/10 text-green-400 border-green-500/20",
      SAFETY: "bg-red-500/10 text-red-400 border-red-500/20",
      TOOL: "bg-orange-500/10 text-orange-400 border-orange-500/20",
    };
    return map[type.toUpperCase()] || "bg-gray-500/10 text-gray-400 border-gray-500/20";
  };

  return (
    <DashboardLayout title="Named Entities" subtitle="Extracted concepts and components from your knowledge base">
      <div className="flex h-[calc(100vh-140px)] gap-6 animate-fade-in">
        
        {/* Main List */}
        <div className={`flex-1 flex flex-col min-h-0 card-premium transition-all duration-300 ${selectedEntity ? 'w-2/3 hidden lg:flex' : 'w-full'}`}>
          <div className="p-4 border-b border-border-default flex flex-col sm:flex-row gap-4 items-center justify-between">
            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search entities..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-background border border-border-default rounded-lg pl-9 pr-4 py-2 text-sm text-foreground focus:outline-none focus:border-primary transition-colors"
              />
            </div>
            
            <div className="flex gap-2 w-full sm:w-auto overflow-x-auto pb-2 sm:pb-0 scrollbar-none">
              {types.map(type => (
                <button
                  key={type}
                  onClick={() => setSelectedType(type)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md whitespace-nowrap transition-colors ${
                    selectedType === type 
                      ? 'bg-primary text-white' 
                      : 'bg-background border border-border-default text-muted-foreground hover:bg-border-default'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {isLoading ? (
              <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
                <Loader2 className="w-8 h-8 animate-spin mb-4 text-primary" />
                <p>Extracting entities from knowledge graph...</p>
              </div>
            ) : filteredEntities.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
                <Tag className="w-12 h-12 mb-4 opacity-20" />
                <p>No entities found matching your criteria.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                {filteredEntities.map((entity, i) => (
                  <button
                    key={`${entity.id}-${i}`}
                    onClick={() => setSelectedEntity(entity)}
                    className={`flex flex-col text-left p-4 rounded-xl border transition-all ${
                      selectedEntity?.value === entity.value 
                        ? 'bg-primary/10 border-primary shadow-[0_0_15px_rgba(37,99,235,0.15)]' 
                        : 'bg-background border-border-default hover:border-primary/50 hover:bg-border-default/50'
                    }`}
                  >
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border uppercase tracking-wider mb-2 ${getTypeColor(entity.type)}`}>
                      {entity.type}
                    </span>
                    <span className="text-sm font-medium text-white truncate w-full" title={entity.value}>
                      {entity.value}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Details Panel */}
        {selectedEntity && (
          <div className="w-full lg:w-1/3 flex flex-col card-premium animate-slide-in-right overflow-hidden">
            <div className="p-4 border-b border-border-default flex items-start justify-between bg-background">
              <div>
                <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-bold border uppercase tracking-wider mb-2 ${getTypeColor(selectedEntity.type)}`}>
                  {selectedEntity.type}
                </span>
                <h2 className="text-xl font-bold text-white leading-tight break-words pr-4">
                  {selectedEntity.value}
                </h2>
              </div>
              <button 
                onClick={() => setSelectedEntity(null)}
                className="p-1.5 hover:bg-border-default rounded-md text-muted-foreground transition-colors shrink-0"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 bg-background">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Document Mentions
              </h3>
              
              {isDetailsLoading ? (
                <div className="py-8 flex justify-center">
                  <Loader2 className="w-6 h-6 animate-spin text-primary" />
                </div>
              ) : entityDetails?.mentions?.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">No specific mentions found.</p>
              ) : (
                <div className="space-y-3">
                  {entityDetails?.mentions.map((mention, i) => (
                    <div key={i} className="p-3 bg-background border border-border-default rounded-lg hover:border-primary/30 transition-colors group">
                      <p className="text-sm font-medium text-white truncate mb-1 flex items-center justify-between" title={mention.filename}>
                        {mention.filename}
                        <ArrowRight className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                      </p>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>Page {mention.page_number}</span>
                        <span className="truncate max-w-30">{mention.section !== 'General' ? mention.section : 'Body'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
        
      </div>
    </DashboardLayout>
  );
}
