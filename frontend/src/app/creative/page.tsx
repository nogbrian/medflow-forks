"use client";

import { useCallback, useEffect, useState } from "react";
import { ExternalLink, Maximize2, RefreshCw, Send, CheckCircle, Sparkles } from "lucide-react";
import { Shell } from "@/components/layout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/auth/auth-provider";

interface CreativeEvent {
  images: string[];
  prompt: string;
  count: number;
}

export default function CreativePage() {
  const studioUrl = process.env.NEXT_PUBLIC_CREATIVE_STUDIO_URL || "http://localhost:3001";
  const { token } = useAuth();
  const [lastCreative, setLastCreative] = useState<CreativeEvent | null>(null);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  // Listen for postMessage from Creative Studio iframe
  useEffect(() => {
    function handleMessage(event: MessageEvent) {
      if (event.data?.type === "creative:generated") {
        setLastCreative({
          images: event.data.images,
          prompt: event.data.prompt,
          count: event.data.count,
        });
        setSent(false);
      }
    }
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  const sendToChatwoot = useCallback(async () => {
    if (!lastCreative || !token) return;
    setSending(true);
    try {
      await fetch("/api/creative-lab/send-to-chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          images: lastCreative.images.slice(0, 1), // Send first image
          prompt: lastCreative.prompt,
        }),
      });
      setSent(true);
    } catch {
      // Silent fail - endpoint may not exist yet
    } finally {
      setSending(false);
    }
  }, [lastCreative, token]);

  return (
    <Shell>
      {/* Service Header - Intelligent Flow Design */}
      <div className="border-b border-eng-blue/[0.06] bg-white/80 backdrop-blur-sm">
        <div className="px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-md bg-gradient-to-br from-alert to-orange-600 flex items-center justify-center shadow-sm shadow-glow-orange/30">
                <Sparkles className="h-4 w-4 text-white" />
              </div>
              <h1 className="font-display text-lg font-semibold text-eng-blue tracking-tight">
                Creative Studio
              </h1>
            </div>
            <Badge variant="info">
              Gemini AI
            </Badge>
            {lastCreative && (
              <Badge variant="success">
                {lastCreative.count} {lastCreative.count === 1 ? "criativo" : "criativos"}
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-2">
            {lastCreative && (
              <Button
                variant="secondary"
                size="sm"
                onClick={sendToChatwoot}
                disabled={sending || sent}
              >
                {sent ? <CheckCircle size={14} /> : <Send size={14} />}
                {sent ? "Enviado" : sending ? "Enviando..." : "Enviar ao Chat"}
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                const iframe = document.getElementById("creative-frame") as HTMLIFrameElement;
                if (iframe) iframe.src = iframe.src;
              }}
              aria-label="Recarregar"
            >
              <RefreshCw size={16} />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                const iframe = document.getElementById("creative-frame") as HTMLIFrameElement;
                if (iframe) iframe.requestFullscreen?.();
              }}
              aria-label="Tela cheia"
            >
              <Maximize2 size={16} />
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => window.open(studioUrl, "_blank")}
            >
              <ExternalLink size={14} />
              Abrir em Nova Aba
            </Button>
          </div>
        </div>
      </div>

      {/* Iframe Container */}
      <div className="h-[calc(100dvh-8rem)] bg-tech-white">
        <iframe
          id="creative-frame"
          src={studioUrl}
          className="w-full h-full border-0"
          title="Creative Studio"
          allow="clipboard-read; clipboard-write"
        />
      </div>
    </Shell>
  );
}
