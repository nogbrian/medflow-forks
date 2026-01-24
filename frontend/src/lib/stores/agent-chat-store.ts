import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Message, StreamChunk, ToolCall, ToolCallStatus } from "@/types/agent-chat";

interface AgentChatState {
  isOpen: boolean;
  messages: Message[];
  isStreaming: boolean;
  pendingToolCalls: ToolCall[];
  sessionId: string | null;
}

interface AgentChatActions {
  toggle: () => void;
  open: () => void;
  close: () => void;
  sendMessage: (content: string) => void;
  appendChunk: (chunk: StreamChunk) => void;
  addToolCall: (toolCall: ToolCall) => void;
  updateToolCall: (id: string, updates: Partial<Pick<ToolCall, "status" | "result" | "error" | "completed_at">>) => void;
  clearMessages: () => void;
  setStreaming: (streaming: boolean) => void;
  setSessionId: (id: string | null) => void;
}

type AgentChatStore = AgentChatState & AgentChatActions;

export const useAgentChatStore = create<AgentChatStore>()(
  persist(
    (set, get) => ({
      // State
      isOpen: false,
      messages: [],
      isStreaming: false,
      pendingToolCalls: [],
      sessionId: null,

      // Actions
      toggle: () => set((state) => ({ isOpen: !state.isOpen })),
      open: () => set({ isOpen: true }),
      close: () => set({ isOpen: false }),

      sendMessage: (content: string) => {
        const message: Message = {
          id: crypto.randomUUID(),
          role: "user",
          content,
          created_at: new Date().toISOString(),
        };
        set((state) => ({ messages: [...state.messages, message] }));
      },

      appendChunk: (chunk: StreamChunk) => {
        const { type, message_id, content, tool_call } = chunk;

        set((state) => {
          switch (type) {
            case "message_start": {
              const newMessage: Message = {
                id: message_id ?? crypto.randomUUID(),
                role: "assistant",
                content: "",
                created_at: new Date().toISOString(),
              };
              return { messages: [...state.messages, newMessage], isStreaming: true };
            }

            case "text_delta": {
              if (!content) return state;
              const messages = [...state.messages];
              const last = messages[messages.length - 1];
              if (last && last.role === "assistant") {
                messages[messages.length - 1] = {
                  ...last,
                  content: last.content + content,
                };
              }
              return { messages };
            }

            case "tool_call_start": {
              if (!tool_call?.id || !tool_call?.name) return state;
              const newToolCall: ToolCall = {
                id: tool_call.id,
                name: tool_call.name,
                arguments: tool_call.arguments ?? {},
                status: "running",
                started_at: new Date().toISOString(),
              };
              return { pendingToolCalls: [...state.pendingToolCalls, newToolCall] };
            }

            case "tool_call_end": {
              if (!tool_call?.id) return state;
              const pendingToolCalls = state.pendingToolCalls.filter(
                (tc) => tc.id !== tool_call.id
              );
              const completedCall: ToolCall = {
                ...(state.pendingToolCalls.find((tc) => tc.id === tool_call.id) ?? {
                  id: tool_call.id,
                  name: tool_call.name ?? "unknown",
                  arguments: {},
                  status: "completed" as ToolCallStatus,
                }),
                status: tool_call.error ? "failed" : "completed",
                result: tool_call.result,
                error: tool_call.error,
                completed_at: new Date().toISOString(),
              };

              // Attach completed tool call to the last assistant message
              const messages = [...state.messages];
              const last = messages[messages.length - 1];
              if (last && last.role === "assistant") {
                messages[messages.length - 1] = {
                  ...last,
                  tool_calls: [...(last.tool_calls ?? []), completedCall],
                };
              }
              return { messages, pendingToolCalls };
            }

            case "message_end": {
              return { isStreaming: false };
            }

            case "error": {
              return { isStreaming: false };
            }

            default:
              return state;
          }
        });
      },

      addToolCall: (toolCall: ToolCall) => {
        set((state) => ({
          pendingToolCalls: [...state.pendingToolCalls, toolCall],
        }));
      },

      updateToolCall: (id, updates) => {
        set((state) => ({
          pendingToolCalls: state.pendingToolCalls.map((tc) =>
            tc.id === id ? { ...tc, ...updates } : tc
          ),
        }));
      },

      clearMessages: () => set({ messages: [], pendingToolCalls: [], sessionId: null }),

      setStreaming: (streaming: boolean) => set({ isStreaming: streaming }),

      setSessionId: (id: string | null) => set({ sessionId: id }),
    }),
    {
      name: "medflow-agent-chat",
      partialize: (state) => ({
        messages: state.messages,
        sessionId: state.sessionId,
      }),
    }
  )
);
