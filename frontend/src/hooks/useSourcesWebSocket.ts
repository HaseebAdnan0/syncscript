import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useVaultSocket } from './useVaultSocket';

interface UseSourcesWebSocketOptions {
  vaultId: string | number;
}

/**
 * Hook to receive real-time source updates within a vault via WebSocket
 *
 * Connects to vault WebSocket channel and listens for source events:
 * - source.created: New source added
 * - source.updated: Source modified
 * - source.deleted: Source removed
 *
 * Automatically invalidates React Query cache on relevant events
 * Includes auto-reconnect with exponential backoff
 *
 * @param vaultId - The ID of the vault to listen to source events for
 */
export function useSourcesWebSocket({ vaultId }: UseSourcesWebSocketOptions) {
  const queryClient = useQueryClient();

  // Convert vaultId to string if it's a number (WebSocket hook expects string)
  const vaultIdStr = typeof vaultId === 'number' ? String(vaultId) : vaultId;

  const { status, addEventListener } = useVaultSocket({ vaultId: vaultIdStr });

  useEffect(() => {
    if (status !== 'connected') return;

    // Helper to invalidate all sources queries for this vault
    // Uses predicate matching to handle different query key formats
    const invalidateSourcesQueries = () => {
      queryClient.invalidateQueries({
        predicate: (query) => {
          const queryKey = query.queryKey;
          // Match ['sources', 'list', vaultId, filters] format from sourceKeys.list()
          // Also match ['sources', vaultId] format from useAddSourceMutation
          if (queryKey[0] !== 'sources') return false;
          const vaultIdStr = String(vaultId);
          // Check position 2 for sourceKeys.list format: ['sources', 'list', vaultId, ...]
          if (queryKey[1] === 'list' && queryKey[2] !== undefined) {
            return String(queryKey[2]) === vaultIdStr;
          }
          // Check position 1 for direct format: ['sources', vaultId, ...]
          return String(queryKey[1]) === vaultIdStr;
        },
      });
    };

    // Listen for source.created events
    const unsubscribeCreated = addEventListener('source.created', () => {
      // Invalidate sources query to fetch fresh data including new source
      invalidateSourcesQueries();
    });

    // Listen for source.updated events
    const unsubscribeUpdated = addEventListener('source.updated', () => {
      // Invalidate sources query to refetch with updated source data
      invalidateSourcesQueries();
    });

    // Listen for source.deleted events
    const unsubscribeDeleted = addEventListener('source.deleted', () => {
      // Invalidate sources query to remove deleted source from list
      invalidateSourcesQueries();
    });

    // Listen for pdf.uploaded events (when PDF processing completes)
    const unsubscribePdfUploaded = addEventListener('pdf.uploaded', () => {
      // Invalidate sources query to show newly created source from PDF upload
      invalidateSourcesQueries();
    });

    // Listen for reconnected events (refetch after reconnection)
    const unsubscribeReconnected = addEventListener('reconnected', () => {
      // Refetch sources after reconnecting to ensure fresh data
      invalidateSourcesQueries();
    });

    // Cleanup all event listeners on unmount or status change
    return () => {
      unsubscribeCreated();
      unsubscribeUpdated();
      unsubscribeDeleted();
      unsubscribePdfUploaded();
      unsubscribeReconnected();
    };
  }, [status, vaultId, addEventListener, queryClient]);

  return { status };
}
