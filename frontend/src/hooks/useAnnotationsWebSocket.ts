import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useVaultSocket } from './useVaultSocket';
import { toast } from './useToast';

interface UseAnnotationsWebSocketOptions {
  vaultId: string | number;
  sourceId?: number;
}

/**
 * Hook to listen for real-time annotation updates via WebSocket
 * Reuses existing vault WebSocket connection from useVaultSocket
 */
export function useAnnotationsWebSocket({ vaultId, sourceId }: UseAnnotationsWebSocketOptions) {
  const queryClient = useQueryClient();
  const { status, addEventListener } = useVaultSocket({ vaultId: String(vaultId) });

  useEffect(() => {
    if (!sourceId) return;

    // Listen for annotation events
    const cleanupCreated = addEventListener('annotation.created', (data: any) => {
      // Invalidate annotations query to fetch fresh data
      queryClient.invalidateQueries({ queryKey: ['annotations', sourceId] });

      // Show subtle toast when another user adds annotation
      // Backend sends payload directly with author field (not wrapped in annotation key)
      if (data?.author?.username) {
        toast({
          title: 'New annotation',
          description: `${data.author.username} added an annotation`,
        });
      }
    });

    const cleanupDeleted = addEventListener('annotation.deleted', () => {
      // Invalidate annotations query to remove deleted annotation
      queryClient.invalidateQueries({ queryKey: ['annotations', sourceId] });
    });

    const cleanupReply = addEventListener('reply.created', (data: any) => {
      // Invalidate annotations query to show new reply
      queryClient.invalidateQueries({ queryKey: ['annotations', sourceId] });

      // Show subtle toast when another user adds reply
      // Backend sends payload directly with author field (not wrapped in reply key)
      if (data?.author?.username) {
        toast({
          title: 'New reply',
          description: `${data.author.username} replied to an annotation`,
        });
      }
    });

    const cleanupReconnect = addEventListener('reconnected', () => {
      // Refresh annotations after reconnection
      queryClient.invalidateQueries({ queryKey: ['annotations', sourceId] });
    });

    // Cleanup all listeners on unmount or dependency change
    return () => {
      cleanupCreated();
      cleanupDeleted();
      cleanupReply();
      cleanupReconnect();
    };
  }, [status, vaultId, sourceId, addEventListener, queryClient]);

  return { status };
}
