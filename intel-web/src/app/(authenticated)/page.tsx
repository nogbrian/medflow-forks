'use client';

import { useState } from 'react';
import { useWorkspaces } from '@/hooks/use-workspaces';
import { useProfiles } from '@/hooks/use-profiles';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatCard } from '@/components/ui/stat-card';
import { EmptyState } from '@/components/ui/empty-state';
import { AddProfileDialog } from '@/components/profiles/add-profile-dialog';
import { Users, FolderKanban, TrendingUp, Plus, Instagram } from 'lucide-react';
import Link from 'next/link';
import { getProxiedImageUrl } from '@/lib/image-proxy';

export default function DashboardPage() {
  const [addProfileOpen, setAddProfileOpen] = useState(false);
  const { data: workspaces, isLoading: workspacesLoading } = useWorkspaces();
  const { data: profiles, isLoading: profilesLoading } = useProfiles();

  const totalProfiles = profiles?.length || 0;
  const totalWorkspaces = workspaces?.length || 0;
  const activeProfiles = profiles?.filter(p => p.is_active).length || 0;

  if (workspacesLoading || profilesLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-48" />
          <div className="grid gap-4 md:grid-cols-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 bg-muted rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Visão geral do monitoramento de perfis</p>
        </div>
        <Button onClick={() => setAddProfileOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Adicionar Perfil
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3 mb-8">
        <StatCard
          title="Total de Workspaces"
          value={totalWorkspaces}
          icon={FolderKanban}
          description="Organizações de clientes"
        />
        <StatCard
          title="Perfis Monitorados"
          value={totalProfiles}
          icon={Users}
          description={`${activeProfiles} ativos`}
        />
        <StatCard
          title="Taxa Média de Engajamento"
          value="--"
          icon={TrendingUp}
          description="Calculado após scraping"
        />
      </div>

      {totalWorkspaces === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <EmptyState
              icon={FolderKanban}
              title="Nenhum workspace criado"
              description="Crie um workspace para organizar seus perfis Instagram por cliente ou projeto."
              action={{
                label: 'Criar Workspace',
                onClick: () => window.location.href = '/workspaces',
              }}
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FolderKanban className="h-5 w-5" />
                Workspaces Recentes
              </CardTitle>
              <CardDescription>Seus workspaces de monitoramento</CardDescription>
            </CardHeader>
            <CardContent>
              {workspaces?.slice(0, 5).map(workspace => (
                <Link
                  key={workspace.id}
                  href={`/workspaces/${workspace.id}`}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-muted transition-colors"
                >
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: workspace.color }}
                  />
                  <div>
                    <p className="font-medium">{workspace.name}</p>
                    {workspace.description && (
                      <p className="text-sm text-muted-foreground">{workspace.description}</p>
                    )}
                  </div>
                </Link>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Instagram className="h-5 w-5 text-pink-500" />
                Perfis Recentes
              </CardTitle>
              <CardDescription>Últimos perfis adicionados</CardDescription>
            </CardHeader>
            <CardContent>
              {profiles?.length === 0 ? (
                <EmptyState
                  icon={Users}
                  title="Nenhum perfil"
                  description="Adicione perfis para começar o monitoramento."
                />
              ) : (
                profiles?.slice(0, 5).map(profile => (
                  <Link
                    key={profile.id}
                    href={`/profiles/${profile.id}`}
                    className="flex items-center gap-3 p-3 rounded-lg hover:bg-muted transition-colors"
                  >
                    {profile.profile_pic_url ? (
                      <img
                        src={getProxiedImageUrl(profile.profile_pic_url) || profile.profile_pic_url}
                        alt={profile.username}
                        className="w-10 h-10 rounded-full"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                        <Users className="h-5 w-5 text-muted-foreground" />
                      </div>
                    )}
                    <div>
                      <p className="font-medium">@{profile.username}</p>
                      <p className="text-sm text-muted-foreground">
                        {profile.followers_count.toLocaleString()} seguidores
                      </p>
                    </div>
                  </Link>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      )}

      <AddProfileDialog open={addProfileOpen} onOpenChange={setAddProfileOpen} />
    </div>
  );
}
