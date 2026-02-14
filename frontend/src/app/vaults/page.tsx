'use client';

import { useVaults } from '@/hooks/useVaults';
import { VaultCard } from '@/components/features/vaults/VaultCard';
import { EmptyVaultsState } from '@/components/features/vaults/EmptyVaultsState';
import GradientButton from '@/components/ui/GradientButton';
import { useVaultsStore } from '@/stores/vaultsStore';
import type { Vault } from '@/lib/types/vault';

export default function VaultsPage() {
  const { openCreateModal } = useVaultsStore();
  const { data, isLoading, error } = useVaults();

  const vaults: Vault[] = data?.results || [];

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#030304]">
        <div className="max-w-7xl mx-auto px-6 py-12">
          {/* Header skeleton */}
          <div className="flex items-center justify-between mb-8">
            <div className="h-10 w-48 bg-white/5 animate-pulse rounded" />
            <div className="h-12 w-40 bg-white/5 animate-pulse rounded-full" />
          </div>

          {/* Grid skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 animate-pulse"
              >
                <div className="h-6 w-3/4 bg-white/5 rounded mb-4" />
                <div className="h-4 w-full bg-white/5 rounded mb-2" />
                <div className="h-4 w-2/3 bg-white/5 rounded mb-6" />
                <div className="flex gap-4">
                  <div className="h-4 w-20 bg-white/5 rounded" />
                  <div className="h-4 w-20 bg-white/5 rounded" />
                  <div className="h-4 w-24 bg-white/5 rounded ml-auto" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-[#030304] flex items-center justify-center">
        <div className="text-red-500 text-center">
          <p className="text-xl mb-2">Failed to load vaults</p>
          <p className="text-sm text-[#94A3B8]">Please try again later</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#030304]">
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Page header */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">
            My Vaults
          </h1>
          <GradientButton onClick={openCreateModal}>
            Create Vault
          </GradientButton>
        </div>

        {/* Vaults grid or empty state */}
        {vaults.length === 0 ? (
          <EmptyVaultsState onCreateVault={openCreateModal} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {vaults.map((vault) => (
              <VaultCard key={vault.id} vault={vault} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
