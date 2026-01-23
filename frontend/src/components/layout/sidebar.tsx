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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth/auth-provider";

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

        {/* Footer - User & Logout */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-graphite bg-white">
          {user && (
            <div className="flex items-center justify-between">
              <div className="min-w-0">
                <span className="block text-xs font-medium truncate">
                  {user.name}
                </span>
                <span className="block font-mono text-[10px] text-steel truncate">
                  {user.email}
                </span>
              </div>
              <button
                onClick={logout}
                className="p-2 text-steel hover:text-red-600 transition-colors flex-shrink-0"
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
