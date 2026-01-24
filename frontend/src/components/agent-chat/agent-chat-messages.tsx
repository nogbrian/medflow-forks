"use client";

import { useEffect, useRef } from "react";
import { Sparkles } from "lucide-react";
import { useAgentChatStore } from "@/lib/stores/agent-chat-store";
import { AgentToolChip } from "./agent-tool-chip";
import type { Message } from "@/types/agent-chat";

const SUGGESTIONS = [
  "Qual o resumo dos leads desta semana?",
  "Crie um post para Instagram",
  "Quais consultas estão agendadas hoje?",
  "Analise a taxa de conversão do funil",
];

interface MessageBubbleProps {
  message: Message;
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex w-full ${isUser ? "justify-end" : "justify-start"} animate-fade-in`}
    >
      <div
        className={`max-w-[85%] whitespace-pre-wrap px-3 py-2 text-sm ${
          isUser
            ? "bg-ink text-white"
            : "border border-graphite bg-paper text-ink"
        }`}
      >
        {message.content}

        {message.tool_calls && message.tool_calls.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {message.tool_calls.map((tc) => (
              <AgentToolChip key={tc.id} toolCall={tc} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface AgentChatMessagesProps {
  onSuggestionClick?: (suggestion: string) => void;
}

/**
 * Scrollable message container with auto-scroll-to-bottom.
 * Renders user/assistant bubbles and an empty state with suggestions.
 */
export function AgentChatMessages({ onSuggestionClick }: AgentChatMessagesProps) {
  const messages = useAgentChatStore((s) => s.messages);
  const isStreaming = useAgentChatStore((s) => s.isStreaming);
  const pendingToolCalls = useAgentChatStore((s) => s.pendingToolCalls);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages, pendingToolCalls]);

  if (messages.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 p-6">
        <Sparkles className="h-8 w-8 text-ink/30" />
        <p className="text-center text-sm text-ink/50">
          Como posso ajudar com seu marketing médico?
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => onSuggestionClick?.(s)}
              className="border border-graphite bg-white px-3 py-1.5 text-xs text-ink transition-colors hover:bg-paper"
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div ref={scrollRef} className="flex h-full flex-col gap-3 overflow-y-auto p-4">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {pendingToolCalls.length > 0 && (
        <div className="flex justify-start">
          <div className="flex flex-wrap gap-1 border border-graphite bg-paper px-3 py-2">
            {pendingToolCalls.map((tc) => (
              <AgentToolChip key={tc.id} toolCall={tc} />
            ))}
          </div>
        </div>
      )}

      {isStreaming && (
        <div className="flex justify-start">
          <span className="inline-flex items-center gap-1 px-3 py-2 text-sm text-ink/50">
            <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-ink/40" />
            <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-ink/40 [animation-delay:150ms]" />
            <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-ink/40 [animation-delay:300ms]" />
          </span>
        </div>
      )}
    </div>
  );
}
