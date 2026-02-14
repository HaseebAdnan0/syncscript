'use client';

import { useParams, useRouter } from 'next/navigation';
import { useVault } from '@/hooks/useVaults';
import { useSources } from '@/hooks/useSources';
import { useVaultsStore } from '@/stores/vaultsStore';
import { SourcesList } from '@/components/features/vaults/SourcesList';
import * as Tabs from '@radix-ui/react-tabs';
import { ArrowLeft } from 'lucide-react';

export default function VaultDetailPage() {
  const params = useParams();
  const router = useRouter();
  const vaultId = parseInt(params.id as string, 10);

  // Fetch vault data
  const { data: vault, isLoading: vaultLoading, error: vaultError } = useVault(vaultId);

  // Fetch sources to get count
  const { data: sources = [] } = useSources(vaultId);

  // Active tab from Zustand store
  const { activeTab, setActiveTab } = useVaultsStore();

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
      {/* Header */}
      <div className="bg-[#0F1115] border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-8">
          {/* Back button */}
          <button
            onClick={() => router.push('/vaults')}
            className="flex items-center gap-2 text-[#94A3B8] hover:text-white transition-colors mb-6"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to vaults</span>
          </button>

          {/* Vault name and description */}
          <h1 className="text-4xl font-bold text-white mb-2">{vault.name}</h1>
          {vault.description && (
            <p className="text-[#94A3B8] text-lg">{vault.description}</p>
          )}
        </div>
      </div>

      {/* Main content with tabs */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
          {/* Tab list */}
          <Tabs.List className="flex gap-8 border-b border-white/10 mb-8">
            <Tabs.Trigger
              value="sources"
              className="pb-4 px-2 text-[#94A3B8] hover:text-white transition-colors relative data-[state=active]:text-white"
            >
              <span className="text-lg font-medium">
                Sources {sources.length > 0 && <span className="text-sm">({sources.length})</span>}
              </span>
              {/* Active indicator */}
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#F7931A] opacity-0 data-[state=active]:opacity-100 transition-opacity" />
            </Tabs.Trigger>

            <Tabs.Trigger
              value="members"
              className="pb-4 px-2 text-[#94A3B8] hover:text-white transition-colors relative data-[state=active]:text-white"
            >
              <span className="text-lg font-medium">Members</span>
              {/* Active indicator */}
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#F7931A] opacity-0 data-[state=active]:opacity-100 transition-opacity" />
            </Tabs.Trigger>

            <Tabs.Trigger
              value="settings"
              className="pb-4 px-2 text-[#94A3B8] hover:text-white transition-colors relative data-[state=active]:text-white"
            >
              <span className="text-lg font-medium">Settings</span>
              {/* Active indicator */}
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#F7931A] opacity-0 data-[state=active]:opacity-100 transition-opacity" />
            </Tabs.Trigger>
          </Tabs.List>

          {/* Tab content */}
          <Tabs.Content value="sources">
            <SourcesList vaultId={vaultId} userRole={vault.user_role} />
          </Tabs.Content>

          <Tabs.Content value="members">
            <div className="text-[#94A3B8]">Members tab content (to be implemented)</div>
          </Tabs.Content>

          <Tabs.Content value="settings">
            <div className="text-[#94A3B8]">Settings tab content (to be implemented)</div>
          </Tabs.Content>
        </Tabs.Root>
      </div>
    </div>
  );
}
