import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getExportUrl(
  profileId: string,
  format: 'csv' | 'json' = 'csv',
  filters?: { date_from?: string; date_to?: string }
): string {
  const params = new URLSearchParams({
    profile_id: profileId,
    format,
  });

  if (filters?.date_from) params.append('date_from', filters.date_from);
  if (filters?.date_to) params.append('date_to', filters.date_to);

  return `/api/export?${params}`;
}
