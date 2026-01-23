"use client";

import { useApi } from "./use-api";
import { fetchLeads, type LeadsResponse } from "@/lib/api";

/**
 * Hook for fetching leads list with optional filters.
 */
export function useLeads(params?: {
  etapa?: string;
  origem?: string;
  limite?: number;
  offset?: number;
}) {
  return useApi<LeadsResponse>(
    () => fetchLeads(params),
    [params?.etapa, params?.origem, params?.limite, params?.offset],
  );
}
