"use client";

import { ExternalLink, Maximize2, RefreshCw } from "lucide-react";
import { Shell } from "@/components/layout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

/**
 * Inbox Page - Chatwoot Embed
 *
 * Integra o Chatwoot via iframe.
 */

export default function InboxPage() {
  const chatwootUrl = process.env.NEXT_PUBLIC_CHATWOOT_URL || "http://localhost:3003";

  return (
    <Shell>
      {/* Service Header */}
      <div className="border-b border-graphite bg-white">
        <div className="px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold tracking-tight uppercase">
              Inbox
            </h1>
            <Badge variant="info">
              Chatwoot
            </Badge>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                const iframe = document.getElementById("inbox-frame") as HTMLIFrameElement;
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
                const iframe = document.getElementById("inbox-frame") as HTMLIFrameElement;
                if (iframe) iframe.requestFullscreen?.();
              }}
              aria-label="Tela cheia"
            >
              <Maximize2 size={16} />
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => window.open(chatwootUrl, "_blank")}
            >
              <ExternalLink size={14} />
              Abrir em Nova Aba
            </Button>
          </div>
        </div>
      </div>

      {/* Iframe Container */}
      <div className="h-[calc(100dvh-8rem)] bg-white border-x border-graphite">
        <iframe
          id="inbox-frame"
          src={chatwootUrl}
          className="w-full h-full border-0"
          title="Chatwoot Inbox"
          allow="clipboard-read; clipboard-write"
        />
      </div>
    </Shell>
  );
}
