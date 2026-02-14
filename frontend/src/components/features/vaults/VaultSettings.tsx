'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useUpdateVault, useArchiveVault } from '@/hooks/useVaults';
import { Vault, VaultRole } from '@/lib/types/vault';
import { useToast } from '@/hooks/useToast';
import GradientButton from '@/components/ui/GradientButton';
import { AlertTriangle } from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';

interface VaultSettingsProps {
  vault: Vault;
  userRole: VaultRole;
}

export function VaultSettings({ vault, userRole }: VaultSettingsProps) {
  const [name, setName] = useState(vault.name);
  const [description, setDescription] = useState(vault.description || '');
  const [isArchiveDialogOpen, setIsArchiveDialogOpen] = useState(false);
  const { toast } = useToast();
  const router = useRouter();

  const isOwner = userRole === VaultRole.OWNER;
  const updateVault = useUpdateVault(vault.id);
  const archiveVault = useArchiveVault(vault.id);

  // Update local state when vault prop changes
  useEffect(() => {
    setName(vault.name);
    setDescription(vault.description || '');
  }, [vault.name, vault.description]);

  // Check if form has changes
  const hasChanges = name !== vault.name || description !== (vault.description || '');

  const handleSave = async () => {
    if (!hasChanges) return;

    try {
      await updateVault.mutateAsync({
        name: name.trim(),
        description: description.trim() || undefined,
      });

      toast({
        title: 'Vault updated',
        description: 'Your changes have been saved successfully.',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to update vault',
      });
    }
  };

  const handleArchive = async () => {
    try {
      await archiveVault.mutateAsync();

      toast({
        title: 'Vault archived',
        description: `${vault.name} has been archived successfully.`,
      });

      setIsArchiveDialogOpen(false);
      router.push('/vaults');
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to archive vault',
      });
    }
  };

  return (
    <div className="space-y-8">
      {/* Vault Details Section */}
      <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-6">Vault Details</h2>

        <div className="space-y-6">
          {/* Name input */}
          <div>
            <label htmlFor="vault-name" className="block text-sm font-medium text-[#94A3B8] mb-2">
              Name
            </label>
            <input
              id="vault-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={!isOwner}
              className="w-full bg-black/50 border-b-2 border-white/20 h-12 px-4 text-white focus:border-[#F7931A] focus:outline-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              placeholder="Enter vault name"
            />
          </div>

          {/* Description textarea */}
          <div>
            <label htmlFor="vault-description" className="block text-sm font-medium text-[#94A3B8] mb-2">
              Description
            </label>
            <textarea
              id="vault-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={!isOwner}
              rows={4}
              className="w-full bg-black/50 border-2 border-white/20 rounded-lg p-4 text-white focus:border-[#F7931A] focus:outline-none transition-colors resize-none disabled:opacity-50 disabled:cursor-not-allowed"
              placeholder="Enter vault description"
            />
          </div>

          {/* Save button (only for owners) */}
          {isOwner && (
            <div className="flex justify-end">
              <GradientButton
                onClick={handleSave}
                disabled={!hasChanges || updateVault.isPending}
              >
                {updateVault.isPending ? 'Saving...' : 'Save Changes'}
              </GradientButton>
            </div>
          )}
        </div>
      </div>

      {/* Non-owner message */}
      {!isOwner && (
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
          <p className="text-[#94A3B8] text-sm">
            Only vault owners can modify settings. Contact the vault owner to request changes.
          </p>
        </div>
      )}

      {/* Danger Zone - Only for owners */}
      {isOwner && (
        <div className="bg-[#0F1115] border-2 border-[#EA580C]/30 rounded-2xl p-8">
          <div className="flex items-start gap-3 mb-6">
            <AlertTriangle className="w-6 h-6 text-[#EA580C] mt-1" />
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">Danger Zone</h2>
              <p className="text-[#94A3B8] text-sm">
                Irreversible and destructive actions. Please proceed with caution.
              </p>
            </div>
          </div>

          {/* Archive Vault */}
          <div className="border-t border-white/10 pt-6">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2">Archive Vault</h3>
                <p className="text-[#94A3B8] text-sm">
                  Archive this vault to hide it from your active vaults list. You can restore it later if needed.
                  Members will lose access until the vault is restored.
                </p>
              </div>
              <button
                onClick={() => setIsArchiveDialogOpen(true)}
                className="px-6 py-2.5 bg-[#EA580C]/10 text-[#EA580C] border border-[#EA580C]/50 rounded-full font-semibold hover:bg-[#EA580C]/20 hover:border-[#EA580C] transition-all whitespace-nowrap"
              >
                Archive Vault
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Archive Confirmation Dialog */}
      <Dialog.Root open={isArchiveDialogOpen} onOpenChange={setIsArchiveDialogOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50" />
          <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-[#0F1115] backdrop-blur-lg border border-white/10 rounded-2xl p-8 w-full max-w-md shadow-[0_0_40px_-10px_rgba(247,147,26,0.3)] z-50">
            <Dialog.Title className="text-2xl font-bold text-white mb-4">
              Archive {vault.name}?
            </Dialog.Title>

            <Dialog.Description className="text-[#94A3B8] mb-6 space-y-3">
              <p>
                Archiving this vault will:
              </p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>Hide it from your active vaults list</li>
                <li>Remove access for all members</li>
                <li>Preserve all sources and annotations</li>
                <li>Allow you to restore it later if needed</li>
              </ul>
              <p className="text-[#EA580C] font-medium mt-4">
                This action can be reversed, but members will need to be re-added.
              </p>
            </Dialog.Description>

            <div className="flex gap-3 justify-end">
              <Dialog.Close asChild>
                <button
                  disabled={archiveVault.isPending}
                  className="px-6 py-2.5 bg-white/5 text-white rounded-full font-semibold hover:bg-white/10 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
              </Dialog.Close>
              <button
                onClick={handleArchive}
                disabled={archiveVault.isPending}
                className="px-6 py-2.5 bg-[#EA580C] text-white rounded-full font-semibold hover:bg-[#EA580C]/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {archiveVault.isPending ? 'Archiving...' : 'Archive Vault'}
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
}
