"use client";

import { useCallback, useMemo } from "react";
import { usePathname } from "next/navigation";
import { useAgentChatStore } from "@/lib/stores/agent-chat-store";
import { getStoredToken } from "@/lib/auth";
import type { StreamChunk } from "@/types/agent-chat";

export interface ChatContext {
  pathname: string;
  activeTenant: string | null;
  activeContext: string | null;
}

/**
 * Hook for agent chat with SSE streaming.
 * Wraps the Zustand store and handles the streaming POST to /api/chat/stream.
 */
export function useAgentChat() {
  const pathname = usePathname();

  const messages = useAgentChatStore((s) => s.messages);
  const isStreaming = useAgentChatStore((s) => s.isStreaming);
  const isOpen = useAgentChatStore((s) => s.isOpen);
  const sessionId = useAgentChatStore((s) => s.sessionId);
  const pendingToolCalls = useAgentChatStore((s) => s.pendingToolCalls);
  const toggle = useAgentChatStore((s) => s.toggle);
  const clearMessages = useAgentChatStore((s) => s.clearMessages);

  const currentContext: ChatContext = useMemo(
    () => ({
      pathname,
      activeTenant: null,
      activeContext: null,
    }),
    [pathname]
  );

  const sendMessage = useCallback(
    async (content: string) => {
      const trimmed = content.trim();
      if (!trimmed || useAgentChatStore.getState().isStreaming) return;

      const store = useAgentChatStore.getState();

      // Add user message to the store
      store.sendMessage(trimmed);
      store.setStreaming(true);

      const token = getStoredToken();

      try {
        const response = await fetch("/api/chat/stream", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            message: trimmed,
            session_id: store.sessionId,
            context: currentContext,
            stream: true,
          }),
        });

        if (!response.ok) {
          const errorBody = await response.json().catch(() => ({}));
          throw new Error(
            errorBody.detail || `Request failed with status ${response.status}`
          );
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error("Response body is not readable");
        }

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // Process SSE lines from buffer
          const lines = buffer.split("\n");
          // Keep incomplete last line in buffer
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            const trimmedLine = line.trim();
            if (!trimmedLine || !trimmedLine.startsWith("data: ")) continue;

            const data = trimmedLine.slice(6); // Remove "data: " prefix
            if (data === "[DONE]") {
              useAgentChatStore.getState().setStreaming(false);
              break;
            }

            try {
              const chunk: StreamChunk = JSON.parse(data);
              useAgentChatStore.getState().appendChunk(chunk);

              // Capture session_id from message_start if present
              if (
                chunk.type === "message_start" &&
                chunk.message_id &&
                !useAgentChatStore.getState().sessionId
              ) {
                useAgentChatStore.getState().setSessionId(chunk.message_id);
              }
            } catch {
              // Skip malformed JSON chunks
            }
          }
        }

        // Ensure streaming is off after the stream ends
        useAgentChatStore.getState().setStreaming(false);
      } catch (error) {
        useAgentChatStore.getState().setStreaming(false);

        // Add error message to chat
        const errorMessage =
          error instanceof Error ? error.message : "An unexpected error occurred";
        useAgentChatStore.getState().appendChunk({
          type: "message_start",
          message_id: crypto.randomUUID(),
        });
        useAgentChatStore.getState().appendChunk({
          type: "text_delta",
          content: `⚠️ Error: ${errorMessage}`,
        });
        useAgentChatStore.getState().appendChunk({
          type: "message_end",
        });
      }
    },
    [currentContext]
  );

  return {
    messages,
    isStreaming,
    isOpen,
    toggle,
    sendMessage,
    clearMessages,
    currentContext,
    sessionId,
    pendingToolCalls,
  };
}
