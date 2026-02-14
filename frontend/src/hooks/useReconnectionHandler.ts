'use client';

import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useVaultSocket } from './useVaultSocket';
import { toast } from './useToast';

interface UseReconnectionHandlerOptions {
  vaultId: string;
  currentUserId?: number;
  enabled?: boolean;
}

/**
 * Hook to handle WebSocket reconnection with state recovery
 * - Shows toast notification on reconnect
 * - Refetches vault data to reconcile with server state
 * - Re-sends presence heartbeat immediately
 */
export function useReconnectionHandler({
  vaultId,
  currentUserId,
  enabled = true,
}: UseReconnectionHandlerOptions) {
  const queryClient = useQueryClient();
  const { send, addEventListener } = useVaultSocket({ vaultId });
  const hasShownToastRef = useRef(false);

  useEffect(() => {
    if (!enabled || !vaultId) return;

    // Reset toast flag when vault changes
    hasShownToastRef.current = false;

    const cleanup = addEventListener('reconnected', (data: { vaultId: string }) => {
      console.log(`Reconnected to vault ${data.vaultId} - recovering state`);

      // Show toast notification (only once per reconnection)
      if (!hasShownToastRef.current) {
        toast({
          title: 'Reconnected',
          description: 'Syncing latest changes...',
        });
        hasShownToastRef.current = true;

        // Reset flag after 5 seconds to allow future reconnection toasts
        setTimeout(() => {
          hasShownToastRef.current = false;
        }, 5000);
      }

      // Refetch vault data to reconcile with server state
      // Invalidate all queries related to this vault
      queryClient.invalidateQueries({ queryKey: ['vault', parseInt(data.vaultId)] });
      queryClient.invalidateQueries({ queryKey: ['sources', parseInt(data.vaultId)] });
      queryClient.invalidateQueries({ queryKey: ['annotations', parseInt(data.vaultId)] });
      queryClient.invalidateQueries({ queryKey: ['vaultMembers', parseInt(data.vaultId)] });

      // Re-send presence heartbeat immediately if we have a current user
      if (currentUserId) {
        send('presence.heartbeat', { userId: currentUserId });
      }
    });

    return cleanup;
  }, [vaultId, currentUserId, enabled, addEventListener, send, queryClient]);
}
