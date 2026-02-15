import { useVaultSocketContextOptional, VaultSocketProvider } from '@/contexts/VaultSocketContext';

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

interface VaultSocketOptions {
  vaultId?: string;
}

interface VaultSocketReturn {
  status: ConnectionStatus;
  send: (eventType: string, data: any) => void;
  addEventListener: (eventType: string, handler: (data: any) => void) => () => void;
}

/**
 * Hook to access the vault WebSocket connection.
 *
 * IMPORTANT: This hook requires a VaultSocketProvider ancestor.
 * The provider is automatically added by the vault layout at:
 * /app/(app)/vaults/[id]/layout.tsx
 *
 * This ensures all components on vault detail pages share a single
 * WebSocket connection instead of each creating their own.
 */
export function useVaultSocket({ vaultId }: VaultSocketOptions): VaultSocketReturn {
  const context = useVaultSocketContextOptional();

  // If we have a context, use it
  if (context) {
    return context;
  }

  // No provider - return a disconnected stub
  // This handles cases where the hook is called outside the provider
  // (e.g., during SSR or on pages without a vault context)
  if (process.env.NODE_ENV === 'development' && vaultId) {
    console.warn(
      'useVaultSocket called outside VaultSocketProvider. ' +
      'WebSocket functionality will not work. ' +
      'Ensure vault pages have a VaultSocketProvider in their layout.'
    );
  }

  return {
    status: 'disconnected',
    send: () => {
      console.warn('Cannot send: useVaultSocket called outside VaultSocketProvider');
    },
    addEventListener: () => {
      // Return a no-op cleanup function
      return () => {};
    },
  };
}

// Re-export the provider for manual usage if needed
export { VaultSocketProvider };
