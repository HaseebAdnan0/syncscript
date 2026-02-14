'use client';

import { useCallback, useEffect, useRef } from 'react';
import { useQueryClient, type QueryKey } from '@tanstack/react-query';
import { useVaultSocket } from './useVaultSocket';

interface UseRealtimeUpdatesOptions<TData, TVariables> {
  vaultId: string;
  queryKey: QueryKey;
  mutation?: {
    mutationFn: (variables: TVariables) => Promise<TData>;
    onMutate?: (variables: TVariables) => TData | void;
  };
  events: {
    success: string; // e.g., 'source.created'
    error: string;   // e.g., 'source.error'
  };
}

interface UseRealtimeUpdatesReturn<TData, TVariables> {
  optimisticUpdate: (variables: TVariables, optimisticData?: TData) => Promise<void>;
}

/**
 * Hook for handling optimistic UI updates with WebSocket reconciliation.
 *
 * Flow:
 * 1. User action triggers optimisticUpdate()
 * 2. Cache is immediately updated with optimistic data
 * 3. Mutation is sent to server
 * 4. WebSocket confirms/rejects via success/error events
 * 5. Cache is reconciled with server state or rolled back
 */
export function useRealtimeUpdates<TData = any, TVariables = any>(
  options: UseRealtimeUpdatesOptions<TData, TVariables>
): UseRealtimeUpdatesReturn<TData, TVariables> {
  const { vaultId, queryKey, mutation, events } = options;
  const queryClient = useQueryClient();
  const { send, addEventListener } = useVaultSocket({ vaultId });

  // Store optimistic updates in-flight to track reconciliation
  const pendingUpdatesRef = useRef<Map<string, { previousData: any; variables: TVariables }>>(new Map());

  /**
   * Optimistically update the cache, send mutation, and wait for WebSocket confirmation
   */
  const optimisticUpdate = useCallback(
    async (variables: TVariables, optimisticData?: TData) => {
      // Generate unique ID for this update
      const updateId = `${Date.now()}-${Math.random()}`;

      // Snapshot previous data for rollback
      const previousData = queryClient.getQueryData(queryKey);

      // Apply optimistic update to cache
      if (optimisticData) {
        queryClient.setQueryData(queryKey, optimisticData);
      } else if (mutation?.onMutate) {
        const result = mutation.onMutate(variables);
        if (result !== undefined) {
          queryClient.setQueryData(queryKey, result);
        }
      }

      // Track this update for reconciliation
      pendingUpdatesRef.current.set(updateId, { previousData, variables });

      try {
        // Send mutation to server if provided
        if (mutation?.mutationFn) {
          await mutation.mutationFn(variables);
        }

        // Send WebSocket event for real-time broadcast
        send('optimistic_update', { updateId, variables });
      } catch (error) {
        // Rollback on immediate error
        queryClient.setQueryData(queryKey, previousData);
        pendingUpdatesRef.current.delete(updateId);
        throw error;
      }
    },
    [queryKey, queryClient, mutation, send]
  );

  // Handle WebSocket success event (reconcile with server state)
  useEffect(() => {
    const handleSuccess = () => {
      // Invalidate query to fetch fresh server state
      queryClient.invalidateQueries({ queryKey });

      // Clear pending updates (success means server accepted the change)
      // Note: We invalidate instead of directly setting data to ensure
      // we get the authoritative server state, not just echoing our optimistic update
      pendingUpdatesRef.current.clear();
    };

    const cleanup = addEventListener(events.success, handleSuccess);
    return cleanup;
  }, [addEventListener, events.success, queryClient, queryKey]);

  // Handle WebSocket error event (rollback optimistic update)
  useEffect(() => {
    const handleError = (data: any) => {
      // Find the pending update that failed (if we tracked it)
      const updateId = data?.updateId;
      if (updateId && pendingUpdatesRef.current.has(updateId)) {
        const { previousData } = pendingUpdatesRef.current.get(updateId)!;

        // Rollback to previous state
        queryClient.setQueryData(queryKey, previousData);
        pendingUpdatesRef.current.delete(updateId);
      } else {
        // Generic error - invalidate to refetch clean state
        queryClient.invalidateQueries({ queryKey });
      }
    };

    on(events.error, handleError);
    return () => {
      off(events.error, handleError);
    };
  }, [on, off, events.error, queryClient, queryKey]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      pendingUpdatesRef.current.clear();
    };
  }, []);

  return {
    optimisticUpdate,
  };
}
