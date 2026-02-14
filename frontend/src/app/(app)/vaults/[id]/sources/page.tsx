'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useVault } from '@/hooks/useVaults';
import { useSourcesQuery } from '@/hooks/useSourcesQuery';
import { useSourcesViewPreference } from '@/hooks/useSourcesViewPreference';
import { useSourcesWebSocket } from '@/hooks/useSourcesWebSocket';
import { SourcesListHeader } from '@/components/features/sources/SourcesListHeader';
import { SourcesFilterBar } from '@/components/features/sources/SourcesFilterBar';
import { SourcesList } from '@/components/features/sources/SourcesList';
import { AddSourceModal } from '@/components/features/sources/AddSourceModal';
import { BulkImportModal } from '@/components/features/sources/BulkImportModal';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ArrowLeft, Wifi, WifiOff, Keyboard } from 'lucide-react';

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

  // Modal state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isBulkImportOpen, setIsBulkImportOpen] = useState(false);
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  // Real-time updates via WebSocket
  const { status } = useSourcesWebSocket({ vaultId });

  // Update page title
  useEffect(() => {
    if (vault) {
      document.title = `${vault.name} - Sources | SyncScript`;
    }
  }, [vault]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in input fields
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        return;
      }

      // Escape closes any open modal
      if (e.key === 'Escape') {
        setIsAddModalOpen(false);
        setIsBulkImportOpen(false);
        setIsHelpOpen(false);
        return;
      }

      // Other shortcuts
      switch (e.key.toLowerCase()) {
        case 'n':
          setIsAddModalOpen(true);
          break;
        case 'b':
          setIsBulkImportOpen(true);
          break;
        case 'g':
          setViewMode('grid');
          break;
        case 't':
          setViewMode('table');
          break;
        case '?':
          setIsHelpOpen(true);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [setViewMode]);

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

          {/* Page title with connection status */}
          <div className="flex items-center gap-4">
            <h1 className="text-3xl font-bold font-heading text-white">
              {vault.name} / Sources
            </h1>

            {/* Subtle connection status indicator */}
            {status === 'connected' && (
              <div className="flex items-center gap-2 px-3 py-1 bg-green-500/10 border border-green-500/30 rounded-full">
                <Wifi className="w-3.5 h-3.5 text-green-400" />
                <span className="text-xs text-green-400">Live</span>
              </div>
            )}
            {status === 'connecting' && (
              <div className="flex items-center gap-2 px-3 py-1 bg-[#F7931A]/10 border border-[#F7931A]/30 rounded-full">
                <Wifi className="w-3.5 h-3.5 text-[#F7931A] animate-pulse" />
                <span className="text-xs text-[#F7931A]">Connecting...</span>
              </div>
            )}
            {status === 'disconnected' && (
              <div className="flex items-center gap-2 px-3 py-1 bg-red-500/10 border border-red-500/30 rounded-full">
                <WifiOff className="w-3.5 h-3.5 text-red-400" />
                <span className="text-xs text-red-400">Offline</span>
              </div>
            )}
          </div>
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

      {/* Bulk import modal */}
      <BulkImportModal
        open={isBulkImportOpen}
        onOpenChange={setIsBulkImportOpen}
        onParsedUrls={() => {
          // Bulk import feature would show preview list here
          // For now, just close the modal
          setIsBulkImportOpen(false);
        }}
      />

      {/* Keyboard shortcuts help dialog */}
      <Dialog open={isHelpOpen} onOpenChange={setIsHelpOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Keyboard className="w-5 h-5 text-[#F7931A]" />
              Keyboard Shortcuts
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-[#94A3B8]">Open Add Source</span>
                <kbd className="px-2 py-1 bg-white/10 border border-white/20 rounded font-mono text-xs">N</kbd>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-[#94A3B8]">Open Bulk Import</span>
                <kbd className="px-2 py-1 bg-white/10 border border-white/20 rounded font-mono text-xs">B</kbd>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-[#94A3B8]">Toggle Grid View</span>
                <kbd className="px-2 py-1 bg-white/10 border border-white/20 rounded font-mono text-xs">G</kbd>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-[#94A3B8]">Toggle Table View</span>
                <kbd className="px-2 py-1 bg-white/10 border border-white/20 rounded font-mono text-xs">T</kbd>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-[#94A3B8]">Close Modal</span>
                <kbd className="px-2 py-1 bg-white/10 border border-white/20 rounded font-mono text-xs">Escape</kbd>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-[#94A3B8]">Show This Help</span>
                <kbd className="px-2 py-1 bg-white/10 border border-white/20 rounded font-mono text-xs">?</kbd>
              </div>
            </div>

            <p className="text-xs text-[#94A3B8] border-t border-white/10 pt-3">
              Shortcuts are disabled when typing in input fields.
            </p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
