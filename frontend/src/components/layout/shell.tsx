"use client";

import * as React from "react";
import { Header } from "./header";
import { Sidebar } from "./sidebar";
import { cn } from "@/lib/utils";

/**
 * Shell Layout Industrial
 *
 * Layout principal com Header fixo e Sidebar.
 * Área de conteúdo com grid pattern.
 */

interface ShellProps {
  children: React.ReactNode;
}

export function Shell({ children }: ShellProps) {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  return (
    <div className="min-h-dvh bg-paper">
      <Header onMenuClick={() => setSidebarOpen(true)} />
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content */}
      <main
        className={cn(
          "lg:ml-64", // Offset for sidebar on desktop
          "min-h-[calc(100dvh-4rem)]",
          "bg-grid"
        )}
      >
        <div className="max-w-[1920px] mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
