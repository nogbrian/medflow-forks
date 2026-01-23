"use client";

import { useApi } from "./use-api";
import { fetchBookings, fetchAvailability, type BookingsResponse } from "@/lib/api";

/**
 * Hook for fetching bookings list.
 */
export function useBookings(params?: {
  data_inicio?: string;
  data_fim?: string;
  status?: string;
}) {
  return useApi<BookingsResponse>(
    () => fetchBookings(params),
    [params?.data_inicio, params?.data_fim, params?.status],
  );
}

/**
 * Hook for fetching available time slots.
 */
export function useAvailability(params?: {
  data?: string;
  event_type_id?: number;
}) {
  return useApi(
    () => fetchAvailability(params),
    [params?.data, params?.event_type_id],
  );
}
