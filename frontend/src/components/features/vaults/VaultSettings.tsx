'use client';

import { useState, useEffect } from 'react';
import { useUpdateVault } from '@/hooks/useVaults';
import { Vault, VaultRole } from '@/lib/types/vault';
import { useToast } from '@/hooks/useToast';
import GradientButton from '@/components/ui/GradientButton';

interface VaultSettingsProps {
  vault: Vault;
  userRole: VaultRole;
}

export function VaultSettings({ vault, userRole }: VaultSettingsProps) {
  const [name, setName] = useState(vault.name);
  const [description, setDescription] = useState(vault.description || '');
  const { toast } = useToast();

  const isOwner = userRole === VaultRole.OWNER;
  const updateVault = useUpdateVault(vault.id);

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
    </div>
  );
}
