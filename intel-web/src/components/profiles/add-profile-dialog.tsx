'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTriggerScrape } from '@/hooks/use-scraping';
import { useWorkspaces } from '@/hooks/use-workspaces';
import { toast } from 'sonner';

import {
  Dialog, DialogContent, DialogDescription,
  DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Instagram, AlertCircle, Loader2 } from 'lucide-react';

interface AddProfileDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  workspaceId?: string;
}

export function AddProfileDialog({ open, onOpenChange, workspaceId: defaultWorkspaceId }: AddProfileDialogProps) {
  const router = useRouter();
  const { data: workspaces } = useWorkspaces();
  const triggerScrape = useTriggerScrape();

  const [username, setUsername] = useState('');
  const [workspaceId, setWorkspaceId] = useState(defaultWorkspaceId || '');
  const [saveProfile, setSaveProfile] = useState(true);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!username.trim()) {
      setError('Digite o username do perfil');
      return;
    }

    if (!workspaceId) {
      setError('Selecione um workspace');
      return;
    }

    const cleanUsername = username.replace(/^@/, '').trim().toLowerCase();

    try {
      const result = await triggerScrape.mutateAsync({
        action: 'full',
        username: cleanUsername,
        workspace_id: workspaceId,
        save_profile: saveProfile,
      });

      toast.success('Perfil adicionado!', {
        description: 'O scraping foi iniciado e os dados serão carregados em breve.',
      });

      onOpenChange(false);
      
      if (result.details?.profile_id) {
        router.push(`/profiles/${result.details.profile_id}`);
      }
    } catch (err) {
      setError((err as Error).message || 'Não foi possível adicionar o perfil.');
    }
  };

  const handleClose = () => {
    setUsername('');
    setError('');
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Instagram className="h-5 w-5 text-pink-500" />
            Adicionar Perfil
          </DialogTitle>
          <DialogDescription>
            Digite o username do perfil Instagram que deseja monitorar.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="username">Username</Label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">@</span>
                <Input
                  id="username"
                  placeholder="exemplo"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="pl-8"
                  autoComplete="off"
                  autoFocus
                />
              </div>
            </div>

            {!defaultWorkspaceId && (
              <div className="grid gap-2">
                <Label htmlFor="workspace">Workspace</Label>
                <Select value={workspaceId} onValueChange={setWorkspaceId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione um workspace" />
                  </SelectTrigger>
                  <SelectContent>
                    {workspaces?.map((workspace) => (
                      <SelectItem key={workspace.id} value={workspace.id}>
                        <span className="flex items-center gap-2">
                          <span
                            className="w-2 h-2 rounded-full"
                            style={{ backgroundColor: workspace.color }}
                          />
                          {workspace.name}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="flex items-center space-x-2">
              <Checkbox
                id="save-profile"
                checked={saveProfile}
                onCheckedChange={(checked) => setSaveProfile(checked as boolean)}
              />
              <Label htmlFor="save-profile" className="text-sm font-normal">
                Salvar para monitoramento contínuo
              </Label>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancelar
            </Button>
            <Button type="submit" disabled={triggerScrape.isPending}>
              {triggerScrape.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Analisando...
                </>
              ) : (
                'Analisar Perfil'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
