'use client';

import { use, useState } from 'react';
import { useWorkspace } from '@/hooks/use-workspaces';
import { useProfileSummaries, useDeleteProfile } from '@/hooks/use-profiles';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { EmptyState } from '@/components/ui/empty-state';
import { AddProfileDialog } from '@/components/profiles/add-profile-dialog';
import { ArrowLeft, Plus, Trash2, Users, TrendingUp, Instagram } from 'lucide-react';
import Link from 'next/link';
import { toast } from 'sonner';
import { getProxiedImageUrl } from '@/lib/image-proxy';

export default function WorkspaceDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [addProfileOpen, setAddProfileOpen] = useState(false);

  const { data: workspace, isLoading: workspaceLoading } = useWorkspace(id);
  const { data: profiles, isLoading: profilesLoading } = useProfileSummaries(id);
  const deleteMutation = useDeleteProfile();

  const handleDelete = async (profileId: string) => {
    if (!confirm('Tem certeza que deseja excluir este perfil?')) return;
    try {
      await deleteMutation.mutateAsync(profileId);
      toast.success('Perfil excluído!');
    } catch {
      toast.error('Erro ao excluir perfil');
    }
  };

  if (workspaceLoading || profilesLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-48" />
          <div className="grid gap-4 md:grid-cols-2">
            {[1, 2].map(i => (
              <div key={i} className="h-48 bg-muted rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!workspace) {
    return (
      <div className="p-8">
        <EmptyState
          icon={Users}
          title="Workspace não encontrado"
          description="O workspace solicitado não existe."
          action={{ label: 'Voltar', onClick: () => window.history.back() }}
        />
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex items-center gap-4 mb-8">
        <Link href="/workspaces">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex items-center gap-3">
          <div
            className="w-5 h-5 rounded-full"
            style={{ backgroundColor: workspace.color }}
          />
          <div>
            <h1 className="text-3xl font-bold">{workspace.name}</h1>
            {workspace.description && (
              <p className="text-muted-foreground">{workspace.description}</p>
            )}
          </div>
        </div>
        <div className="ml-auto">
          <Button onClick={() => setAddProfileOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Adicionar Perfil
          </Button>
        </div>
      </div>

      {profiles?.length === 0 ? (
        <EmptyState
          icon={Instagram}
          title="Nenhum perfil"
          description="Adicione perfis Instagram para começar a monitorar."
          action={{ label: 'Adicionar Perfil', onClick: () => setAddProfileOpen(true) }}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {profiles?.map(profile => (
            <Card key={profile.id} className="group relative">
              <Link href={`/profiles/${profile.id}`}>
                <CardHeader>
                  <div className="flex items-center gap-3">
                    {profile.profile_pic_url ? (
                      <img
                        src={getProxiedImageUrl(profile.profile_pic_url) || profile.profile_pic_url}
                        alt={profile.username}
                        className="w-12 h-12 rounded-full"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                        <Instagram className="h-6 w-6" />
                      </div>
                    )}
                    <div>
                      <CardTitle className="text-lg flex items-center gap-2">
                        @{profile.username}
                        {profile.is_verified && (
                          <Badge variant="secondary" className="text-xs">✓</Badge>
                        )}
                      </CardTitle>
                      {profile.full_name && (
                        <CardDescription>{profile.full_name}</CardDescription>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Seguidores</p>
                      <p className="font-semibold">{profile.followers_count.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Posts</p>
                      <p className="font-semibold">{profile.total_posts}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Reels</p>
                      <p className="font-semibold">{profile.total_reels}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground flex items-center gap-1">
                        <TrendingUp className="h-3 w-3" />
                        Engagement
                      </p>
                      <p className="font-semibold">
                        {profile.avg_engagement_rate.toFixed(2)}%
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Link>
              <Button
                variant="ghost"
                size="icon"
                className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => handleDelete(profile.id)}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </Card>
          ))}
        </div>
      )}

      <AddProfileDialog
        open={addProfileOpen}
        onOpenChange={setAddProfileOpen}
        workspaceId={id}
      />
    </div>
  );
}
