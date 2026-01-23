'use client';

import { useState } from 'react';
import { useWorkspaces, useCreateWorkspace, useDeleteWorkspace } from '@/hooks/use-workspaces';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { EmptyState } from '@/components/ui/empty-state';
import { FolderKanban, Plus, Trash2, Users } from 'lucide-react';
import Link from 'next/link';
import { toast } from 'sonner';

export default function WorkspacesPage() {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [color, setColor] = useState('#6366f1');

  const { data: workspaces, isLoading } = useWorkspaces();
  const createMutation = useCreateWorkspace();
  const deleteMutation = useDeleteWorkspace();

  const handleCreate = async () => {
    if (!name.trim()) return;
    try {
      await createMutation.mutateAsync({ name, description, color });
      toast.success('Workspace criado!');
      setOpen(false);
      setName('');
      setDescription('');
    } catch {
      toast.error('Erro ao criar workspace');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Tem certeza que deseja excluir este workspace?')) return;
    try {
      await deleteMutation.mutateAsync(id);
      toast.success('Workspace excluído!');
    } catch {
      toast.error('Erro ao excluir workspace');
    }
  };

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-48" />
          <div className="grid gap-4 md:grid-cols-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-40 bg-muted rounded" />
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
          <h1 className="text-3xl font-bold">Workspaces</h1>
          <p className="text-muted-foreground">Organize seus perfis por cliente ou projeto</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Novo Workspace
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Criar Workspace</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nome</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="Ex: Cliente XYZ"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Descrição</Label>
                <Input
                  id="description"
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="Opcional"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="color">Cor</Label>
                <div className="flex gap-2">
                  <Input
                    id="color"
                    type="color"
                    value={color}
                    onChange={e => setColor(e.target.value)}
                    className="w-16 h-10 p-1"
                  />
                  <Input
                    value={color}
                    onChange={e => setColor(e.target.value)}
                    className="flex-1"
                  />
                </div>
              </div>
              <Button onClick={handleCreate} className="w-full" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Criando...' : 'Criar Workspace'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {workspaces?.length === 0 ? (
        <EmptyState
          icon={FolderKanban}
          title="Nenhum workspace"
          description="Crie seu primeiro workspace para organizar perfis."
          action={{ label: 'Criar Workspace', onClick: () => setOpen(true) }}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {workspaces?.map(workspace => (
            <Card key={workspace.id} className="group relative">
              <Link href={`/workspaces/${workspace.id}`}>
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: workspace.color }}
                    />
                    <CardTitle className="text-lg">{workspace.name}</CardTitle>
                  </div>
                  {workspace.description && (
                    <CardDescription>{workspace.description}</CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Users className="h-4 w-4" />
                    <span>Ver perfis</span>
                  </div>
                </CardContent>
              </Link>
              <Button
                variant="ghost"
                size="icon"
                className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => handleDelete(workspace.id)}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
