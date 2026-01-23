'use client';

import { useState } from 'react';
import { ChatInterface } from '@/components/creative-lab/chat-interface';

export default function CopywriterPage() {
  const [conversationId, setConversationId] = useState<string | null>(null);

  return (
    <div className="h-[calc(100vh-4rem)]">
      <ChatInterface
        agentType="copywriter"
        conversationId={conversationId}
        onConversationCreated={setConversationId}
      />
    </div>
  );
}
