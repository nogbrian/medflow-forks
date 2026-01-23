"use client";

import { useApi } from "./use-api";
import {
  fetchConversations,
  fetchConversationStats,
  type Conversation,
} from "@/lib/api";

/**
 * Hook for fetching conversations list.
 */
export function useConversations(params?: {
  status?: string;
  page?: number;
}) {
  return useApi<{ data: Conversation[]; meta: Record<string, unknown> }>(
    () => fetchConversations(params),
    [params?.status, params?.page],
  );
}

/**
 * Hook for conversation statistics.
 */
export function useConversationStats() {
  return useApi(fetchConversationStats);
}
