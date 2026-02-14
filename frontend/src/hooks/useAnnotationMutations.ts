import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createAnnotation, createReply, deleteAnnotation } from '@/lib/api/annotations';
import { toast } from '@/hooks/useToast';
import type { Annotation } from '@/lib/types/annotations';

interface CreateAnnotationRequest {
  sourceId: number;
  text: string;
  pageNumber?: number;
}

interface CreateReplyRequest {
  annotationId: number;
  text: string;
}

interface MutationContext {
  previousAnnotations?: Annotation[];
}

// Create annotation mutation
export function useCreateAnnotation() {
  const queryClient = useQueryClient();

  return useMutation<Annotation, Error, CreateAnnotationRequest, MutationContext>({
    mutationFn: ({ sourceId, text, pageNumber }) =>
      createAnnotation({ source: sourceId, text, pageNumber }),
    onMutate: async (variables) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['annotations', variables.sourceId] });

      // Snapshot previous value
      const previousAnnotations = queryClient.getQueryData<Annotation[]>([
        'annotations',
        variables.sourceId,
      ]);

      // Optimistic update
      const optimisticAnnotation: Annotation = {
        id: Date.now(), // Temporary ID
        source: variables.sourceId,
        text: variables.text,
        pageNumber: variables.pageNumber,
        author: {
          id: 0, // Will be replaced by server response
          username: 'You',
          email: '',
        },
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        replies: [],
      };

      queryClient.setQueryData<Annotation[]>(
        ['annotations', variables.sourceId],
        (old) => [optimisticAnnotation, ...(old || [])]
      );

      return { previousAnnotations };
    },
    onError: (error, variables, context) => {
      // Rollback on error
      if (context?.previousAnnotations) {
        queryClient.setQueryData(
          ['annotations', variables.sourceId],
          context.previousAnnotations
        );
      }
      toast({
        title: 'Error',
        description: error.message || 'Failed to create annotation',
      });
    },
    onSuccess: (_data, variables) => {
      // Invalidate to get server response
      queryClient.invalidateQueries({ queryKey: ['annotations', variables.sourceId] });
      toast({
        title: 'Success',
        description: 'Annotation added successfully',
      });
    },
  });
}

// Create reply mutation
export function useCreateReply() {
  const queryClient = useQueryClient();

  return useMutation<Annotation, Error, CreateReplyRequest & { sourceId: number }, MutationContext>({
    mutationFn: ({ annotationId, text }) => createReply({ annotation: annotationId, text }),
    onMutate: async (variables) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['annotations', variables.sourceId] });

      // Snapshot previous value
      const previousAnnotations = queryClient.getQueryData<Annotation[]>([
        'annotations',
        variables.sourceId,
      ]);

      // Optimistic update - Note: createReply returns full Annotation with updated replies
      // We'll just invalidate on success instead of complex optimistic update

      return { previousAnnotations };
    },
    onError: (error, variables, context) => {
      // Rollback on error
      if (context?.previousAnnotations) {
        queryClient.setQueryData(
          ['annotations', variables.sourceId],
          context.previousAnnotations
        );
      }
      toast({
        title: 'Error',
        description: error.message || 'Failed to create reply',
      });
    },
    onSuccess: (_data, variables) => {
      // Invalidate to get server response
      queryClient.invalidateQueries({ queryKey: ['annotations', variables.sourceId] });
      toast({
        title: 'Success',
        description: 'Reply added successfully',
      });
    },
  });
}

// Delete annotation mutation
export function useDeleteAnnotation() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, { annotationId: number; sourceId: number }, MutationContext>({
    mutationFn: ({ annotationId }) => deleteAnnotation(annotationId),
    onMutate: async (variables) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['annotations', variables.sourceId] });

      // Snapshot previous value
      const previousAnnotations = queryClient.getQueryData<Annotation[]>([
        'annotations',
        variables.sourceId,
      ]);

      // Optimistic update
      queryClient.setQueryData<Annotation[]>(
        ['annotations', variables.sourceId],
        (old) => old?.filter((annotation) => annotation.id !== variables.annotationId) || []
      );

      return { previousAnnotations };
    },
    onError: (error, variables, context) => {
      // Rollback on error
      if (context?.previousAnnotations) {
        queryClient.setQueryData(
          ['annotations', variables.sourceId],
          context.previousAnnotations
        );
      }
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete annotation',
      });
    },
    onSuccess: (_data, variables) => {
      // Invalidate to get server response
      queryClient.invalidateQueries({ queryKey: ['annotations', variables.sourceId] });
      toast({
        title: 'Success',
        description: 'Annotation deleted successfully',
      });
    },
  });
}
