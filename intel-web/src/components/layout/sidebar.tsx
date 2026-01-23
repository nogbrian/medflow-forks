'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Users,
  FolderKanban,
  Settings,
  Sparkles,
  PenLine,
  Palette,
  LogOut,
  ArrowLeft,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Workspaces', href: '/workspaces', icon: FolderKanban },
  { name: 'Perfis Instagram', href: '/profiles', icon: Users },
  { name: 'Creative Lab', href: '/creative-lab', icon: Sparkles },
  { name: 'Copywriter', href: '/copywriter', icon: PenLine },
  { name: 'Brand Profiles', href: '/brand-profiles', icon: Palette },
  { name: 'Configurações', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  const handleLogout = () => {
    // Clear the shared auth cookie and redirect to MedFlow login
    document.cookie = 'medflow_token=; path=/; domain=.trafegoparaconsultorios.com.br; max-age=0';
    window.location.href = 'https://medflow.trafegoparaconsultorios.com.br/login';
  };

  return (
    <div className="flex h-full w-64 flex-col bg-card border-r">
      <div className="flex h-16 items-center gap-2 px-6 border-b">
        <Sparkles className="h-6 w-6 text-orange-500" />
        <span className="font-semibold text-lg">Viral Finder</span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href || 
            (item.href !== '/' && pathname.startsWith(item.href));
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="border-t p-4 space-y-3">
        <a
          href="https://medflow.trafegoparaconsultorios.com.br"
          className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Voltar ao MedFlow
        </a>
        <Button
          variant="ghost"
          className="w-full justify-start text-muted-foreground hover:text-foreground"
          onClick={handleLogout}
        >
          <LogOut className="h-4 w-4 mr-2" />
          Sair
        </Button>
      </div>
    </div>
  );
}
