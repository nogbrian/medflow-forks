'use client';

import { useState } from 'react';
import { useProfiles, useDeleteProfile } from '@/hooks/use-profiles';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { EmptyState } from '@/components/ui/empty-state';
import { AddProfileDialog } from '@/components/profiles/add-profile-dialog';
import { Plus, Trash2, TrendingUp, Instagram } from 'lucide-react';
import Link from 'next/link';
import { toast } from 'sonner';
import { getProxiedImageUrl } from '@/lib/image-proxy';

export default function ProfilesPage() {
  const [addProfileOpen, setAddProfileOpen] = useState(false);

  const { data: profiles, isLoading } = useProfiles();
  const deleteMutation = useDeleteProfile();

  const handleDelete = async (id: string) => {
    if (!confirm('Tem certeza que deseja excluir este perfil?')) return;
    try {
      await deleteMutation.mutateAsync(id);
      toast.success('Perfil excluído!');
    } catch {
      toast.error('Erro ao excluir perfil');
    }
  };

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-48" />
          <div className="grid gap-4 md:grid-cols-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-48 bg-muted rounded" />
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
          <h1 className="text-3xl font-bold">Perfis</h1>
          <p className="text-muted-foreground">Todos os perfis Instagram monitorados</p>
        </div>
        <Button onClick={() => setAddProfileOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Adicionar Perfil
        </Button>
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
                      <p className="font-semibold">{profile.posts_count}</p>
                    </div>
                  </div>
                  {profile.last_scraped_at && (
                    <p className="text-xs text-muted-foreground mt-3">
                      Atualizado em {new Date(profile.last_scraped_at).toLocaleDateString('pt-BR')}
                    </p>
                  )}
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

      <AddProfileDialog open={addProfileOpen} onOpenChange={setAddProfileOpen} />
    </div>
  );
}
