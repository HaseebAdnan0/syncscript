'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useVault } from '@/hooks/useVaults';
import { useSourcesQuery } from '@/hooks/useSourcesQuery';
import { useSourcesViewPreference } from '@/hooks/useSourcesViewPreference';
import { SourcesListHeader } from '@/components/features/sources/SourcesListHeader';
import { SourcesFilterBar } from '@/components/features/sources/SourcesFilterBar';
import { SourcesList } from '@/components/features/sources/SourcesList';
import { AddSourceModal } from '@/components/features/sources/AddSourceModal';
import { ArrowLeft } from 'lucide-react';

export default function SourcesPage() {
  const params = useParams();
  const router = useRouter();
  const vaultId = params.id as string;

  // Fetch vault data
  const { data: vault, isLoading: vaultLoading, error: vaultError } = useVault(parseInt(vaultId, 10));

  // Fetch sources
  const { data: sources = [], isLoading: sourcesLoading } = useSourcesQuery({
    vaultId: parseInt(vaultId, 10),
  });

  // View preference hook
  const [viewMode, setViewMode] = useSourcesViewPreference();

  // Add source modal state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // Update page title
  useEffect(() => {
    if (vault) {
      document.title = `${vault.name} - Sources | SyncScript`;
    }
  }, [vault]);

  // Loading state
  if (vaultLoading) {
    return (
      <div className="min-h-screen bg-[#030304] flex items-center justify-center">
        <div className="text-[#94A3B8] text-lg">Loading vault...</div>
      </div>
    );
  }

  // 404 handling
  if (vaultError || !vault) {
    return (
      <div className="min-h-screen bg-[#030304] flex flex-col items-center justify-center gap-4">
        <div className="text-red-500 text-xl">Vault not found</div>
        <button
          onClick={() => router.push('/vaults')}
          className="text-[#F7931A] hover:text-[#FFD600] transition-colors"
        >
          Return to vaults
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#030304]">
      {/* Header with vault context */}
      <div className="bg-[#0F1115] border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-6">
          {/* Breadcrumb navigation */}
          <button
            onClick={() => router.push(`/vaults/${vaultId}`)}
            className="flex items-center gap-2 text-[#94A3B8] hover:text-white transition-colors mb-4"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to {vault.name}</span>
          </button>

          {/* Page title */}
          <h1 className="text-3xl font-bold font-heading text-white">
            {vault.name} / Sources
          </h1>
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Sources list header with view toggle */}
        <SourcesListHeader
          sourceCount={sources.length}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          onAddSource={() => setIsAddModalOpen(true)}
        />

        {/* Filters bar */}
        <div className="mb-8">
          <SourcesFilterBar />
        </div>

        {/* Sources list */}
        <SourcesList
          sources={sources}
          vaultId={vaultId}
          viewMode={viewMode}
          isLoading={sourcesLoading}
          onAddSource={() => setIsAddModalOpen(true)}
        />
      </div>

      {/* Add source modal */}
      <AddSourceModal
        open={isAddModalOpen}
        onOpenChange={setIsAddModalOpen}
        vaultId={vaultId}
      />
    </div>
  );
}
