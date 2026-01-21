"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  Building2,
  Kanban,
  Calendar,
  Clock,
  ListChecks,
  MessageSquare,
  Contact,
  Palette,
  Bot,
  PenLine,
  Image,
  Workflow,
  ClipboardList,
  Settings,
  Hospital,
  Plug,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Sidebar Industrial
 *
 * Navegação lateral com grid exposto.
 * Links organizados por seção.
 */

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const navigation: NavSection[] = [
  {
    title: "Principal",
    items: [
      { href: "/", label: "Dashboard", icon: LayoutDashboard },
    ],
  },
  {
    title: "CRM",
    items: [
      { href: "/crm/contacts", label: "Contatos", icon: Users },
      { href: "/crm/companies", label: "Empresas", icon: Building2 },
      { href: "/crm/pipeline", label: "Pipeline", icon: Kanban },
    ],
  },
  {
    title: "Agenda",
    items: [
      { href: "/agenda/bookings", label: "Agendamentos", icon: Calendar },
      { href: "/agenda/availability", label: "Disponibilidade", icon: Clock },
      { href: "/agenda/event-types", label: "Tipos de Evento", icon: ListChecks },
    ],
  },
  {
    title: "Inbox",
    items: [
      { href: "/inbox/conversations", label: "Conversas", icon: MessageSquare },
      { href: "/inbox/contacts", label: "Contatos", icon: Contact },
    ],
  },
  {
    title: "Creative Lab",
    items: [
      { href: "/creative/chat", label: "Assistente", icon: Bot },
      { href: "/creative/copy", label: "Copywriter", icon: PenLine },
      { href: "/creative/image", label: "Designer", icon: Image },
    ],
  },
  {
    title: "Agentes IA",
    items: [
      { href: "/agents/workflows", label: "Workflows", icon: Workflow },
      { href: "/agents/plans", label: "Planos", icon: ClipboardList },
    ],
  },
  {
    title: "Configurações",
    items: [
      { href: "/settings/clinics", label: "Clínicas", icon: Hospital },
      { href: "/settings/users", label: "Usuários", icon: Users },
      { href: "/settings/integrations", label: "Integrações", icon: Plug },
    ],
  },
];

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-ink/50 z-sidebar lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-16 left-0 z-sidebar",
          "w-64 h-[calc(100dvh-4rem)]",
          "bg-paper border-r border-graphite",
          "overflow-y-auto",
          "transition-transform duration-150 ease-out",
          // Mobile: slide in/out
          "lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Mobile Close */}
        <button
          onClick={onClose}
          className="lg:hidden absolute top-4 right-4 p-2 hover:text-accent-orange"
          aria-label="Fechar menu"
        >
          <X size={20} />
        </button>

        {/* Navigation */}
        <nav className="py-6">
          {navigation.map((section) => (
            <div key={section.title} className="mb-6">
              {/* Section Title */}
              <h3 className="px-6 mb-2 font-mono text-[10px] uppercase text-steel tracking-wider">
                {section.title}
              </h3>

              {/* Section Items */}
              <ul>
                {section.items.map((item) => {
                  const isActive = pathname === item.href ||
                    (item.href !== "/" && pathname.startsWith(item.href));
                  const Icon = item.icon;

                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        onClick={onClose}
                        className={cn(
                          "flex items-center gap-3 px-6 py-2.5",
                          "text-sm font-medium",
                          "border-l-2 border-transparent",
                          "transition-colors duration-100",
                          isActive
                            ? "bg-white text-ink border-l-accent-orange"
                            : "hover:bg-white hover:border-l-steel"
                        )}
                      >
                        <Icon size={16} className={isActive ? "text-accent-orange" : ""} />
                        {item.label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-graphite bg-white">
          <div className="flex justify-between items-end">
            <div>
              <span className="font-mono text-[10px] text-steel uppercase block mb-1">
                Sistema
              </span>
              <span className="font-mono text-xs font-bold">MF-2026</span>
            </div>
            <div className="text-right">
              <span className="font-mono text-[10px] text-steel uppercase block mb-1">
                Versão
              </span>
              <span className="font-mono text-xs">1.0.0</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
