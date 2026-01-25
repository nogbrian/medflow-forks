"use client";

import { ExternalLink, Maximize2, RefreshCw, Calendar } from "lucide-react";
import { Shell } from "@/components/layout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useSsoUrl } from "@/hooks/use-sso-url";

/**
 * Agenda Page - Cal.com Embed
 *
 * Uses SSO endpoint for authenticated Cal.com access.
 * Falls back to the base URL (public pages don't require auth).
 */

export default function AgendaPage() {
  const calcomUrl = process.env.NEXT_PUBLIC_CALCOM_URL || "http://localhost:3002";
  const { url: iframeSrc, loading, error: ssoError } = useSsoUrl("calcom", calcomUrl);

  return (
    <Shell>
      {/* Service Header - Intelligent Flow Design */}
      <div className="border-b border-eng-blue/[0.06] bg-white/80 backdrop-blur-sm">
        <div className="px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-md bg-gradient-to-br from-eng-blue to-[#1A4A55] flex items-center justify-center shadow-sm">
                <Calendar className="h-4 w-4 text-white" />
              </div>
              <h1 className="font-display text-lg font-semibold text-eng-blue tracking-tight">
                Agenda
              </h1>
            </div>
            <Badge variant="info">
              Cal.com
            </Badge>
            {ssoError && (
              <Badge variant="warning">Login manual</Badge>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                const iframe = document.getElementById("agenda-frame") as HTMLIFrameElement;
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
                const iframe = document.getElementById("agenda-frame") as HTMLIFrameElement;
                if (iframe) iframe.requestFullscreen?.();
              }}
              aria-label="Tela cheia"
            >
              <Maximize2 size={16} />
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => window.open(calcomUrl, "_blank")}
            >
              <ExternalLink size={14} />
              Abrir em Nova Aba
            </Button>
          </div>
        </div>
      </div>

      {/* Iframe Container */}
      <div className="h-[calc(100dvh-8rem)] bg-tech-white">
        {!loading && iframeSrc ? (
          <iframe
            id="agenda-frame"
            src={iframeSrc}
            className="w-full h-full border-0"
            title="Cal.com Agenda"
            allow="clipboard-read; clipboard-write"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <div className="w-8 h-8 border-3 border-eng-blue/20 border-t-alert rounded-full animate-spin" />
          </div>
        )}
      </div>
    </Shell>
  );
}
