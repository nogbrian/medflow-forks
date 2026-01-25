"use client";

import { useState, useRef, useCallback } from "react";
import { Shell } from "@/components/layout/shell";
import { getStoredToken } from "@/lib/auth";
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

      const token = getStoredToken();
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
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
        {/* Header - Intelligent Flow Design */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-eng-blue/[0.06] bg-white/80 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-gradient-to-br from-eng-blue to-[#1A4A55] flex items-center justify-center shadow-sm">
              <Bot size={16} className="text-white" />
            </div>
            <h1 className="font-display text-lg font-semibold text-eng-blue tracking-tight">
              Agent Playground
            </h1>
          </div>

          <div className="flex items-center gap-3">
            {/* Agent Type Picker */}
            <div className="relative">
              <button
                onClick={() => setShowAgentPicker(!showAgentPicker)}
                className="flex items-center gap-2 px-3 py-1.5 border-2 border-eng-blue-10 rounded-md text-xs font-sans font-medium text-eng-blue hover:bg-eng-blue-05 transition-all duration-300"
              >
                {AGENT_TYPES.find((a) => a.id === agentType)?.label || "Geral"}
                <ChevronDown size={12} />
              </button>
              {showAgentPicker && (
                <div className="absolute right-0 top-full mt-2 bg-white/95 backdrop-blur-xl border border-eng-blue/[0.08] rounded-lg shadow-lg z-dropdown min-w-[200px] overflow-hidden">
                  {AGENT_TYPES.map((agent) => (
                    <button
                      key={agent.id}
                      onClick={() => {
                        setAgentType(agent.id);
                        setShowAgentPicker(false);
                      }}
                      className={`w-full text-left px-4 py-2.5 text-sm font-sans hover:bg-eng-blue-05 transition-all duration-300 ${
                        agentType === agent.id ? "bg-alert-05 border-l-2 border-l-alert text-alert" : "text-eng-blue"
                      }`}
                    >
                      <span className="font-medium">{agent.label}</span>
                      <span className="block text-xs text-concrete">{agent.description}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Usage Display */}
            {sessionUsage && (
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-eng-blue-05 rounded-md text-xs font-mono text-eng-blue">
                <DollarSign size={10} className="text-alert" />
                <span>${sessionUsage.total_cost_usd.toFixed(4)}</span>
                <span className="text-concrete">|</span>
                <span>{sessionUsage.total_input_tokens + sessionUsage.total_output_tokens} tok</span>
              </div>
            )}

            {/* Reset */}
            <button
              onClick={handleReset}
              className="p-2 rounded-md text-concrete hover:text-alert hover:bg-alert-05 transition-all duration-300"
              title="Nova conversa"
            >
              <RotateCcw size={14} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 bg-tech-white">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-full bg-alert-10 flex items-center justify-center mb-4">
                <Bot size={32} className="text-alert" />
              </div>
              <p className="text-sm text-eng-blue font-sans">
                Envie uma mensagem para testar o agente <strong className="text-alert">{AGENT_TYPES.find((a) => a.id === agentType)?.label}</strong>.
              </p>
              <p className="text-xs text-concrete mt-2 font-sans">
                Streaming SSE com visibilidade de tools e custo por mensagem.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-fade-in`}
            >
              <div
                className={`max-w-[75%] rounded-lg ${
                  msg.role === "user"
                    ? "bg-eng-blue text-white px-4 py-3"
                    : "bg-white border border-eng-blue/[0.08] px-4 py-3 shadow-sm"
                }`}
              >
                {/* Content */}
                <p className="text-sm font-sans whitespace-pre-wrap break-words">
                  {msg.content}
                  {msg.role === "assistant" && loading && msg.id === messages[messages.length - 1]?.id && !msg.content && (
                    <span className="inline-flex items-center gap-1.5 text-concrete">
                      <Loader2 size={12} className="animate-spin text-alert" />
                      <span className="text-xs">pensando...</span>
                    </span>
                  )}
                </p>

                {/* Tool Calls */}
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-eng-blue/[0.06] space-y-1.5">
                    {msg.toolCalls.map((tc) => (
                      <div
                        key={tc.id}
                        className="flex items-center gap-2 text-xs font-mono text-concrete"
                      >
                        <Wrench size={10} className="text-alert" />
                        <span className={tc.status === "running" ? "text-alert" : "text-eng-blue"}>
                          {tc.name}
                        </span>
                        {tc.status === "running" && (
                          <Loader2 size={10} className="animate-spin text-alert" />
                        )}
                        {tc.status === "done" && <span className="text-green-600">ok</span>}
                        {tc.status === "error" && <span className="text-red-600">erro</span>}
                      </div>
                    ))}
                  </div>
                )}

                {/* Per-message usage */}
                {msg.usage && (
                  <div className="mt-2 pt-1 border-t border-eng-blue/[0.04] text-[10px] font-mono text-concrete">
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
          className="flex items-center gap-3 px-6 py-3 border-t border-eng-blue/[0.06] bg-white/80 backdrop-blur-sm"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Digite uma mensagem para o agente..."
            disabled={loading}
            className="flex-1 px-4 py-2.5 border-2 border-eng-blue-10 bg-white/80 rounded-md text-sm font-sans placeholder:text-concrete/50 text-eng-blue focus:outline-none focus:border-alert focus:ring-4 focus:ring-alert-10 disabled:opacity-50 transition-all duration-300"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="flex items-center gap-2 px-4 py-2.5 bg-alert text-white rounded-md text-sm font-sans font-semibold shadow-md shadow-glow-orange hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300 disabled:opacity-30 disabled:transform-none disabled:shadow-none"
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            Enviar
          </button>
        </form>
      </div>
    </Shell>
  );
}
