"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Header } from "./header";
import { Sidebar } from "./sidebar";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth/auth-provider";
import { AgentChatFab, AgentChatPanel } from "@/components/agent-chat";

/**
 * Shell Layout Industrial
 *
 * Layout principal com Header fixo e Sidebar.
 * Redireciona para /login se não autenticado.
 */

interface ShellProps {
  children: React.ReactNode;
}

export function Shell({ children }: ShellProps) {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const { user, loading } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="min-h-dvh bg-paper bg-grid flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-ink/20 border-t-ink rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs font-mono text-steel uppercase tracking-widest">
            Carregando...
          </p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-dvh bg-paper">
      <Header onMenuClick={() => setSidebarOpen(true)} />
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content */}
      <main
        className={cn(
          "lg:ml-64",
          "min-h-[calc(100dvh-4rem)]",
          "bg-grid"
        )}
      >
        <div className="max-w-[1920px] mx-auto">
          {children}
        </div>
      </main>

      <AgentChatPanel />
      <AgentChatFab />
    </div>
  );
}
