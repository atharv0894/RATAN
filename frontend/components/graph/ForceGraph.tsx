"use client";

import React, { useRef, useEffect, useState, useCallback } from "react";
import ForceGraph2D from "react-force-graph-2d";

interface GraphNode {
  id: string;
  label: string;
  group: number;
  val: number;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number;
  fy?: number;
}

interface GraphData {
  nodes: GraphNode[];
  edges: { id: string; source: string; target: string; relationship: string }[];
}

const GROUP_COLORS: Record<number, string> = {
  1: "#60a5fa", // Document - Bright Blue
  2: "#fbbf24", // Role - Amber
  3: "#34d399", // Equipment - Emerald
  4: "#c084fc", // Standard - Purple
  5: "#f87171", // Safety - Red
  6: "#22d3ee", // Tool - Cyan
  7: "#fb7185", // Parameter - Rose
  8: "#a78bfa", // Organization - Violet
  9: "#f472b6", // Concept - Pink
};

export default function ForceGraph({
  data,
  onNodeClick,
}: {
  data: GraphData;
  onNodeClick?: (node: any) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };
    updateDimensions();
    const observer = new ResizeObserver(updateDimensions);
    if (containerRef.current) observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Inject d3 forces after mount for proper repulsion
  const handleEngineStop = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400, 60);
    }
  }, []);

  useEffect(() => {
    if (graphRef.current) {
      // Strong charge repulsion so nodes spread out
      graphRef.current.d3Force("charge")?.strength(-400);
      // Longer link distance
      graphRef.current.d3Force("link")?.distance(120).strength(0.3);
      // Gentle centering
      graphRef.current.d3Force("center")?.strength(0.05);
    }
  });

  const drawNode = useCallback(
    (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      if (
        node.x === undefined || node.y === undefined ||
        Number.isNaN(node.x) || Number.isNaN(node.y) ||
        !Number.isFinite(node.x) || !Number.isFinite(node.y) ||
        node.val === undefined || Number.isNaN(node.val) || node.val < 0
      ) return;

      const label = node.label as string;
      const color = GROUP_COLORS[node.group] || "#94a3b8";
      const isDoc = node.group === 1;
      const isHovered = hoveredNode === node.id;

      const baseRadius = isDoc
        ? Math.sqrt(node.val) * 3 + 8
        : Math.sqrt(node.val) * 2.2 + 4;
      const radius = isHovered ? baseRadius * 1.3 : baseRadius;

      // --- Outer glow ring ---
      const glowRadius = radius + (isHovered ? 12 : 8);
      const glowGrad = ctx.createRadialGradient(
        node.x, node.y, radius * 0.5,
        node.x, node.y, glowRadius
      );
      glowGrad.addColorStop(0, color + "66");
      glowGrad.addColorStop(1, color + "00");
      ctx.beginPath();
      ctx.arc(node.x, node.y, glowRadius, 0, 2 * Math.PI);
      ctx.fillStyle = glowGrad;
      ctx.fill();

      // --- Inner node with gradient ---
      const grad = ctx.createRadialGradient(
        node.x - radius * 0.3, node.y - radius * 0.3, 0,
        node.x, node.y, radius
      );
      grad.addColorStop(0, color + "ff");
      grad.addColorStop(0.6, color + "cc");
      grad.addColorStop(1, color + "88");

      ctx.beginPath();
      ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
      ctx.fillStyle = grad;
      ctx.shadowBlur = isHovered ? 30 : 18;
      ctx.shadowColor = color;
      ctx.fill();
      ctx.shadowBlur = 0;

      // --- Stroke ring ---
      ctx.strokeStyle = isHovered ? "#ffffff" : color + "aa";
      ctx.lineWidth = isHovered ? 2 : 1;
      ctx.stroke();

      // --- Label (only show when zoomed in enough or for document nodes) ---
      const showLabel = globalScale > 0.6 || isDoc;
      if (!showLabel) return;

      const fontSize = Math.min(Math.max(11 / globalScale, 2.5), 14);
      ctx.font = `${isDoc ? "700" : "500"} ${fontSize}px Inter, system-ui, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";

      const textWidth = ctx.measureText(label).width;
      const labelY = node.y + radius + 4;
      const padX = 5;
      const padY = 3;

      // pill background
      ctx.fillStyle = "rgba(5, 10, 24, 0.82)";
      const bx = node.x - textWidth / 2 - padX;
      const by = labelY;
      const bw = textWidth + padX * 2;
      const bh = fontSize + padY * 2;
      const br = bh / 2;
      ctx.beginPath();
      ctx.moveTo(bx + br, by);
      ctx.lineTo(bx + bw - br, by);
      ctx.quadraticCurveTo(bx + bw, by, bx + bw, by + br);
      ctx.lineTo(bx + bw, by + bh - br);
      ctx.quadraticCurveTo(bx + bw, by + bh, bx + bw - br, by + bh);
      ctx.lineTo(bx + br, by + bh);
      ctx.quadraticCurveTo(bx, by + bh, bx, by + bh - br);
      ctx.lineTo(bx, by + br);
      ctx.quadraticCurveTo(bx, by, bx + br, by);
      ctx.closePath();
      ctx.fill();

      ctx.fillStyle = isDoc ? "#ffffff" : color;
      ctx.fillText(label, node.x, labelY + padY);
    },
    [hoveredNode]
  );

  return (
    <div
      ref={containerRef}
      className="w-full h-full min-h-[600px] rounded-xl overflow-hidden border border-border-default relative"
      style={{ background: "radial-gradient(ellipse at center, #0d1a2d 0%, #050a18 100%)" }}
    >
      {/* Subtle grid background */}
      <svg
        className="absolute inset-0 w-full h-full opacity-[0.04] pointer-events-none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#60a5fa" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      <ForceGraph2D
        ref={graphRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={{ nodes: data.nodes, links: data.edges || [] }}
        nodeLabel={() => ""}
        onNodeClick={onNodeClick}
        onNodeHover={(node: any) => setHoveredNode(node ? node.id : null)}
        // Edge styling
        linkColor={(link: any) => {
          const srcColor = GROUP_COLORS[(link.source as GraphNode)?.group || 1];
          return srcColor + "33";
        }}
        linkWidth={1.2}
        linkDirectionalParticles={2}
        linkDirectionalParticleWidth={2}
        linkDirectionalParticleSpeed={0.005}
        linkDirectionalParticleColor={(link: any) => {
          const srcColor = GROUP_COLORS[(link.source as GraphNode)?.group || 1];
          return srcColor + "cc";
        }}
        // Node rendering
        nodeCanvasObject={drawNode}
        nodeCanvasObjectMode={() => "replace"}
        // Background
        backgroundColor="transparent"
        onEngineStop={handleEngineStop}
        // Interaction
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        minZoom={0.2}
        maxZoom={8}
      />
    </div>
  );
}
