'use client';

import { useState } from 'react';
import { Plus, Palette, MoreVertical, Trash2, Edit, Sparkles, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useWorkspaces } from '@/hooks/use-workspaces';
import {
  useBrandProfiles,
  useCreateBrandProfile,
  useDeleteBrandProfile,
  useAnalyzeBrandProfile,
} from '@/hooks/use-ai';

export default function BrandProfilesPage() {
  const { data: workspaces } = useWorkspaces();
  const workspaceId = workspaces?.[0]?.id;

  const { data: profilesData, isLoading } = useBrandProfiles(workspaceId);
  const createMutation = useCreateBrandProfile();
  const deleteMutation = useDeleteBrandProfile();
  const analyzeMutation = useAnalyzeBrandProfile();

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newProfile, setNewProfile] = useState({ name: '', description: '' });

  const handleCreate = async () => {
    if (!workspaceId || !newProfile.name.trim()) return;

    await createMutation.mutateAsync({
      workspace_id: workspaceId,
      name: newProfile.name,
      description: newProfile.description || undefined,
    });

    setNewProfile({ name: '', description: '' });
    setIsCreateOpen(false);
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Tem certeza que deseja excluir este perfil de marca?')) {
      await deleteMutation.mutateAsync(id);
    }
  };

  const handleAnalyze = async (id: string) => {
    await analyzeMutation.mutateAsync(id);
  };

  const profiles = profilesData?.profiles || [];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Brand Profiles</h1>
          <p className="text-muted-foreground">
            Gerencie a identidade visual dos seus clientes
          </p>
        </div>

        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button className="bg-orange-500 hover:bg-orange-600">
              <Plus className="mr-2 h-4 w-4" />
              Novo Perfil
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Criar Brand Profile</DialogTitle>
              <DialogDescription>
                Adicione um novo perfil de marca para armazenar a identidade visual do cliente.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nome da Marca</Label>
                <Input
                  id="name"
                  value={newProfile.name}
                  onChange={(e) => setNewProfile({ ...newProfile, name: e.target.value })}
                  placeholder="Ex: Clínica Odonto Premium"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Descrição</Label>
                <Textarea
                  id="description"
                  value={newProfile.description}
                  onChange={(e) => setNewProfile({ ...newProfile, description: e.target.value })}
                  placeholder="Descreva brevemente a marca e seu posicionamento..."
                  rows={3}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
                Cancelar
              </Button>
              <Button
                onClick={handleCreate}
                disabled={!newProfile.name.trim() || createMutation.isPending}
                className="bg-orange-500 hover:bg-orange-600"
              >
                {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Criar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : profiles.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Palette className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">Nenhum perfil de marca</h3>
            <p className="text-muted-foreground text-center mb-4">
              Crie seu primeiro perfil de marca para começar a salvar identidades visuais.
            </p>
            <Button
              onClick={() => setIsCreateOpen(true)}
              className="bg-orange-500 hover:bg-orange-600"
            >
              <Plus className="mr-2 h-4 w-4" />
              Criar Primeiro Perfil
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {profiles.map((profile) => (
            <Card key={profile.id} className="group">
              <CardHeader className="flex flex-row items-start justify-between space-y-0">
                <div className="space-y-1">
                  <CardTitle className="text-lg">{profile.name}</CardTitle>
                  <CardDescription className="line-clamp-2">
                    {profile.description || 'Sem descrição'}
                  </CardDescription>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem>
                      <Edit className="mr-2 h-4 w-4" />
                      Editar
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => handleAnalyze(profile.id)}
                      disabled={analyzeMutation.isPending}
                    >
                      <Sparkles className="mr-2 h-4 w-4" />
                      Analisar com AI
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      className="text-destructive"
                      onClick={() => handleDelete(profile.id)}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Excluir
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </CardHeader>
              <CardContent>
                {/* Color Palette Preview */}
                {profile.color_palette && Object.keys(profile.color_palette).length > 0 ? (
                  <div className="flex gap-1 mb-3">
                    {Object.values(profile.color_palette).slice(0, 5).map((color, idx) => (
                      <div
                        key={idx}
                        className="h-6 w-6 rounded-full border"
                        style={{ backgroundColor: color as string }}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="flex gap-1 mb-3">
                    {[1, 2, 3, 4, 5].map((idx) => (
                      <div
                        key={idx}
                        className="h-6 w-6 rounded-full border border-dashed bg-muted"
                      />
                    ))}
                  </div>
                )}

                {/* AI Synthesis Preview */}
                {profile.ai_synthesis ? (
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {profile.ai_synthesis}
                  </p>
                ) : (
                  <p className="text-sm text-muted-foreground italic">
                    Faça upload de materiais e clique em &quot;Analisar com AI&quot; para gerar uma síntese.
                  </p>
                )}

                <div className="mt-4 text-xs text-muted-foreground">
                  Criado em {new Date(profile.created_at).toLocaleDateString('pt-BR')}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
