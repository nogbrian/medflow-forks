"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  Kanban,
  Calendar,
  MessageSquare,
  Image,
  Hospital,
  Plug,
  X,
  LogOut,
  Radar,
  Bot,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth/auth-provider";

/**
 * Sidebar - Intelligent Flow Design
 *
 * Navegação lateral com glassmorphism e transições suaves.
 * Links com hover lift e indicador de página ativa.
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
      { href: "/crm", label: "CRM", icon: Kanban },
      { href: "/crm/contacts", label: "Contatos", icon: Users },
    ],
  },
  {
    title: "Agenda",
    items: [
      { href: "/agenda", label: "Agendamentos", icon: Calendar },
    ],
  },
  {
    title: "Inbox",
    items: [
      { href: "/inbox", label: "Conversas", icon: MessageSquare },
    ],
  },
  {
    title: "Creative Lab",
    items: [
      { href: "/creative", label: "Creative Studio", icon: Image },
    ],
  },
  {
    title: "Agentes",
    items: [
      { href: "/agents", label: "Playground", icon: Bot },
    ],
  },
  {
    title: "Inteligência",
    items: [
      { href: "https://intel.trafegoparaconsultorios.com.br", label: "Viral Finder", icon: Radar },
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
  const { user, logout } = useAuth();

  return (
    <>
      {/* Mobile Overlay with blur */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-eng-blue/60 backdrop-blur-sm z-sidebar lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-16 left-0 z-sidebar",
          "w-64 h-[calc(100dvh-4rem)]",
          "bg-white/95 backdrop-blur-xl",
          "border-r border-eng-blue/[0.06]",
          "overflow-y-auto",
          "transition-transform duration-300 ease-out",
          // Mobile: slide in/out
          "lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Mobile Close */}
        <button
          onClick={onClose}
          className="lg:hidden absolute top-4 right-4 p-2 rounded-md hover:bg-eng-blue-05 hover:text-alert transition-all duration-300"
          aria-label="Fechar menu"
        >
          <X size={20} />
        </button>

        {/* Navigation */}
        <nav className="py-6">
          {navigation.map((section) => (
            <div key={section.title} className="mb-6">
              {/* Section Title */}
              <h3 className="px-6 mb-2 font-mono text-[10px] uppercase text-concrete tracking-wider">
                {section.title}
              </h3>

              {/* Section Items */}
              <ul className="space-y-1">
                {section.items.map((item) => {
                  const isExternal = item.href.startsWith("http");
                  const isActive = !isExternal && (
                    pathname === item.href ||
                    (item.href !== "/" && pathname.startsWith(item.href))
                  );
                  const Icon = item.icon;
                  const linkClass = cn(
                    "flex items-center gap-3 mx-3 px-3 py-2.5",
                    "text-sm font-sans font-medium",
                    "rounded-md",
                    "transition-all duration-300",
                    isActive
                      ? "bg-alert-10 text-alert"
                      : "hover:bg-eng-blue-05 text-eng-blue"
                  );

                  return (
                    <li key={item.href}>
                      {isExternal ? (
                        <a
                          href={item.href}
                          onClick={onClose}
                          className={linkClass}
                        >
                          <Icon size={16} />
                          {item.label}
                        </a>
                      ) : (
                        <Link
                          href={item.href}
                          onClick={onClose}
                          className={linkClass}
                        >
                          <Icon size={16} className={isActive ? "text-alert" : ""} />
                          {item.label}
                        </Link>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        {/* Footer - User & Logout */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-eng-blue-10 bg-white/80 backdrop-blur-sm">
          {user && (
            <div className="flex items-center justify-between">
              <div className="min-w-0">
                <span className="block text-sm font-sans font-medium text-eng-blue truncate">
                  {user.name}
                </span>
                <span className="block font-mono text-[10px] text-concrete truncate">
                  {user.email}
                </span>
              </div>
              <button
                onClick={logout}
                className="p-2 rounded-md text-concrete hover:text-red-600 hover:bg-red-50 transition-all duration-300 flex-shrink-0"
                aria-label="Sair"
                title="Sair"
              >
                <LogOut size={16} />
              </button>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
