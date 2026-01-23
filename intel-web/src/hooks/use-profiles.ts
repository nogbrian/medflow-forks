import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProfiles, getProfile, getProfileSummaries, deleteProfile } from '@/lib/api';

export const PROFILES_KEY = ['profiles'] as const;

export function useProfiles(workspaceId?: string) {
  return useQuery({
    queryKey: [...PROFILES_KEY, workspaceId],
    queryFn: () => getProfiles(workspaceId),
  });
}

export function useProfile(id: string | undefined) {
  return useQuery({
    queryKey: [...PROFILES_KEY, 'detail', id],
    queryFn: () => getProfile(id!),
    enabled: !!id,
  });
}

export function useProfileSummaries(workspaceId: string | undefined) {
  return useQuery({
    queryKey: [...PROFILES_KEY, 'summaries', workspaceId],
    queryFn: () => getProfileSummaries(workspaceId!),
    enabled: !!workspaceId,
  });
}

export function useDeleteProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROFILES_KEY });
    },
  });
}
