import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getSources,
  getSource,
  createSource,
  updateSource,
  deleteSource,
} from '@/lib/api/sources';
import type {
  Source,
  CreateSourceRequest,
  UpdateSourceRequest,
  SourcesFilterParams,
} from '@/lib/types/sources';

// Query keys
export const sourceKeys = {
  all: ['sources'] as const,
  lists: () => [...sourceKeys.all, 'list'] as const,
  list: (vaultId: string, filters?: SourcesFilterParams) =>
    [...sourceKeys.lists(), vaultId, filters] as const,
  details: () => [...sourceKeys.all, 'detail'] as const,
  detail: (id: number) => [...sourceKeys.details(), id] as const,
};

/**
 * Fetch all sources for a vault with optional filters
 */
export function useSources(vaultId: string, filters?: SourcesFilterParams) {
  return useQuery<Source[], Error>({
    queryKey: sourceKeys.list(vaultId, filters),
    queryFn: () => getSources(vaultId, filters),
    enabled: !!vaultId,
  });
}

/**
 * Fetch a single source by ID
 */
export function useSource(id: number) {
  return useQuery<Source, Error>({
    queryKey: sourceKeys.detail(id),
    queryFn: () => getSource(id),
    enabled: !!id,
  });
}

/**
 * Create a new source
 */
export function useCreateSource() {
  const queryClient = useQueryClient();

  return useMutation<Source, Error, CreateSourceRequest>({
    mutationFn: createSource,
    onSuccess: () => {
      // Invalidate all source lists for this vault to refetch with new source
      queryClient.invalidateQueries({ queryKey: sourceKeys.lists() });
    },
  });
}

/**
 * Update an existing source
 */
export function useUpdateSource(id: number) {
  const queryClient = useQueryClient();

  return useMutation<Source, Error, UpdateSourceRequest>({
    mutationFn: (data) => updateSource(id, data),
    onSuccess: (updatedSource) => {
      // Update the specific source in cache
      queryClient.setQueryData(sourceKeys.detail(id), updatedSource);
      // Invalidate lists to reflect changes
      queryClient.invalidateQueries({ queryKey: sourceKeys.lists() });
    },
  });
}

/**
 * Delete a source
 */
export function useDeleteSource() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, number>({
    mutationFn: deleteSource,
    onSuccess: (_, deletedId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: sourceKeys.detail(deletedId) });
      // Invalidate lists to reflect deletion
      queryClient.invalidateQueries({ queryKey: sourceKeys.lists() });
    },
  });
}
