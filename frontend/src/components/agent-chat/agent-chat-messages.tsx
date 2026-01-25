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
        className={`max-w-[85%] whitespace-pre-wrap px-4 py-3 text-sm rounded-lg ${
          isUser
            ? "bg-eng-blue text-white"
            : "bg-eng-blue-05 text-eng-blue border border-eng-blue/[0.08]"
        }`}
      >
        <span className="font-sans">{message.content}</span>

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
      <div className="flex h-full flex-col items-center justify-center gap-4 p-4 md:p-6">
        <div className="w-12 h-12 rounded-full bg-alert-10 flex items-center justify-center">
          <Sparkles className="h-6 w-6 text-alert" />
        </div>
        <p className="text-center text-sm text-concrete font-sans">
          Como posso ajudar com seu marketing médico?
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => onSuggestionClick?.(s)}
              className="border border-eng-blue-10 bg-white px-3 py-1.5 rounded-full text-xs font-sans text-eng-blue transition-all duration-300 hover:bg-eng-blue-05 hover:border-eng-blue-30 hover:-translate-y-0.5"
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div ref={scrollRef} className="flex h-full flex-col gap-3 overflow-y-auto p-3 md:p-4">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {pendingToolCalls.length > 0 && (
        <div className="flex justify-start">
          <div className="flex flex-wrap gap-1 bg-eng-blue-05 border border-eng-blue/[0.08] rounded-lg px-3 py-2">
            {pendingToolCalls.map((tc) => (
              <AgentToolChip key={tc.id} toolCall={tc} />
            ))}
          </div>
        </div>
      )}

      {isStreaming && (
        <div className="flex justify-start">
          <span className="inline-flex items-center gap-1 px-3 py-2 text-sm text-concrete">
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-alert" />
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-alert [animation-delay:150ms]" />
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-alert [animation-delay:300ms]" />
          </span>
        </div>
      )}
    </div>
  );
}
