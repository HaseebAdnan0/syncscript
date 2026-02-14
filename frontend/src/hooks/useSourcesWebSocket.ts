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

    // Listen for source.created events
    const unsubscribeCreated = addEventListener('source.created', () => {
      // Invalidate sources query to fetch fresh data including new source
      queryClient.invalidateQueries({
        queryKey: ['sources', typeof vaultId === 'string' ? parseInt(vaultId, 10) : vaultId]
      });
    });

    // Listen for source.updated events
    const unsubscribeUpdated = addEventListener('source.updated', () => {
      // Invalidate sources query to refetch with updated source data
      queryClient.invalidateQueries({
        queryKey: ['sources', typeof vaultId === 'string' ? parseInt(vaultId, 10) : vaultId]
      });
    });

    // Listen for source.deleted events
    const unsubscribeDeleted = addEventListener('source.deleted', () => {
      // Invalidate sources query to remove deleted source from list
      queryClient.invalidateQueries({
        queryKey: ['sources', typeof vaultId === 'string' ? parseInt(vaultId, 10) : vaultId]
      });
    });

    // Listen for reconnected events (refetch after reconnection)
    const unsubscribeReconnected = addEventListener('reconnected', () => {
      // Refetch sources after reconnecting to ensure fresh data
      queryClient.invalidateQueries({
        queryKey: ['sources', typeof vaultId === 'string' ? parseInt(vaultId, 10) : vaultId]
      });
    });

    // Cleanup all event listeners on unmount or status change
    return () => {
      unsubscribeCreated();
      unsubscribeUpdated();
      unsubscribeDeleted();
      unsubscribeReconnected();
    };
  }, [status, vaultId, addEventListener, queryClient]);

  return { status };
}
