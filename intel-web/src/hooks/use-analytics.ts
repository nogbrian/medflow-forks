import { useQuery } from '@tanstack/react-query';
import { getProfileAnalytics } from '@/lib/api';
import type { PostFilters } from '@/types/database';

export const ANALYTICS_KEY = ['analytics'] as const;

export function useAnalytics(
  profileId: string | undefined,
  filters: Partial<PostFilters> = {}
) {
  return useQuery({
    queryKey: [...ANALYTICS_KEY, profileId, filters],
    queryFn: () => getProfileAnalytics(profileId!, filters),
    enabled: !!profileId,
    staleTime: 5 * 60 * 1000,
  });
}
