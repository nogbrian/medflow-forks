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
 * Right-side slide-in panel for agent chat - Intelligent Flow Design
 * Controlled by isOpen from the Zustand store.
 * w-[420px] on desktop, full-width on mobile.
 * Glassmorphism with smooth transitions.
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
      {/* Panel — bottom sheet on mobile, side panel on desktop */}
      <aside
        className={`fixed z-sidebar flex flex-col bg-white/95 backdrop-blur-xl transition-transform duration-300 ease-out ${
          // Mobile: bottom sheet
          "inset-x-0 bottom-0 h-[85vh] rounded-t-xl border-t border-eng-blue/[0.08] shadow-2xl"
        } ${
          // Desktop: right side panel
          "md:inset-y-0 md:right-0 md:left-auto md:h-auto md:w-[420px] md:rounded-none md:border-l md:border-t-0 md:shadow-xl"
        } ${
          isOpen
            ? "translate-y-0 md:translate-x-0 md:translate-y-0"
            : "translate-y-full md:translate-x-full md:translate-y-0"
        }`}
        aria-label="Agent Chat"
        role="complementary"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-eng-blue/[0.06] px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-gradient-to-br from-eng-blue to-[#1A4A55] flex items-center justify-center">
              <Bot className="h-4 w-4 text-white" />
            </div>
            <span className="font-display text-sm font-semibold text-eng-blue tracking-tight">
              MedFlow Agent
            </span>
          </div>
          <button
            onClick={close}
            className="flex h-8 w-8 items-center justify-center rounded-md text-concrete hover:text-eng-blue hover:bg-eng-blue-05 transition-all duration-300"
            aria-label="Fechar chat"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Context chip */}
        <div className="border-b border-eng-blue/[0.04] px-4 py-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-alert-05 border border-alert-10 font-mono text-xs text-alert">
            <span className="h-1.5 w-1.5 rounded-full bg-alert animate-pulse" />
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
