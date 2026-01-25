"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Header } from "./header";
import { Sidebar } from "./sidebar";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth/auth-provider";
import { AgentChatFab, AgentChatPanel } from "@/components/agent-chat";

/**
 * Shell Layout - Intelligent Flow Design
 *
 * Layout principal com Header fixo e Sidebar.
 * Glassmorphism e transições suaves.
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
      <div className="min-h-dvh bg-tech-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-eng-blue/20 border-t-alert rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm font-sans text-concrete">
            Carregando...
          </p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-dvh bg-tech-white">
      <Header onMenuClick={() => setSidebarOpen(true)} />
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content */}
      <main
        className={cn(
          "lg:ml-64",
          "min-h-[calc(100dvh-4rem)]"
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
