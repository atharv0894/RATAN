"use client";

import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/lib/api";
import { Activity, Database, HardDrive, Server } from "lucide-react";

export default function SystemHealthCards() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["admin", "telemetry", "system"],
    queryFn: async () => {
      const res = await adminApi.telemetrySystem();
      return res.data.data;
    },
    refetchInterval: 10000, // 10 seconds auto-polling
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-32 bg-gray-800 rounded-xl border border-gray-700"></div>
        ))}
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="p-4 bg-red-900/20 border border-red-800 rounded-xl text-red-400">
        Failed to load system telemetry.
      </div>
    );
  }

  const cards = [
    {
      title: "CPU Usage",
      value: `${data.cpu_usage_percent}%`,
      icon: <Activity className="w-5 h-5 text-blue-400" />,
      color: "bg-blue-500/10 border-blue-500/20",
    },
    {
      title: "Memory Usage",
      value: `${data.memory_used_mb} MB`,
      subtitle: `of ${data.memory_total_mb} MB (${data.memory_percent}%)`,
      icon: <Server className="w-5 h-5 text-purple-400" />,
      color: "bg-purple-500/10 border-purple-500/20",
    },
    {
      title: "Vector DB Capacity",
      value: data.qdrant_vector_count.toLocaleString(),
      subtitle: "Total stored embeddings",
      icon: <HardDrive className="w-5 h-5 text-green-400" />,
      color: "bg-green-500/10 border-green-500/20",
    },
    {
      title: "Relational DB",
      value: data.database_status === "healthy" ? "Healthy" : "Degraded",
      icon: <Database className={`w-5 h-5 ${data.database_status === "healthy" ? "text-emerald-400" : "text-red-400"}`} />,
      color: data.database_status === "healthy" ? "bg-emerald-500/10 border-emerald-500/20" : "bg-red-500/10 border-red-500/20",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => (
        <div key={idx} className={`p-6 rounded-xl border backdrop-blur-sm ${card.color} flex flex-col justify-between`}>
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-gray-400 font-medium text-sm">{card.title}</h3>
            {card.icon}
          </div>
          <div>
            <div className="text-2xl font-bold text-white mb-1">{card.value}</div>
            {card.subtitle && (
              <div className="text-xs text-gray-500">{card.subtitle}</div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
