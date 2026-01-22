"use client";

import { ExternalLink, Maximize2, RefreshCw } from "lucide-react";
import { Shell } from "@/components/layout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

/**
 * Creative Studio Page - Gemini-powered Image Generation
 *
 * Integra o Creative Studio via iframe.
 */

export default function CreativePage() {
  const studioUrl = process.env.NEXT_PUBLIC_CREATIVE_STUDIO_URL || "http://localhost:3001";

  return (
    <Shell>
      {/* Service Header */}
      <div className="border-b border-graphite bg-white">
        <div className="px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold tracking-tight uppercase">
              Creative Studio
            </h1>
            <Badge variant="info">
              Gemini AI
            </Badge>
          </div>

          <div className="flex items-center gap-2">
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
      <div className="h-[calc(100dvh-8rem)] bg-white border-x border-graphite">
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
