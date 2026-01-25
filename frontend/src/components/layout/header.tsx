"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowRight, Menu, Bell, User, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

/**
 * Header - Intelligent Flow Design
 *
 * Glassmorphism com transição ao scroll.
 * Logo com hover animado, nav links com underline.
 */

interface HeaderProps {
  onMenuClick?: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header
      className={cn(
        "sticky top-0 z-header",
        "backdrop-blur-xl",
        "border-b border-eng-blue/[0.06]",
        "transition-all duration-300",
        isScrolled ? "bg-white/95 shadow-md" : "bg-tech-white/80"
      )}
    >
      <div className="max-w-[1920px] mx-auto flex h-16 items-center px-4 lg:px-8 gap-4 lg:gap-8">
        {/* Mobile Menu Toggle */}
        <button
          onClick={onMenuClick}
          className="lg:hidden flex items-center justify-center w-10 h-10 rounded-md hover:bg-eng-blue-05 transition-all duration-300"
          aria-label="Abrir menu"
        >
          <Menu size={20} className="text-eng-blue" />
        </button>

        {/* Logo Block with hover animation */}
        <Link
          href="/"
          className="flex items-center gap-3 group cursor-pointer"
        >
          <div className="w-10 h-10 rounded-md bg-gradient-to-br from-eng-blue to-[#1A4A55] flex items-center justify-center transition-transform duration-300 group-hover:rotate-[-8deg] group-hover:scale-105">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div className="flex flex-col leading-none">
            <span className="font-display font-semibold text-lg text-eng-blue tracking-tight">
              MedFlow
            </span>
            <span className="font-mono text-[10px] text-concrete tracking-wide">
              Sistema Integrado
            </span>
          </div>
        </Link>

        {/* Status Badge */}
        <div className="hidden md:flex items-center ml-4">
          <Badge variant="active">
            <span className="size-1.5 rounded-full bg-green-500 animate-pulse" />
            Operacional
          </Badge>
        </div>

        {/* Nav Links with animated underline */}
        <nav className="flex-1 hidden lg:flex items-center justify-center gap-8">
          {[
            { href: "/crm", label: "CRM" },
            { href: "/agenda", label: "Agenda" },
            { href: "/inbox", label: "Inbox" },
            { href: "/creative", label: "Creative Lab" },
          ].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="relative font-sans font-medium text-sm text-eng-blue hover:text-alert transition-colors duration-300 group"
            >
              {item.label}
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-alert rounded-full transition-all duration-300 group-hover:w-full" />
            </Link>
          ))}
        </nav>

        {/* Right side actions */}
        <div className="flex items-center gap-2">
          {/* Notifications */}
          <button
            className="hidden md:flex items-center justify-center w-10 h-10 rounded-md hover:bg-eng-blue-05 transition-all duration-300 relative"
            aria-label="Notificações"
          >
            <Bell size={18} className="text-eng-blue" />
            <span className="absolute top-2 right-2 size-2 rounded-full bg-alert" />
          </button>

          {/* User Menu */}
          <button
            className="hidden md:flex items-center justify-center w-10 h-10 rounded-md hover:bg-eng-blue-05 transition-all duration-300"
            aria-label="Menu do usuário"
          >
            <User size={18} className="text-eng-blue" />
          </button>

          {/* CTA Block */}
          <Link
            href="/agents"
            className={cn(
              "bg-alert text-white px-6 py-2.5 rounded-md",
              "font-sans text-sm font-semibold",
              "shadow-md shadow-glow-orange",
              "hover:shadow-lg hover:-translate-y-0.5",
              "transition-all duration-300",
              "flex items-center gap-2"
            )}
          >
            <span className="hidden sm:inline">Agentes IA</span>
            <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    </header>
  );
}
