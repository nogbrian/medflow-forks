"use client";

import { Sparkles, X } from "lucide-react";
import { useAuth } from "@/components/auth/auth-provider";
import { useAgentChatStore } from "@/lib/stores/agent-chat-store";

/**
 * Floating action button for the agent chat - Intelligent Flow Design
 * Only visible to superusers. Toggles the chat panel open/closed.
 */
export function AgentChatFab() {
  const { user } = useAuth();
  const isOpen = useAgentChatStore((s) => s.isOpen);
  const toggle = useAgentChatStore((s) => s.toggle);
  const pendingToolCalls = useAgentChatStore((s) => s.pendingToolCalls);
  const messages = useAgentChatStore((s) => s.messages);

  if (user?.role !== "superuser") return null;

  const hasNotification = pendingToolCalls.length > 0 || (messages.length > 0 && !isOpen);

  return (
    <button
      onClick={toggle}
      aria-label={isOpen ? "Fechar chat" : "Abrir chat"}
      className="fixed bottom-4 right-4 z-50 flex h-12 w-12 items-center justify-center rounded-full bg-alert text-white shadow-lg shadow-glow-orange transition-all duration-300 ease-out hover:scale-105 hover:-translate-y-0.5 active:scale-95 md:bottom-6 md:right-6 md:h-14 md:w-14"
    >
      <span
        className={`transition-transform duration-300 ${isOpen ? "rotate-90" : "rotate-0"}`}
      >
        {isOpen ? <X className="h-5 w-5 md:h-6 md:w-6" /> : <Sparkles className="h-5 w-5 md:h-6 md:w-6" />}
      </span>

      {hasNotification && !isOpen && (
        <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-eng-blue text-[10px] font-bold text-white border-2 border-white">
          {pendingToolCalls.length > 0 ? pendingToolCalls.length : ""}
        </span>
      )}
    </button>
  );
}
