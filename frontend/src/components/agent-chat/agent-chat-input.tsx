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
 * Auto-resizing chat input with Enter-to-send.
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
    <div className="flex items-end gap-2 border-t border-graphite bg-white p-3">
      <textarea
        ref={textareaRef}
        rows={MIN_ROWS}
        placeholder="Digite sua mensagem..."
        disabled={isStreaming}
        onInput={resize}
        onKeyDown={handleKeyDown}
        className="flex-1 resize-none border border-graphite bg-paper px-3 py-2 text-sm text-ink placeholder:text-steel outline-none focus:border-ink disabled:opacity-50"
        style={{ lineHeight: `${LINE_HEIGHT}px`, maxHeight: `${LINE_HEIGHT * MAX_ROWS}px` }}
      />
      <button
        onClick={handleSend}
        disabled={isStreaming}
        className="flex h-9 w-9 shrink-0 items-center justify-center border border-graphite bg-ink text-white transition-colors hover:bg-accent-orange disabled:opacity-50"
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
