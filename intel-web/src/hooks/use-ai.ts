import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  sendChatMessage,
  generateImage,
  getProviders,
  getConversations,
  getConversation,
  deleteConversation,
  getBrandProfiles,
  getBrandProfile,
  createBrandProfile,
  updateBrandProfile,
  deleteBrandProfile,
  analyzeBrandProfile,
  getFrontierModels,
  compareChatModels,
  searchMemories,
  storeMemory,
  consolidateConversation,
  type ChatRequest,
  type ImageGenerationRequest,
  type BrandProfile,
} from '@/lib/ai-api';

// Query Keys
export const AI_KEYS = {
  providers: ['ai', 'providers'] as const,
  conversations: (workspaceId: string, agentType?: string) =>
    ['ai', 'conversations', workspaceId, agentType] as const,
  conversation: (id: string) => ['ai', 'conversation', id] as const,
  brandProfiles: (workspaceId: string) => ['ai', 'brand-profiles', workspaceId] as const,
  brandProfile: (id: string) => ['ai', 'brand-profile', id] as const,
};

// Providers
export function useProviders() {
  return useQuery({
    queryKey: AI_KEYS.providers,
    queryFn: getProviders,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Chat
export function useChatMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ChatRequest) => sendChatMessage(request),
    onSuccess: (data, variables) => {
      // Invalidate conversations list after new message
      queryClient.invalidateQueries({
        queryKey: AI_KEYS.conversations(variables.workspace_id, variables.agent_type),
      });
      // Invalidate specific conversation if exists
      if (variables.conversation_id) {
        queryClient.invalidateQueries({
          queryKey: AI_KEYS.conversation(variables.conversation_id),
        });
      }
    },
  });
}

// Image Generation
export function useImageGenerationMutation() {
  return useMutation({
    mutationFn: (request: ImageGenerationRequest) => generateImage(request),
  });
}

// Conversations
export function useConversations(workspaceId: string | undefined, agentType?: string) {
  return useQuery({
    queryKey: AI_KEYS.conversations(workspaceId || '', agentType),
    queryFn: () => getConversations(workspaceId!, agentType),
    enabled: !!workspaceId,
  });
}

export function useConversation(id: string | undefined) {
  return useQuery({
    queryKey: AI_KEYS.conversation(id || ''),
    queryFn: () => getConversation(id!),
    enabled: !!id,
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteConversation,
    onSuccess: () => {
      // Invalidate all conversations queries
      queryClient.invalidateQueries({
        predicate: (query) =>
          query.queryKey[0] === 'ai' && query.queryKey[1] === 'conversations',
      });
    },
  });
}

// Brand Profiles
export function useBrandProfiles(workspaceId: string | undefined) {
  return useQuery({
    queryKey: AI_KEYS.brandProfiles(workspaceId || ''),
    queryFn: () => getBrandProfiles(workspaceId!),
    enabled: !!workspaceId,
  });
}

export function useBrandProfile(id: string | undefined) {
  return useQuery({
    queryKey: AI_KEYS.brandProfile(id || ''),
    queryFn: () => getBrandProfile(id!),
    enabled: !!id,
  });
}

export function useCreateBrandProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { workspace_id: string; name: string; description?: string }) =>
      createBrandProfile(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: AI_KEYS.brandProfiles(variables.workspace_id),
      });
    },
  });
}

export function useUpdateBrandProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<BrandProfile> }) =>
      updateBrandProfile(id, data),
    onSuccess: (result) => {
      queryClient.invalidateQueries({
        queryKey: AI_KEYS.brandProfile(result.id),
      });
      queryClient.invalidateQueries({
        queryKey: AI_KEYS.brandProfiles(result.workspace_id),
      });
    },
  });
}

export function useDeleteBrandProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteBrandProfile,
    onSuccess: () => {
      // Invalidate all brand profiles queries
      queryClient.invalidateQueries({
        predicate: (query) =>
          query.queryKey[0] === 'ai' && query.queryKey[1] === 'brand-profiles',
      });
    },
  });
}

export function useAnalyzeBrandProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: analyzeBrandProfile,
    onSuccess: (result) => {
      queryClient.invalidateQueries({
        queryKey: AI_KEYS.brandProfile(result.id),
      });
    },
  });
}

// ============================================================
// Multi-Model Comparison
// ============================================================

export function useFrontierModels() {
  return useQuery({
    queryKey: ['ai', 'frontier-models'] as const,
    queryFn: getFrontierModels,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function useCompareChatModels() {
  return useMutation({
    mutationFn: ({
      workspaceId,
      models,
      message,
      images,
      systemPrompt,
    }: {
      workspaceId: string;
      models: string[];
      message: string;
      images?: string[];
      systemPrompt?: string;
    }) => compareChatModels(workspaceId, models, message, images, systemPrompt),
  });
}

// ============================================================
// Memory & Context
// ============================================================

export function useSearchMemories() {
  return useMutation({
    mutationFn: ({
      workspaceId,
      query,
      limit,
      conversationId,
    }: {
      workspaceId: string;
      query: string;
      limit?: number;
      conversationId?: string;
    }) => searchMemories(workspaceId, query, limit, conversationId),
  });
}

export function useStoreMemory() {
  return useMutation({
    mutationFn: ({
      workspaceId,
      content,
      role,
      conversationId,
      metadata,
    }: {
      workspaceId: string;
      content: string;
      role?: string;
      conversationId?: string;
      metadata?: Record<string, unknown>;
    }) => storeMemory(workspaceId, content, role, conversationId, metadata),
  });
}

export function useConsolidateConversation() {
  return useMutation({
    mutationFn: consolidateConversation,
  });
}
