/**
 * AI API client for FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  images?: string[];
}

export interface ChatRequest {
  workspace_id: string;
  conversation_id?: string | null;
  agent_type: 'creative' | 'copywriter';
  provider: 'gemini' | 'openai' | 'xai' | 'anthropic';
  messages: ChatMessage[];
  brand_profile_id?: string | null;
}

// Frontier Models
export interface FrontierModel {
  key: string;
  model_id: string;
  provider: string;
  display_name: string;
  supports_vision: boolean;
  supports_images: boolean;
  available: boolean;
}

export interface ModelsResponse {
  success: boolean;
  models: FrontierModel[];
  total: number;
  available_count: number;
}

// Multi-model comparison
export interface MultiModelResponse {
  model_id: string;
  provider: string;
  display_name: string;
  content: string;
  images?: string[];
  error?: string;
  latency_ms: number;
}

export interface CompareResponse {
  success: boolean;
  responses: MultiModelResponse[];
}

export interface ChatResponse {
  success: boolean;
  message?: string;
  images?: string[];
  conversation_id?: string;
  error?: string;
}

export interface AIConversation {
  id: string;
  workspace_id: string;
  brand_profile_id: string | null;
  title: string | null;
  agent_type: string;
  provider: string;
  system_prompt: string | null;
  context: Record<string, unknown> | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  messages?: AIMessage[];
  message_count?: number;
}

export interface AIMessage {
  id: string;
  conversation_id: string;
  role: string;
  content: string;
  images: string[];
  token_count: number | null;
  created_at: string;
}

export interface BrandProfile {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  color_palette: Record<string, string> | null;
  typography: Record<string, string> | null;
  visual_style: string | null;
  logo_url: string | null;
  brand_manual_url: string | null;
  ai_synthesis: string | null;
  created_at: string;
  updated_at: string;
}

export interface ImageGenerationRequest {
  workspace_id: string;
  conversation_id?: string | null;
  provider: 'gemini' | 'openai' | 'xai';
  style_prompt: string;
  content_prompt: string;
  aspect_ratio: '1:1' | '9:16' | '3:4' | '16:9';
}

export interface ImageGenerationResponse {
  success: boolean;
  image_url?: string;
  image_id?: string;
  error?: string;
}

export interface ProvidersResponse {
  providers: {
    id: string;
    name: string;
    available: boolean;
    supports_chat: boolean;
    supports_images: boolean;
    supports_vision: boolean;
  }[];
}

// Chat API
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ai/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to send message');
  }

  return response.json();
}

// Image Generation API
export async function generateImage(request: ImageGenerationRequest): Promise<ImageGenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ai/generate-image`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to generate image');
  }

  return response.json();
}

// Providers API
export async function getProviders(): Promise<ProvidersResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ai/providers`);

  if (!response.ok) {
    throw new Error('Failed to fetch providers');
  }

  return response.json();
}

// Conversations API
export async function getConversations(
  workspaceId: string,
  agentType?: string
): Promise<{ conversations: AIConversation[] }> {
  const params = new URLSearchParams({ workspace_id: workspaceId });
  if (agentType) params.append('agent_type', agentType);

  const response = await fetch(`${API_BASE_URL}/api/ai/conversations?${params}`);

  if (!response.ok) {
    throw new Error('Failed to fetch conversations');
  }

  return response.json();
}

export async function getConversation(id: string): Promise<AIConversation> {
  const response = await fetch(`${API_BASE_URL}/api/ai/conversations/${id}`);

  if (!response.ok) {
    throw new Error('Failed to fetch conversation');
  }

  return response.json();
}

export async function deleteConversation(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/ai/conversations/${id}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete conversation');
  }
}

// Brand Profiles API
export async function getBrandProfiles(workspaceId: string): Promise<{ profiles: BrandProfile[] }> {
  const response = await fetch(`${API_BASE_URL}/api/ai/brand-profiles?workspace_id=${workspaceId}`);

  if (!response.ok) {
    throw new Error('Failed to fetch brand profiles');
  }

  return response.json();
}

export async function getBrandProfile(id: string): Promise<BrandProfile> {
  const response = await fetch(`${API_BASE_URL}/api/ai/brand-profiles/${id}`);

  if (!response.ok) {
    throw new Error('Failed to fetch brand profile');
  }

  return response.json();
}

export async function createBrandProfile(data: {
  workspace_id: string;
  name: string;
  description?: string;
}): Promise<BrandProfile> {
  const response = await fetch(`${API_BASE_URL}/api/ai/brand-profiles`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to create brand profile');
  }

  return response.json();
}

export async function updateBrandProfile(
  id: string,
  data: Partial<BrandProfile>
): Promise<BrandProfile> {
  const response = await fetch(`${API_BASE_URL}/api/ai/brand-profiles/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to update brand profile');
  }

  return response.json();
}

export async function deleteBrandProfile(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/ai/brand-profiles/${id}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete brand profile');
  }
}

export async function analyzeBrandProfile(id: string): Promise<BrandProfile> {
  const response = await fetch(`${API_BASE_URL}/api/ai/brand-profiles/${id}/analyze`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error('Failed to analyze brand profile');
  }

  return response.json();
}

// ============================================================
// Multi-Model Comparison API
// ============================================================

export async function getFrontierModels(): Promise<ModelsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ai/models`);

  if (!response.ok) {
    throw new Error('Failed to fetch models');
  }

  return response.json();
}

export async function compareChatModels(
  workspaceId: string,
  models: string[],
  message: string,
  images?: string[],
  systemPrompt?: string
): Promise<CompareResponse> {
  const params = new URLSearchParams({
    workspace_id: workspaceId,
    models: models.join(','),
    message,
  });

  if (systemPrompt) params.append('system_prompt', systemPrompt);

  const response = await fetch(`${API_BASE_URL}/api/ai/chat/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      workspace_id: workspaceId,
      models,
      message,
      images,
      system_prompt: systemPrompt,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to compare models');
  }

  return response.json();
}

// ============================================================
// Memory API
// ============================================================

export interface MemoryEntry {
  id: string;
  content: string;
  role: string;
  similarity: number;
  created_at: string | null;
}

export async function searchMemories(
  workspaceId: string,
  query: string,
  limit: number = 10,
  conversationId?: string
): Promise<{ memories: MemoryEntry[]; count: number }> {
  const response = await fetch(`${API_BASE_URL}/api/ai/memory/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      workspace_id: workspaceId,
      query,
      limit,
      conversation_id: conversationId,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to search memories');
  }

  return response.json();
}

export async function storeMemory(
  workspaceId: string,
  content: string,
  role: string = 'knowledge',
  conversationId?: string,
  metadata?: Record<string, unknown>
): Promise<{ success: boolean; memory_id: string | null }> {
  const response = await fetch(`${API_BASE_URL}/api/ai/memory/store`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      workspace_id: workspaceId,
      content,
      role,
      conversation_id: conversationId,
      metadata,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to store memory');
  }

  return response.json();
}

export async function consolidateConversation(
  conversationId: string
): Promise<{ success: boolean; memory_id: string | null }> {
  const response = await fetch(`${API_BASE_URL}/api/ai/conversations/${conversationId}/consolidate`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error('Failed to consolidate conversation');
  }

  return response.json();
}
