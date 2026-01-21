"use client";

import Link from "next/link";
import { ArrowRight, Menu, Bell, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

/**
 * Header Industrial
 *
 * Barra de ferramentas fixa no topo.
 * Grid dividido por bordas pretas.
 */

interface HeaderProps {
  onMenuClick?: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  return (
    <header className="sticky top-0 z-header bg-paper border-b border-graphite">
      <div className="max-w-[1920px] mx-auto flex h-16 divide-x divide-graphite border-x border-graphite">
        {/* Mobile Menu Toggle */}
        <button
          onClick={onMenuClick}
          className="lg:hidden flex items-center justify-center w-16 hover:bg-white transition-colors"
          aria-label="Abrir menu"
        >
          <Menu size={20} />
        </button>

        {/* Logo Block */}
        <Link
          href="/"
          className="w-64 flex items-center px-6 bg-white hover:bg-paper transition-colors"
        >
          <div className="flex flex-col leading-none">
            <span className="font-bold text-lg tracking-tight uppercase">
              MedFlow
            </span>
            <span className="font-mono text-[10px] text-steel uppercase tracking-wider">
              Sistema Integrado
            </span>
          </div>
        </Link>

        {/* Status Badge */}
        <div className="hidden md:flex items-center px-6">
          <Badge variant="active">
            <span className="size-1.5 bg-[#22C55E] animate-pulse" />
            Operacional
          </Badge>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 hidden lg:flex items-center px-8 gap-8">
          {[
            { href: "/crm", label: "CRM" },
            { href: "/agenda", label: "Agenda" },
            { href: "/inbox", label: "Inbox" },
            { href: "/creative", label: "Creative Lab" },
          ].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "font-medium text-sm uppercase tracking-wide",
                "hover:text-accent-orange transition-colors duration-100"
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        {/* Notifications */}
        <button
          className="hidden md:flex items-center justify-center w-16 hover:bg-white transition-colors relative"
          aria-label="Notificações"
        >
          <Bell size={18} />
          <span className="absolute top-4 right-4 size-2 bg-accent-orange" />
        </button>

        {/* User Menu */}
        <button
          className="hidden md:flex items-center justify-center w-16 hover:bg-white transition-colors"
          aria-label="Menu do usuário"
        >
          <User size={18} />
        </button>

        {/* CTA Block */}
        <Link
          href="/agents"
          className={cn(
            "bg-ink text-white px-8 h-full",
            "font-mono text-xs uppercase tracking-wider",
            "hover:bg-accent-orange transition-colors duration-100",
            "flex items-center gap-2"
          )}
        >
          <span className="hidden sm:inline">Agentes IA</span>
          <ArrowRight size={14} />
        </Link>
      </div>
    </header>
  );
}
