'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Trash2, Paperclip, Square, Sparkles, X, Palette } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { MessageBubble } from './message-bubble';
import { ProviderSelector } from './provider-selector';
import { useWorkspaces } from '@/hooks/use-workspaces';
import { useBrandProfiles } from '@/hooks/use-ai';
import { sendChatMessage } from '@/lib/ai-api';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  images?: string[];
  isThinking?: boolean;
}

interface ChatInterfaceProps {
  agentType: 'creative' | 'copywriter';
  conversationId: string | null;
  onConversationCreated: (id: string) => void;
}

const WELCOME_MESSAGES = {
  creative: `### Creative Lab

Olá! Sou seu **Diretor de Criação**. Estou aqui para criar conteúdo visual incrível.

**Como começar:**
1. Descreva o conteúdo que você quer criar
2. Envie referências visuais (opcional)
3. Escolha o formato: Feed, Stories ou Carrossel`,

  copywriter: `### Copywriter Elite

Olá! Sou seu **Copywriter Sênior** com 20+ anos de experiência em conversão.

**Comandos rápidos:**
- \`/objecoes\` - Quebrar objeções de vendas
- \`/icp\` - Definir cliente ideal
- \`/copy\` - Criar copy persuasiva
- \`/landing\` - Otimizar landing page

Ou simplesmente descreva o que você precisa.`,
};

export function ChatInterface({ agentType, conversationId, onConversationCreated }: ChatInterfaceProps) {
  const { data: workspaces } = useWorkspaces();
  const workspaceId = workspaces?.[0]?.id;

  // Brand Profiles
  const { data: brandProfilesData } = useBrandProfiles(workspaceId);
  const brandProfiles = brandProfilesData?.profiles || [];

  const [messages, setMessages] = useState<Message[]>([
    { id: 'welcome', role: 'assistant', content: WELCOME_MESSAGES[agentType] },
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [previewImages, setPreviewImages] = useState<string[]>([]);
  const [provider, setProvider] = useState<'gemini' | 'openai' | 'xai' | 'anthropic'>('openai');
  const [selectedBrandProfileId, setSelectedBrandProfileId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const maxHeight = 200;
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, maxHeight)}px`;
    }
  }, [inputText]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    Array.from(e.target.files).forEach((file) => {
      if (!file.type.startsWith('image/')) return;
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewImages((prev) => [...prev, reader.result as string]);
      };
      reader.readAsDataURL(file);
    });
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData.items;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        const blob = items[i].getAsFile();
        if (blob) {
          const reader = new FileReader();
          reader.onloadend = () => {
            setPreviewImages((prev) => [...prev, reader.result as string]);
          };
          reader.readAsDataURL(blob);
        }
      }
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    if (window.confirm('Deseja limpar o histórico e iniciar uma nova conversa?')) {
      setMessages([{ id: 'welcome', role: 'assistant', content: WELCOME_MESSAGES[agentType] }]);
    }
  };

  const handleSendMessage = async () => {
    if ((!inputText.trim() && previewImages.length === 0) || isLoading || !workspaceId) return;

    abortControllerRef.current = new AbortController();

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputText,
      images: previewImages.length > 0 ? [...previewImages] : undefined,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setPreviewImages([]);
    setIsLoading(true);

    // Add thinking indicator
    const thinkingId = `thinking-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { id: thinkingId, role: 'assistant', content: '', isThinking: true },
    ]);

    try {
      const data = await sendChatMessage({
        workspace_id: workspaceId,
        conversation_id: conversationId,
        agent_type: agentType,
        provider,
        brand_profile_id: selectedBrandProfileId,
        messages: [{ role: 'user', content: inputText, images: previewImages.length > 0 ? previewImages : undefined }],
      });

      // Remove thinking indicator
      setMessages((prev) => prev.filter((m) => m.id !== thinkingId));

      if (data.success) {
        if (data.conversation_id && !conversationId) {
          onConversationCreated(data.conversation_id);
        }

        setMessages((prev) => [
          ...prev,
          {
            id: `response-${Date.now()}`,
            role: 'assistant',
            content: data.message || 'Sem resposta',
            images: data.images,
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: `error-${Date.now()}`,
            role: 'assistant',
            content: `Erro: ${data.error || 'Erro desconhecido'}`,
          },
        ]);
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido';
      if (errorMessage === 'AbortError') return;

      setMessages((prev) => prev.filter((m) => m.id !== thinkingId));
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `Erro ao processar mensagem: ${errorMessage}`,
        },
      ]);
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full bg-muted/20">
      {/* Header */}
      <div className="border-b bg-background px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-orange-500" />
          <span className="font-medium">
            {agentType === 'creative' ? 'Creative Lab' : 'Copywriter Elite'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* Brand Profile Selector */}
          <Select
            value={selectedBrandProfileId || 'none'}
            onValueChange={(v) => setSelectedBrandProfileId(v === 'none' ? null : v)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue>
                <span className="flex items-center gap-2">
                  <Palette className="h-4 w-4" />
                  {selectedBrandProfileId
                    ? brandProfiles.find((p) => p.id === selectedBrandProfileId)?.name || 'Marca'
                    : 'Sem marca'}
                </span>
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">
                <span className="text-muted-foreground">Sem marca vinculada</span>
              </SelectItem>
              {brandProfiles.map((profile) => (
                <SelectItem key={profile.id} value={profile.id}>
                  <div>
                    <div className="font-medium">{profile.name}</div>
                    {profile.description && (
                      <div className="text-xs text-muted-foreground truncate max-w-[200px]">
                        {profile.description}
                      </div>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <ProviderSelector value={provider} onChange={setProvider} />
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t bg-background p-4">
        {/* Preview Images */}
        {previewImages.length > 0 && (
          <div className="mb-3 flex gap-2 overflow-x-auto pb-2">
            {previewImages.map((img, idx) => (
              <div key={idx} className="relative group">
                <img src={img} alt="Preview" className="h-16 w-auto rounded border" />
                <button
                  onClick={() => setPreviewImages((prev) => prev.filter((_, i) => i !== idx))}
                  className="absolute -top-1 -right-1 bg-destructive text-destructive-foreground rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X size={12} />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="flex items-end gap-2">
          {/* Action buttons */}
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleClearChat}
              title="Limpar conversa"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => fileInputRef.current?.click()}
              title="Adicionar imagem"
            >
              <Paperclip className="h-4 w-4" />
            </Button>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            className="hidden"
            onChange={handleFileUpload}
          />

          {/* Text input */}
          <div className="flex-1">
            <textarea
              ref={textareaRef}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              onPaste={handlePaste}
              disabled={isLoading}
              placeholder={isLoading ? 'Aguarde...' : 'Digite sua mensagem...'}
              className="w-full resize-none rounded-lg border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
              rows={1}
              style={{ minHeight: '40px', maxHeight: '200px' }}
            />
          </div>

          {/* Send/Stop button */}
          {isLoading ? (
            <Button variant="destructive" size="icon" onClick={handleStop}>
              <Square className="h-4 w-4" />
            </Button>
          ) : (
            <Button
              size="icon"
              onClick={handleSendMessage}
              disabled={!inputText.trim() && previewImages.length === 0}
              className="bg-orange-500 hover:bg-orange-600"
            >
              <Send className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
