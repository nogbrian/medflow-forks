"use client";

import { CheckCircle, Loader2, XCircle } from "lucide-react";
import type { ToolCall } from "@/types/agent-chat";

interface AgentToolChipProps {
  toolCall: ToolCall;
}

const statusConfig = {
  pending: {
    icon: Loader2,
    className: "border-graphite text-ink animate-spin",
    label: "Aguardando",
  },
  running: {
    icon: Loader2,
    className: "border-graphite text-ink animate-spin",
    label: "Executando",
  },
  completed: {
    icon: CheckCircle,
    className: "border-green-600 text-green-600",
    label: "Concluído",
  },
  failed: {
    icon: XCircle,
    className: "border-red-600 text-red-600",
    label: "Erro",
  },
} as const;

/**
 * Badge showing tool execution status with icon.
 * Renders inline within assistant messages.
 */
export function AgentToolChip({ toolCall }: AgentToolChipProps) {
  const config = statusConfig[toolCall.status];
  const Icon = config.icon;

  return (
    <span className="inline-flex animate-fade-in items-center gap-1.5 rounded-none border border-graphite bg-paper px-2 py-0.5 font-mono text-xs">
      <Icon className={`h-3 w-3 ${config.className}`} />
      <span className="text-ink/80">{toolCall.name}</span>
      {toolCall.error && (
        <span className="max-w-[120px] truncate text-red-600">
          {toolCall.error}
        </span>
      )}
    </span>
  );
}
