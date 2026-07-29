"use client";
import { useState, useRef, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { chatApi } from "@/lib/api";
import { Search, Sparkles, FileText, ChevronRight, Loader2, Info, Brain, Clock, X } from "lucide-react";

export default function GlobalSearchPage() {
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [recentSearches, setRecentSearches] = useState<string[]>([]);

  useEffect(() => {
    const saved = localStorage.getItem("ratan_recent_searches");
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved));
      } catch (e) {
        // ignore
      }
    }
  }, []);

  const saveRecentSearch = (q: string) => {
    if (!q.trim()) return;
    const updated = [q.trim(), ...recentSearches.filter(s => s.toLowerCase() !== q.trim().toLowerCase())].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem("ratan_recent_searches", JSON.stringify(updated));
  };

  const clearRecentSearches = () => {
    setRecentSearches([]);
    localStorage.removeItem("ratan_recent_searches");
  };

  const { data, isLoading, error } = useQuery({
    queryKey: ["semanticSearch", submittedQuery],
    queryFn: async () => {
      if (!submittedQuery) return null;
      const res = await chatApi.search(submittedQuery);
      return res.data.data;
    },
    enabled: !!submittedQuery,
    staleTime: 5 * 60 * 1000,
  });

  const handleSubmit = (e?: React.FormEvent, directQuery?: string) => {
    if (e) e.preventDefault();
    const finalQuery = directQuery || query;
    if (finalQuery.trim()) {
      setSubmittedQuery(finalQuery.trim());
      saveRecentSearch(finalQuery);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <Search className="w-6 h-6 text-primary" />
          Semantic Search
        </h1>
        <p className="text-muted-foreground text-sm">
          Search across all your indexed documents. Ask questions naturally or search by keywords.
        </p>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSubmit} className="relative group">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-muted-foreground group-focus-within:text-primary transition-colors" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question or search for technical procedures..."
          className="w-full bg-surface-2 border border-border-default rounded-xl py-4 pl-12 pr-14 text-foreground placeholder-muted-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary shadow-sm transition-all"
        />
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="absolute inset-y-2 right-2 px-3 bg-primary hover:bg-primary-hover disabled:bg-muted disabled:cursor-not-allowed text-white rounded-lg flex items-center justify-center transition-colors"
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ChevronRight className="w-5 h-5" />}
        </button>
      </form>

      {/* Search Results */}
      {error ? (
        <div className="card-premium p-6 border-danger/50 text-center">
          <p className="text-danger">Failed to execute search. Please try again.</p>
        </div>
      ) : isLoading ? (
        <div className="flex flex-col items-center justify-center py-20 space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-muted-foreground animate-pulse">Scanning knowledge base...</p>
        </div>
      ) : data ? (
        <div className="space-y-6 animate-fade-in">
          {/* AI Overview */}
          <div className="card-premium border-primary/20 bg-primary/5 p-6 space-y-4 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10 pointer-events-none">
              <Sparkles className="w-24 h-24 text-primary" />
            </div>
            
            <div className="flex items-center gap-2 text-primary font-medium">
              <Sparkles className="w-5 h-5" />
              <h3>AI Overview</h3>
            </div>
            
            <div className="text-foreground leading-relaxed">
              {data.answer}
            </div>

            <div className="flex items-center gap-4 text-xs pt-4 border-t border-border-default/50">
              <span className="flex items-center gap-1 text-muted-foreground">
                <Info className="w-3.5 h-3.5" />
                Confidence: {(data.confidence_score * 100).toFixed(1)}%
              </span>
              <span className="flex items-center gap-1 text-muted-foreground">
                <Brain className="w-3.5 h-3.5" />
                Model: {data.provider}
              </span>
            </div>
          </div>

          {/* Citations as Search Results */}
          {data.citations && data.citations.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-foreground-2 uppercase tracking-wider">Sources & Citations</h3>
              <div className="grid gap-4">
                {data.citations.map((cite: any, i: number) => (
                  <div key={i} className="card-premium p-4 flex flex-col gap-2 hover:border-primary/50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-surface flex items-center justify-center">
                          <FileText className="w-4 h-4 text-accent" />
                        </div>
                        <div>
                          <h4 className="font-medium text-foreground">{cite.document_name}</h4>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span>Version {cite.version}</span>
                            {cite.page && <span>• Page {cite.page}</span>}
                            {cite.section && <span>• Section: {cite.section}</span>}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Follow-up Questions */}
          {data.follow_up_questions && data.follow_up_questions.length > 0 && (
            <div className="pt-4 border-t border-border-default space-y-3">
              <h3 className="text-sm font-medium text-foreground-2">Related searches</h3>
              <div className="flex flex-wrap gap-2">
                {data.follow_up_questions.map((q: string, i: number) => (
                  <button
                    key={i}
                    onClick={() => {
                      setQuery(q);
                      setSubmittedQuery(q);
                    }}
                    className="px-3 py-1.5 text-xs rounded-full bg-surface-2 border border-border-default hover:bg-primary/20 hover:border-primary/50 text-foreground transition-colors text-left"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : submittedQuery ? (
        <div className="card-premium p-12 text-center text-muted-foreground flex flex-col items-center gap-3">
          <Search className="w-8 h-8 opacity-50" />
          <p>No results found for "<span className="text-foreground">{submittedQuery}</span>". Try a different keyword.</p>
        </div>
      ) : (
        <div className="space-y-8 animate-fade-in">
          {recentSearches.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-foreground-2 uppercase tracking-wider flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  Recent Searches
                </h3>
                <button 
                  onClick={clearRecentSearches}
                  className="text-xs text-muted-foreground hover:text-danger transition-colors"
                >
                  Clear all
                </button>
              </div>
              <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
                {recentSearches.map((term, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setQuery(term);
                      handleSubmit(undefined, term);
                    }}
                    className="flex items-center gap-3 p-3 rounded-xl bg-surface-2 hover:bg-primary/10 border border-border-default hover:border-primary/30 text-left transition-all group"
                  >
                    <Search className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors shrink-0" />
                    <span className="text-sm text-foreground truncate flex-1">{term}</span>
                    <ChevronRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-all shrink-0 -translate-x-2 group-hover:translate-x-0" />
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="card-premium p-12 flex flex-col items-center justify-center text-center space-y-4 border-dashed bg-surface/50">
            <div className="w-16 h-16 rounded-2xl bg-surface-2 border border-border-default flex items-center justify-center">
              <Search className="w-8 h-8 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="font-medium text-foreground text-lg">Global Semantic Search</h3>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                Enter a search query above to instantly retrieve exact answers and citations from all indexed industrial manuals and procedures.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
