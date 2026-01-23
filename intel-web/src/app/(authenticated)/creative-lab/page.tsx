'use client';

import { useState } from 'react';
import { MessageSquare, Zap } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ChatInterface } from '@/components/creative-lab/chat-interface';
import { ConversationList } from '@/components/creative-lab/conversation-list';
import { ModelComparison } from '@/components/creative-lab/model-comparison';

export default function CreativeLabPage() {
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'chat' | 'compare'>('chat');

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Conversation List Sidebar */}
      <div className="w-72 border-r bg-muted/30 overflow-hidden flex flex-col">
        <div className="p-4 border-b">
          <h2 className="font-semibold text-lg">Creative Lab</h2>
          <p className="text-sm text-muted-foreground">Crie conteúdo visual com AI</p>
        </div>

        {/* Mode Tabs */}
        <div className="p-3 border-b">
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'chat' | 'compare')}>
            <TabsList className="w-full">
              <TabsTrigger value="chat" className="flex-1">
                <MessageSquare className="h-4 w-4 mr-1" />
                Chat
              </TabsTrigger>
              <TabsTrigger value="compare" className="flex-1">
                <Zap className="h-4 w-4 mr-1" />
                Comparar
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {activeTab === 'chat' && (
          <ConversationList
            agentType="creative"
            selectedId={selectedConversationId}
            onSelect={setSelectedConversationId}
          />
        )}

        {activeTab === 'compare' && (
          <div className="p-4 text-sm text-muted-foreground">
            <p>Compare respostas de múltiplos modelos de AI simultaneamente.</p>
            <ul className="mt-2 space-y-1 list-disc list-inside">
              <li>GPT-5.2 (OpenAI)</li>
              <li>Claude Opus 4.5 (Anthropic)</li>
              <li>Gemini 3 (Google)</li>
              <li>Grok 4 (xAI)</li>
            </ul>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="flex-1">
        {activeTab === 'chat' ? (
          <ChatInterface
            agentType="creative"
            conversationId={selectedConversationId}
            onConversationCreated={setSelectedConversationId}
          />
        ) : (
          <ModelComparison />
        )}
      </div>
    </div>
  );
}
