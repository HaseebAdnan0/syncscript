// React Query hooks for annotations

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getAnnotations,
  createAnnotation,
  updateAnnotation,
  deleteAnnotation,
} from '@/lib/api/annotations';
import type {
  Annotation,
  CreateAnnotationRequest,
  UpdateAnnotationRequest,
} from '@/lib/types/annotations';

/**
 * Hook to fetch all annotations for a source
 */
export function useAnnotations(sourceId: number) {
  return useQuery({
    queryKey: ['annotations', sourceId],
    queryFn: () => getAnnotations(sourceId),
    enabled: !!sourceId,
  });
}

/**
 * Hook to create a new annotation
 */
export function useCreateAnnotation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateAnnotationRequest) => createAnnotation(data),
    onSuccess: (_, variables) => {
      // Invalidate annotations list for this source
      queryClient.invalidateQueries({ queryKey: ['annotations', variables.source] });
    },
  });
}

/**
 * Hook to update an annotation
 */
export function useUpdateAnnotation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateAnnotationRequest }) =>
      updateAnnotation(id, data),
    onSuccess: (annotation) => {
      // Invalidate annotations list
      queryClient.invalidateQueries({ queryKey: ['annotations', annotation.source] });
    },
  });
}

/**
 * Hook to delete an annotation
 */
export function useDeleteAnnotation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, sourceId }: { id: number; sourceId: number }) => deleteAnnotation(id),
    onSuccess: (_, variables) => {
      // Invalidate annotations list
      queryClient.invalidateQueries({ queryKey: ['annotations', variables.sourceId] });
    },
  });
}
