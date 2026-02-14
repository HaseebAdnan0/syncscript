// React Query mutation hook for creating sources

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createSource } from '@/lib/api/sources';
import { toast } from '@/hooks/useToast';
import type { Source, CreateSourceRequest } from '@/lib/types/sources';

/**
 * Hook to create a new source with optimistic updates
 *
 * Creates a source within a vault and invalidates the sources query cache.
 * Shows success/error toast notifications automatically.
 *
 * @returns React Query mutation result with mutate, isLoading, error
 */
export function useAddSourceMutation() {
  const queryClient = useQueryClient();

  return useMutation<Source, Error, CreateSourceRequest>({
    mutationFn: createSource,
    onSuccess: (newSource) => {
      // Invalidate sources query for this vault to refetch with new source
      queryClient.invalidateQueries({
        queryKey: ['sources', newSource.vault],
      });

      // Show success toast
      toast({
        title: 'Source added',
        description: `${newSource.title} has been added successfully.`,
      });
    },
    onError: (error: Error) => {
      // Show error toast
      toast({
        title: 'Failed to add source',
        description: error.message || 'An error occurred while adding the source.',
      });
    },
  });
}
