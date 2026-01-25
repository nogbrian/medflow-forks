"use client";

import { useCallback, useRef, KeyboardEvent, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import { useAgentChatStore } from "@/lib/stores/agent-chat-store";

interface AgentChatInputProps {
  onSend: (message: string) => void;
}

const MIN_ROWS = 1;
const MAX_ROWS = 4;
const LINE_HEIGHT = 20; // px per line

/**
 * Auto-resizing chat input with Enter-to-send - Intelligent Flow Design
 * Disables input and shows spinner while streaming.
 */
export function AgentChatInput({ onSend }: AgentChatInputProps) {
  const isStreaming = useAgentChatStore((s) => s.isStreaming);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const resize = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    const maxHeight = LINE_HEIGHT * MAX_ROWS;
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`;
  }, []);

  useEffect(() => {
    resize();
  }, [resize]);

  const handleSend = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    const value = el.value.trim();
    if (!value || isStreaming) return;

    onSend(value);
    el.value = "";
    resize();
    el.focus();
  }, [onSend, isStreaming, resize]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  return (
    <div className="flex items-end gap-2 border-t border-eng-blue/[0.06] bg-white/80 backdrop-blur-sm p-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
      <textarea
        ref={textareaRef}
        rows={MIN_ROWS}
        placeholder="Digite sua mensagem..."
        disabled={isStreaming}
        onInput={resize}
        onKeyDown={handleKeyDown}
        className="flex-1 resize-none border-2 border-eng-blue-10 bg-white/80 rounded-md px-4 py-2.5 text-sm font-sans text-eng-blue placeholder:text-concrete/50 outline-none focus:border-alert focus:ring-4 focus:ring-alert-10 disabled:opacity-50 transition-all duration-300"
        style={{ lineHeight: `${LINE_HEIGHT}px`, maxHeight: `${LINE_HEIGHT * MAX_ROWS}px` }}
      />
      <button
        onClick={handleSend}
        disabled={isStreaming}
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-alert text-white shadow-md shadow-glow-orange transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5 disabled:opacity-50 disabled:transform-none"
        aria-label="Enviar mensagem"
      >
        {isStreaming ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
      </button>
    </div>
  );
}
