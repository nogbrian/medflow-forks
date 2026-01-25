"use client";

import { ExternalLink, Maximize2, RefreshCw, Kanban } from "lucide-react";
import { Shell } from "@/components/layout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useSsoUrl } from "@/hooks/use-sso-url";

/**
 * CRM Page - Twenty CRM Embed
 *
 * Uses SSO endpoint to auto-login the user into Twenty CRM.
 * Falls back to the base URL if SSO is not configured.
 */

export default function CRMPage() {
  const twentyUrl = process.env.NEXT_PUBLIC_TWENTY_URL || "http://localhost:3004";
  const { url: iframeSrc, loading, error: ssoError } = useSsoUrl("twenty", twentyUrl);

  return (
    <Shell>
      {/* Service Header - Intelligent Flow Design */}
      <div className="border-b border-eng-blue/[0.06] bg-white/80 backdrop-blur-sm">
        <div className="px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-md bg-gradient-to-br from-eng-blue to-[#1A4A55] flex items-center justify-center shadow-sm">
                <Kanban className="h-4 w-4 text-white" />
              </div>
              <h1 className="font-display text-lg font-semibold text-eng-blue tracking-tight">
                CRM
              </h1>
            </div>
            <Badge variant="info">
              Twenty CRM
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
                const iframe = document.getElementById("crm-frame") as HTMLIFrameElement;
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
                const iframe = document.getElementById("crm-frame") as HTMLIFrameElement;
                if (iframe) iframe.requestFullscreen?.();
              }}
              aria-label="Tela cheia"
            >
              <Maximize2 size={16} />
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => window.open(twentyUrl, "_blank")}
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
            id="crm-frame"
            src={iframeSrc}
            className="w-full h-full border-0"
            title="Twenty CRM"
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
