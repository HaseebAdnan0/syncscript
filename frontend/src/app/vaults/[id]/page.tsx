'use client';

import { useParams } from 'next/navigation';
import { useState, useEffect, useCallback } from 'react';
import { useVault } from '@/hooks/useVaults';
import { useSources } from '@/hooks/useSources';
import { useVaultSocket } from '@/hooks/useVaultSocket';
import { SourceCard } from '@/components/features/sources/SourceCard';
import type { Source } from '@/lib/types/sources';

export default function VaultDetailPage() {
  const params = useParams();
  const vaultId = parseInt(params.id as string, 10);
  const vaultIdStr = params.id as string;

  // Fetch vault data
  const { data: vault, isLoading: vaultLoading, error: vaultError } = useVault(vaultId);

  // Fetch sources
  const { data: sources = [], isLoading: sourcesLoading, refetch: refetchSources } = useSources(vaultId);

  // WebSocket connection
  const { status, addEventListener } = useVaultSocket({ vaultId: vaultIdStr });

  // Local state for animated sources (to trigger fade-in)
  const [newSourceIds, setNewSourceIds] = useState<Set<number>>(new Set());

  // Handle real-time source events
  const handleSourceCreated = useCallback((data: { source: Source }) => {
    console.log('Source created event:', data);
    // Mark as new for animation
    setNewSourceIds((prev) => new Set(prev).add(data.source.id));
    // Refetch sources to update the list
    refetchSources();
    // Remove animation after 2 seconds
    setTimeout(() => {
      setNewSourceIds((prev) => {
        const updated = new Set(prev);
        updated.delete(data.source.id);
        return updated;
      });
    }, 2000);
  }, [refetchSources]);

  const handleSourceUpdated = useCallback((data: { source: Source }) => {
    console.log('Source updated event:', data);
    refetchSources();
  }, [refetchSources]);

  const handleSourceDeleted = useCallback((data: { source_id: number }) => {
    console.log('Source deleted event:', data);
    refetchSources();
  }, [refetchSources]);

  // Subscribe to WebSocket events
  useEffect(() => {
    const unsubscribeCreated = addEventListener('source.created', handleSourceCreated);
    const unsubscribeUpdated = addEventListener('source.updated', handleSourceUpdated);
    const unsubscribeDeleted = addEventListener('source.deleted', handleSourceDeleted);

    return () => {
      unsubscribeCreated();
      unsubscribeUpdated();
      unsubscribeDeleted();
    };
  }, [addEventListener, handleSourceCreated, handleSourceUpdated, handleSourceDeleted]);

  if (vaultLoading) {
    return (
      <div className="min-h-screen bg-[#030304] flex items-center justify-center">
        <div className="text-[#94A3B8]">Loading vault...</div>
      </div>
    );
  }

  if (vaultError || !vault) {
    return (
      <div className="min-h-screen bg-[#030304] flex items-center justify-center">
        <div className="text-red-500">Failed to load vault</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#030304]">
      {/* Header */}
      <div className="bg-[#0F1115] border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <h1 className="text-4xl font-bold text-white mb-2">{vault.name}</h1>
          <p className="text-[#94A3B8]">{vault.description}</p>
          <div className="flex items-center gap-6 mt-4 text-sm text-[#94A3B8]">
            <span>{vault.source_count} sources</span>
            <span>{vault.member_count} members</span>
            <span>
              Connection:{' '}
              <span
                className={
                  status === 'connected'
                    ? 'text-green-500'
                    : status === 'reconnecting'
                    ? 'text-[#F7931A]'
                    : 'text-red-500'
                }
              >
                {status}
              </span>
            </span>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-6">Sources</h2>

          {sourcesLoading ? (
            <div className="text-[#94A3B8]">Loading sources...</div>
          ) : sources.length === 0 ? (
            <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-12 text-center">
              <p className="text-[#94A3B8]">No sources yet. Add your first source to get started!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {sources.map((source) => (
                <div
                  key={source.id}
                  className={
                    newSourceIds.has(source.id)
                      ? 'animate-in fade-in duration-500'
                      : ''
                  }
                >
                  <SourceCard source={source} vaultId={vaultId.toString()} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
