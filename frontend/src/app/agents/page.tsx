"use client";

import { useState, useRef, useCallback } from "react";
import { Shell } from "@/components/layout/shell";
import {
  Bot,
  Send,
  Loader2,
  Wrench,
  DollarSign,
  RotateCcw,
  ChevronDown,
} from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  toolCalls?: ToolCall[];
  usage?: UsageInfo;
  timestamp: number;
}

interface ToolCall {
  name: string;
  id: string;
  status: "running" | "done" | "error";
  result?: string;
}

interface UsageInfo {
  total_input_tokens: number;
  total_output_tokens: number;
  total_cost_usd: number;
  total_calls: number;
}

const AGENT_TYPES = [
  { id: "general", label: "Geral", description: "Assistente genérico" },
  { id: "sdr", label: "SDR", description: "Vendas e qualificação" },
  { id: "support", label: "Suporte", description: "Atendimento a pacientes" },
  { id: "content", label: "Conteúdo", description: "Criação de copies" },
  { id: "scheduler", label: "Agendamento", description: "Gerenciar consultas" },
] as const;

export default function AgentsPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [agentType, setAgentType] = useState("general");
  const [sessionUsage, setSessionUsage] = useState<UsageInfo | null>(null);
  const [showAgentPicker, setShowAgentPicker] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: trimmed,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    const assistantId = `assistant-${Date.now()}`;
    const assistantMsg: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      toolCalls: [],
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      abortRef.current = new AbortController();

      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          agent_type: agentType,
          stream: true,
        }),
        signal: abortRef.current.signal,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API error ${response.status}: ${errorText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6);
          if (data === "[DONE]") break;

          try {
            const event = JSON.parse(data);
            handleSSEEvent(event, assistantId);
          } catch {
            // Skip malformed events
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") return;
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: m.content || `Erro: ${err instanceof Error ? err.message : "Unknown error"}` }
            : m
        )
      );
    } finally {
      setLoading(false);
      abortRef.current = null;
      setTimeout(scrollToBottom, 100);
    }
  };

  const handleSSEEvent = (event: Record<string, unknown>, msgId: string) => {
    switch (event.type) {
      case "text":
        setMessages((prev) =>
          prev.map((m) =>
            m.id === msgId
              ? { ...m, content: m.content + (event.content as string) }
              : m
          )
        );
        setTimeout(scrollToBottom, 50);
        break;

      case "tool_start":
        setMessages((prev) =>
          prev.map((m) =>
            m.id === msgId
              ? {
                  ...m,
                  toolCalls: [
                    ...(m.toolCalls || []),
                    { name: event.name as string, id: event.id as string, status: "running" },
                  ],
                }
              : m
          )
        );
        break;

      case "tool_result":
        setMessages((prev) =>
          prev.map((m) =>
            m.id === msgId
              ? {
                  ...m,
                  toolCalls: (m.toolCalls || []).map((tc) =>
                    tc.id === event.id
                      ? { ...tc, status: "done" as const, result: (event.content as string)?.slice(0, 200) }
                      : tc
                  ),
                }
              : m
          )
        );
        break;

      case "usage":
        setSessionUsage(event.costs as UsageInfo);
        break;

      case "done": {
        const result = event.result as Record<string, unknown> | undefined;
        if (result) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId
                ? {
                    ...m,
                    usage: {
                      total_input_tokens: (result.total_input_tokens as number) || 0,
                      total_output_tokens: (result.total_output_tokens as number) || 0,
                      total_cost_usd: (result.total_cost_usd as number) || 0,
                      total_calls: (result.total_calls as number) || 0,
                    },
                  }
                : m
            )
          );
        }
        break;
      }

      case "error":
        setMessages((prev) =>
          prev.map((m) =>
            m.id === msgId
              ? { ...m, content: m.content || `Erro: ${event.message as string}` }
              : m
          )
        );
        break;
    }
  };

  const handleReset = () => {
    abortRef.current?.abort();
    setMessages([]);
    setSessionUsage(null);
    setLoading(false);
  };

  return (
    <Shell>
      <div className="flex flex-col h-[calc(100dvh-4rem)]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-graphite bg-white">
          <div className="flex items-center gap-3">
            <Bot size={20} className="text-accent-orange" />
            <h1 className="font-mono text-sm font-semibold uppercase tracking-wider">
              Agent Playground
            </h1>
          </div>

          <div className="flex items-center gap-3">
            {/* Agent Type Picker */}
            <div className="relative">
              <button
                onClick={() => setShowAgentPicker(!showAgentPicker)}
                className="flex items-center gap-2 px-3 py-1.5 border border-graphite text-xs font-mono uppercase tracking-wider hover:bg-paper transition-colors"
              >
                {AGENT_TYPES.find((a) => a.id === agentType)?.label || "Geral"}
                <ChevronDown size={12} />
              </button>
              {showAgentPicker && (
                <div className="absolute right-0 top-full mt-1 bg-white border border-graphite shadow-hard-sm z-dropdown min-w-[200px]">
                  {AGENT_TYPES.map((agent) => (
                    <button
                      key={agent.id}
                      onClick={() => {
                        setAgentType(agent.id);
                        setShowAgentPicker(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-sm hover:bg-paper transition-colors ${
                        agentType === agent.id ? "bg-paper border-l-2 border-l-accent-orange" : ""
                      }`}
                    >
                      <span className="font-medium">{agent.label}</span>
                      <span className="block text-xs text-steel">{agent.description}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Usage Display */}
            {sessionUsage && (
              <div className="flex items-center gap-1 px-2 py-1 bg-paper text-xs font-mono text-steel">
                <DollarSign size={10} />
                <span>${sessionUsage.total_cost_usd.toFixed(4)}</span>
                <span className="text-graphite/30">|</span>
                <span>{sessionUsage.total_input_tokens + sessionUsage.total_output_tokens} tok</span>
              </div>
            )}

            {/* Reset */}
            <button
              onClick={handleReset}
              className="p-1.5 text-steel hover:text-accent-orange transition-colors"
              title="Nova conversa"
            >
              <RotateCcw size={14} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Bot size={48} className="text-steel/30 mb-4" />
              <p className="text-sm text-steel">
                Envie uma mensagem para testar o agente <strong>{AGENT_TYPES.find((a) => a.id === agentType)?.label}</strong>.
              </p>
              <p className="text-xs text-steel/60 mt-1">
                Streaming SSE com visibilidade de tools e custo por mensagem.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[75%] ${
                  msg.role === "user"
                    ? "bg-ink text-white px-4 py-2.5"
                    : "bg-white border border-graphite px-4 py-2.5"
                }`}
              >
                {/* Content */}
                <p className="text-sm whitespace-pre-wrap break-words">
                  {msg.content}
                  {msg.role === "assistant" && loading && msg.id === messages[messages.length - 1]?.id && !msg.content && (
                    <span className="inline-flex items-center gap-1 text-steel">
                      <Loader2 size={12} className="animate-spin" />
                      <span className="text-xs">pensando...</span>
                    </span>
                  )}
                </p>

                {/* Tool Calls */}
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-graphite/20 space-y-1">
                    {msg.toolCalls.map((tc) => (
                      <div
                        key={tc.id}
                        className="flex items-center gap-2 text-xs font-mono text-steel"
                      >
                        <Wrench size={10} />
                        <span className={tc.status === "running" ? "text-accent-blue" : ""}>
                          {tc.name}
                        </span>
                        {tc.status === "running" && (
                          <Loader2 size={10} className="animate-spin text-accent-blue" />
                        )}
                        {tc.status === "done" && <span className="text-green-600">ok</span>}
                        {tc.status === "error" && <span className="text-red-600">erro</span>}
                      </div>
                    ))}
                  </div>
                )}

                {/* Per-message usage */}
                {msg.usage && (
                  <div className="mt-2 pt-1 border-t border-graphite/10 text-[10px] font-mono text-steel/60">
                    {msg.usage.total_input_tokens + msg.usage.total_output_tokens} tokens | ${msg.usage.total_cost_usd.toFixed(4)}
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form
          onSubmit={handleSubmit}
          className="flex items-center gap-3 px-6 py-3 border-t border-graphite bg-white"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Digite uma mensagem para o agente..."
            disabled={loading}
            className="flex-1 px-4 py-2.5 border border-graphite bg-paper text-sm placeholder:text-steel/50 focus:outline-none focus:border-accent-orange disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="flex items-center gap-2 px-4 py-2.5 bg-ink text-white text-sm font-medium hover:bg-accent-orange transition-colors disabled:opacity-30 disabled:hover:bg-ink"
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            Enviar
          </button>
        </form>
      </div>
    </Shell>
  );
}
