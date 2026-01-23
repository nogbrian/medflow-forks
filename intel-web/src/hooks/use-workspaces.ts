import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getWorkspaces, getWorkspace, createWorkspace, deleteWorkspace } from '@/lib/api';

export const WORKSPACES_KEY = ['workspaces'] as const;

export function useWorkspaces() {
  return useQuery({
    queryKey: WORKSPACES_KEY,
    queryFn: getWorkspaces,
  });
}

export function useWorkspace(id: string | undefined) {
  return useQuery({
    queryKey: [...WORKSPACES_KEY, id],
    queryFn: () => getWorkspace(id!),
    enabled: !!id,
  });
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createWorkspace,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WORKSPACES_KEY });
    },
  });
}

export function useDeleteWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteWorkspace,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WORKSPACES_KEY });
    },
  });
}
