'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Settings, Database, Webhook, Key, Instagram, Loader2, Check, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

export default function SettingsPage() {
  const [sessionCookie, setSessionCookie] = useState('');
  const [hasExistingCookie, setHasExistingCookie] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function checkCookie() {
      try {
        const res = await fetch('/api/settings?key=instagram_session_cookie');
        const data = await res.json();
        if (data.setting?.value) {
          setHasExistingCookie(true);
        }
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    }
    checkCookie();
  }, []);

  const handleSaveCookie = async () => {
    if (!sessionCookie.trim()) {
      toast.error('Insira o cookie sessionid');
      return;
    }

    setSaving(true);
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          key: 'instagram_session_cookie',
          value: sessionCookie.trim(),
        }),
      });

      const data = await res.json();
      if (data.success) {
        toast.success('Cookie salvo com sucesso!');
        setHasExistingCookie(true);
        setSessionCookie('');
      } else {
        toast.error('Erro ao salvar: ' + data.error);
      }
    } catch {
      toast.error('Erro ao salvar cookie');
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveCookie = async () => {
    if (!confirm('Tem certeza que deseja remover o cookie?')) return;

    try {
      const res = await fetch('/api/settings?key=instagram_session_cookie', {
        method: 'DELETE',
      });

      const data = await res.json();
      if (data.success) {
        toast.success('Cookie removido');
        setHasExistingCookie(false);
      } else {
        toast.error('Erro ao remover: ' + data.error);
      }
    } catch {
      toast.error('Erro ao remover cookie');
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Configurações</h1>
        <p className="text-muted-foreground">Gerencie as configurações do sistema</p>
      </div>

      <div className="grid gap-6 max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Instagram className="h-5 w-5 text-pink-500" />
              Instagram Session Cookie
            </CardTitle>
            <CardDescription>
              Cookie de sessão para acessar perfis restritos por idade (21+)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Carregando...
              </div>
            ) : (
              <>
                <div className="flex items-center gap-2 mb-4">
                  {hasExistingCookie ? (
                    <>
                      <Check className="h-4 w-4 text-green-500" />
                      <span className="text-sm text-green-600">Cookie configurado</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="h-4 w-4 text-yellow-500" />
                      <span className="text-sm text-yellow-600">Cookie não configurado</span>
                    </>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="session-cookie">
                    {hasExistingCookie ? 'Atualizar cookie' : 'Adicionar cookie'}
                  </Label>
                  <Input
                    id="session-cookie"
                    type="password"
                    placeholder="Cole o valor do cookie sessionid aqui"
                    value={sessionCookie}
                    onChange={(e) => setSessionCookie(e.target.value)}
                  />
                </div>

                <div className="flex gap-2">
                  <Button onClick={handleSaveCookie} disabled={saving || !sessionCookie.trim()}>
                    {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                    {hasExistingCookie ? 'Atualizar' : 'Salvar'}
                  </Button>
                  {hasExistingCookie && (
                    <Button variant="destructive" onClick={handleRemoveCookie}>
                      Remover
                    </Button>
                  )}
                </div>

                <div className="mt-4 p-4 bg-muted rounded-lg text-sm space-y-2">
                  <p className="font-medium">Como obter o cookie:</p>
                  <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
                    <li>Faça login no Instagram com uma conta 21+ anos</li>
                    <li>Abra DevTools (F12) → Application → Cookies</li>
                    <li>Procure por <code className="bg-background px-1 rounded">sessionid</code></li>
                    <li>Copie o valor (não o nome) e cole aqui</li>
                  </ol>
                  <p className="text-yellow-600 mt-2">
                    O cookie expira periodicamente. Atualize se parar de funcionar.
                  </p>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Banco de Dados
            </CardTitle>
            <CardDescription>Conexão com o PostgreSQL</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Status</Label>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                <span className="text-sm text-muted-foreground">Conectado</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Webhook className="h-5 w-5" />
              n8n Webhooks
            </CardTitle>
            <CardDescription>Configurações de integração com n8n</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="webhook-url">Webhook Base URL</Label>
              <Input
                id="webhook-url"
                value={process.env.NEXT_PUBLIC_N8N_WEBHOOK_URL || 'Não configurado'}
                disabled
              />
            </div>
            <p className="text-sm text-muted-foreground">
              Configure a variável de ambiente <code>N8N_WEBHOOK_BASE_URL</code> para alterar.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              API Keys
            </CardTitle>
            <CardDescription>Chaves de API para integrações</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Apify Token</Label>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${process.env.APIFY_API_TOKEN ? 'bg-green-500' : 'bg-yellow-500'}`} />
                <span className="text-sm text-muted-foreground">
                  {process.env.APIFY_API_TOKEN ? 'Configurado' : 'Não configurado'}
                </span>
              </div>
            </div>
            <p className="text-sm text-muted-foreground">
              Configure a variável de ambiente <code>APIFY_API_TOKEN</code> no servidor.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Informações do Sistema
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Versão</span>
              <span>1.0.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Next.js</span>
              <span>14.x</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Prisma</span>
              <span>5.x</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
