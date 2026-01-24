"use client";

import { useEffect, useCallback } from "react";
import { Bot, X } from "lucide-react";
import { usePathname } from "next/navigation";
import { useAgentChatStore } from "@/lib/stores/agent-chat-store";
import { useAgentChat } from "@/hooks/use-agent-chat";
import { AgentChatMessages } from "./agent-chat-messages";
import { AgentChatInput } from "./agent-chat-input";

const PATHNAME_LABELS: Record<string, string> = {
  "/": "Dashboard",
  "/inbox": "Atendimento",
  "/crm": "CRM",
  "/agenda": "Agenda",
  "/creative": "Creative Studio",
  "/analytics": "Analytics",
};

function getContextLabel(pathname: string): string {
  return PATHNAME_LABELS[pathname] ?? (pathname.replace("/", "").replace(/-/g, " ") || "Dashboard");
}

/**
 * Right-side slide-in panel for agent chat.
 * Controlled by isOpen from the Zustand store.
 * w-[420px] on desktop, full-width on mobile.
 * No dark overlay - content remains interactive.
 */
export function AgentChatPanel() {
  const isOpen = useAgentChatStore((s) => s.isOpen);
  const close = useAgentChatStore((s) => s.close);
  const pathname = usePathname();
  const { sendMessage } = useAgentChat();

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [isOpen, close]);

  const handleSuggestionClick = useCallback(
    (suggestion: string) => {
      sendMessage(suggestion);
    },
    [sendMessage]
  );

  return (
    <>
      {/* Panel */}
      <aside
        className={`fixed inset-y-0 right-0 z-sidebar flex w-full flex-col border-l border-graphite bg-white transition-transform duration-150 ease-[cubic-bezier(0.4,0,0.2,1)] sm:w-[420px] ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
        aria-label="Agent Chat"
        role="complementary"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-graphite px-4 py-3">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-ink" />
            <span className="font-sans text-sm font-semibold uppercase tracking-wide text-ink">
              MedFlow Agent
            </span>
          </div>
          <button
            onClick={close}
            className="flex h-7 w-7 items-center justify-center text-ink/60 transition-colors hover:text-ink"
            aria-label="Fechar chat"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Context chip */}
        <div className="border-b border-graphite/30 px-4 py-2">
          <span className="inline-flex items-center gap-1.5 border border-graphite bg-paper px-2 py-0.5 font-mono text-label-sm uppercase text-steel">
            <span className="h-1.5 w-1.5 rounded-full bg-accent-orange" />
            {getContextLabel(pathname)}
          </span>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-hidden">
          <AgentChatMessages onSuggestionClick={handleSuggestionClick} />
        </div>

        {/* Input */}
        <AgentChatInput onSend={sendMessage} />
      </aside>
    </>
  );
}
