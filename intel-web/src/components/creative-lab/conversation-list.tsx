'use client';

import { useState } from 'react';
import { MessageSquare, Plus, Trash2, MoreVertical, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { useWorkspaces } from '@/hooks/use-workspaces';
import { useConversations, useDeleteConversation } from '@/hooks/use-ai';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface ConversationListProps {
  agentType: 'creative' | 'copywriter';
  selectedId: string | null;
  onSelect: (id: string | null) => void;
}

export function ConversationList({ agentType, selectedId, onSelect }: ConversationListProps) {
  const { data: workspaces } = useWorkspaces();
  const workspaceId = workspaces?.[0]?.id;

  const { data: conversationsData, isLoading } = useConversations(workspaceId, agentType);
  const deleteMutation = useDeleteConversation();

  const conversations = conversationsData?.conversations || [];

  const handleNewConversation = () => {
    onSelect(null);
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('Deseja excluir esta conversa?')) {
      await deleteMutation.mutateAsync(id);
      if (selectedId === id) {
        onSelect(null);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* New Conversation Button */}
      <div className="p-3">
        <Button
          variant="outline"
          className="w-full justify-start"
          onClick={handleNewConversation}
        >
          <Plus className="mr-2 h-4 w-4" />
          Nova conversa
        </Button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-auto">
        {conversations.length === 0 ? (
          <div className="px-4 py-8 text-center text-muted-foreground">
            <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">Nenhuma conversa ainda</p>
          </div>
        ) : (
          <div className="space-y-1 px-2">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                className={cn(
                  'group flex items-center gap-2 rounded-lg px-3 py-2 cursor-pointer transition-colors',
                  selectedId === conversation.id
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-muted'
                )}
                onClick={() => onSelect(conversation.id)}
              >
                <MessageSquare className="h-4 w-4 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="truncate text-sm font-medium">
                    {conversation.title || 'Nova conversa'}
                  </div>
                  <div
                    className={cn(
                      'text-xs truncate',
                      selectedId === conversation.id
                        ? 'text-primary-foreground/70'
                        : 'text-muted-foreground'
                    )}
                  >
                    {formatDistanceToNow(new Date(conversation.updated_at), {
                      addSuffix: true,
                      locale: ptBR,
                    })}
                  </div>
                </div>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className={cn(
                        'h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity',
                        selectedId === conversation.id && 'opacity-100'
                      )}
                      onClick={(e) => e.stopPropagation()}
                    >
                      <MoreVertical className="h-3 w-3" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      className="text-destructive"
                      onClick={(e) => handleDelete(conversation.id, e)}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Excluir
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
