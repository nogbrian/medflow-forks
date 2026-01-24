"use client";

import { Sparkles, X } from "lucide-react";
import { useAuth } from "@/components/auth/auth-provider";
import { useAgentChatStore } from "@/lib/stores/agent-chat-store";

/**
 * Floating action button for the agent chat.
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
      className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-ink text-white shadow-[4px_4px_0px_0px_#F24E1E] transition-transform duration-150 ease-out hover:scale-105 active:translate-x-0.5 active:translate-y-0.5 active:shadow-[2px_2px_0px_0px_#F24E1E]"
    >
      <span
        className={`transition-transform duration-200 ${isOpen ? "rotate-90" : "rotate-0"}`}
      >
        {isOpen ? <X className="h-6 w-6" /> : <Sparkles className="h-6 w-6" />}
      </span>

      {hasNotification && !isOpen && (
        <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-600 text-[10px] font-bold text-white">
          {pendingToolCalls.length > 0 ? pendingToolCalls.length : ""}
        </span>
      )}
    </button>
  );
}
