'use client';

import { ReactNode } from 'react';
import { useParams } from 'next/navigation';
import { VaultSocketProvider } from '@/contexts/VaultSocketContext';

interface VaultLayoutProps {
  children: ReactNode;
}

/**
 * Layout that provides a single WebSocket connection for all vault detail pages.
 * This prevents multiple connections from being created by different components.
 */
export default function VaultLayout({ children }: VaultLayoutProps) {
  const params = useParams();
  const vaultId = params.id as string;

  if (!vaultId) {
    return <>{children}</>;
  }

  return (
    <VaultSocketProvider vaultId={vaultId}>
      {children}
    </VaultSocketProvider>
  );
}
