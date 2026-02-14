'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useUpdateVault, useArchiveVault, useDeleteVault } from '@/hooks/useVaults';
import { Vault, VaultRole } from '@/lib/types/vault';
import { useToast } from '@/hooks/useToast';
import GradientButton from '@/components/ui/GradientButton';
import { AlertTriangle, Trash2, CheckCircle2, XCircle, BellOff, Bell } from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';
import { StorageUsageIndicator } from './StorageUsageIndicator';
import { muteVault, unmuteVault, getMutedVaults } from '@/lib/api';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface VaultSettingsProps {
  vault: Vault;
  userRole: VaultRole;
}

type CitationFormat = 'apa7' | 'mla9' | 'chicago17' | 'bibtex' | 'ieee' | 'harvard';

const CITATION_FORMATS: { value: CitationFormat | 'none'; label: string }[] = [
  { value: 'none', label: 'Use User Preference' },
  { value: 'apa7', label: 'APA 7th Edition' },
  { value: 'mla9', label: 'MLA 9th Edition' },
  { value: 'chicago17', label: 'Chicago 17th Edition' },
  { value: 'bibtex', label: 'BibTeX' },
  { value: 'ieee', label: 'IEEE' },
  { value: 'harvard', label: 'Harvard' },
];

export function VaultSettings({ vault, userRole }: VaultSettingsProps) {
  const [name, setName] = useState(vault.name);
  const [description, setDescription] = useState(vault.description || '');
  const [citationFormat, setCitationFormat] = useState<CitationFormat | 'none'>(
    vault.default_citation_format || 'none'
  );
  const [isArchiveDialogOpen, setIsArchiveDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const { toast } = useToast();
  const router = useRouter();
  const queryClient = useQueryClient();

  const isOwner = userRole === VaultRole.OWNER;
  const updateVault = useUpdateVault(vault.id);
  const archiveVault = useArchiveVault(vault.id);
  const deleteVault = useDeleteVault();

  // Fetch muted vaults to check if this vault is muted
  const { data: mutedVaults = [] } = useQuery({
    queryKey: ['notifications', 'muted-vaults'],
    queryFn: getMutedVaults,
  });

  const isVaultMuted = mutedVaults.some((mv) => mv.vault_id === vault.id.toString());

  // Mute/unmute mutations
  const muteMutation = useMutation({
    mutationFn: () => muteVault(vault.id.toString()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications', 'muted-vaults'] });
      toast({
        title: 'Vault muted',
        description: 'You will no longer receive notifications from this vault.',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to mute vault. Please try again.',
      });
    },
  });

  const unmuteMutation = useMutation({
    mutationFn: () => unmuteVault(vault.id.toString()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications', 'muted-vaults'] });
      toast({
        title: 'Vault unmuted',
        description: 'You will now receive notifications from this vault.',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to unmute vault. Please try again.',
      });
    },
  });

  const handleToggleMute = () => {
    if (isVaultMuted) {
      unmuteMutation.mutate();
    } else {
      muteMutation.mutate();
    }
  };

  // Update local state when vault prop changes
  useEffect(() => {
    setName(vault.name);
    setDescription(vault.description || '');
    setCitationFormat(vault.default_citation_format || 'none');
  }, [vault.name, vault.description, vault.default_citation_format]);

  // Check if form has changes
  const hasChanges =
    name !== vault.name ||
    description !== (vault.description || '') ||
    citationFormat !== (vault.default_citation_format || 'none');

  const handleSave = async () => {
    if (!hasChanges) return;

    try {
      await updateVault.mutateAsync({
        name: name.trim(),
        description: description.trim() || undefined,
        default_citation_format: citationFormat === 'none' ? null : citationFormat,
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

  const handleDelete = async () => {
    try {
      await deleteVault.mutateAsync(vault.id);

      toast({
        title: 'Vault deleted',
        description: `${vault.name} has been permanently deleted.`,
      });

      setIsDeleteDialogOpen(false);
      router.push('/vaults');
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to delete vault',
      });
    }
  };

  // Check if this is the demo vault
  const isDemoVault = vault.name === 'AI Research Papers 2025';

  // Check if delete confirmation text matches vault name
  const isDeleteConfirmed = deleteConfirmText === vault.name;

  // Reset delete confirmation when dialog closes
  useEffect(() => {
    if (!isDeleteDialogOpen) {
      setDeleteConfirmText('');
    }
  }, [isDeleteDialogOpen]);

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

          {/* Citation Format selector */}
          <div>
            <label htmlFor="citation-format" className="block text-sm font-medium text-[#94A3B8] mb-2">
              Default Citation Format
            </label>
            <p className="text-sm text-[#94A3B8] mb-3">
              Set a default citation format for this vault. This overrides individual user preferences.
              Select &quot;Use User Preference&quot; to let members use their own defaults.
            </p>
            <div className="relative">
              <select
                id="citation-format"
                value={citationFormat}
                onChange={(e) => setCitationFormat(e.target.value as CitationFormat | 'none')}
                disabled={!isOwner}
                className="w-full bg-black/50 border border-white/20 rounded-lg px-4 py-3 text-white
                           focus:border-[#F7931A] focus:outline-none transition-colors
                           disabled:opacity-50 disabled:cursor-not-allowed
                           appearance-none cursor-pointer"
              >
                {CITATION_FORMATS.map((format) => (
                  <option key={format.value} value={format.value} className="bg-[#0F1115] text-white">
                    {format.label}
                  </option>
                ))}
              </select>
              {/* Custom dropdown arrow */}
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg
                  className="h-5 w-5 text-[#94A3B8]"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            </div>
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

      {/* Notification Settings Section */}
      <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-6">Notification Settings</h2>

        <div className="flex items-start justify-between gap-6">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              {isVaultMuted ? (
                <BellOff className="w-5 h-5 text-[#94A3B8]" />
              ) : (
                <Bell className="w-5 h-5 text-[#F7931A]" />
              )}
              <h3 className="text-lg font-semibold text-white">
                {isVaultMuted ? 'Notifications Muted' : 'Notifications Enabled'}
              </h3>
            </div>
            <p className="text-[#94A3B8] text-sm">
              {isVaultMuted
                ? 'You are not receiving notifications from this vault. Toggle to enable notifications for new sources, annotations, and mentions.'
                : 'You are receiving notifications from this vault. Toggle to mute all notifications from this vault.'}
            </p>
          </div>

          {/* Toggle Switch */}
          <button
            onClick={handleToggleMute}
            disabled={muteMutation.isPending || unmuteMutation.isPending}
            className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-[#F7931A] focus:ring-offset-2 focus:ring-offset-[#0F1115] disabled:opacity-50 disabled:cursor-not-allowed ${
              isVaultMuted
                ? 'bg-[#1E293B]'
                : 'bg-gradient-to-r from-[#EA580C] to-[#F7931A]'
            }`}
          >
            <span
              className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-lg transition-transform ${
                isVaultMuted ? 'translate-x-1' : 'translate-x-7'
              }`}
            />
          </button>
        </div>

        {/* Additional info */}
        <div className="mt-6 bg-white/5 border border-white/10 rounded-lg p-4">
          <p className="text-[#94A3B8] text-sm">
            <strong className="text-white">Note:</strong> Muting a vault only affects your personal notifications.
            Other vault members will continue to receive notifications normally.
            You can manage global notification preferences from{' '}
            <a href="/settings/notifications" className="text-[#F7931A] hover:text-[#FFD600] underline">
              Settings → Notifications
            </a>
            .
          </p>
        </div>
      </div>

      {/* Storage Usage Section */}
      {vault.storage_usage && (
        <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
          <h2 className="text-2xl font-bold text-white mb-6">Storage Usage</h2>

          <StorageUsageIndicator
            usedBytes={vault.storage_usage.used_bytes}
            limitBytes={vault.storage_usage.limit_bytes}
            warning={vault.storage_usage.warning}
          />

          {/* Warning message when approaching limit */}
          {vault.storage_usage.warning && vault.storage_usage.percentage >= 0.8 && vault.storage_usage.percentage < 0.95 && (
            <div className="mt-6 bg-[#F7931A]/10 border border-[#F7931A]/30 rounded-lg p-4">
              <p className="text-[#F7931A] text-sm font-medium">
                ⚠️ Storage Approaching Limit
              </p>
              <p className="text-[#94A3B8] text-sm mt-2">
                You're using {Math.round(vault.storage_usage.percentage * 100)}% of your storage quota.
                Consider archiving or removing old files to free up space.
              </p>
            </div>
          )}

          {/* Critical warning when nearly full */}
          {vault.storage_usage.percentage >= 0.95 && (
            <div className="mt-6 bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <p className="text-red-400 text-sm font-semibold">
                🚨 Storage Nearly Full
              </p>
              <p className="text-[#94A3B8] text-sm mt-2">
                You've used {Math.round(vault.storage_usage.percentage * 100)}% of your storage quota.
                Delete files immediately to continue uploading new content.
              </p>
            </div>
          )}
        </div>
      )}

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

          {/* Delete Vault */}
          <div className="border-t border-white/10 pt-6 mt-6">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                  <Trash2 className="w-5 h-5 text-red-500" />
                  Delete Vault
                </h3>
                <p className="text-[#94A3B8] text-sm">
                  Permanently delete this vault and all associated data. This action cannot be undone.
                  All sources, annotations, and member data will be lost forever.
                </p>
              </div>
              <button
                onClick={() => setIsDeleteDialogOpen(true)}
                className="px-6 py-2.5 bg-red-600/10 text-red-500 border border-red-500/50 rounded-full font-semibold hover:bg-red-600/20 hover:border-red-500 transition-all whitespace-nowrap"
              >
                Delete Vault
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

      {/* Delete Confirmation Dialog */}
      <Dialog.Root open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50" />
          <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-[#0F1115] backdrop-blur-lg border border-red-500/20 rounded-2xl p-8 w-full max-w-md shadow-[0_0_40px_-10px_rgba(239,68,68,0.3)] z-50">
            <Dialog.Title className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <Trash2 className="w-6 h-6 text-red-500" />
              Delete {vault.name}?
            </Dialog.Title>

            <Dialog.Description className="text-[#94A3B8] mb-6 space-y-4">
              {isDemoVault && (
                <div className="bg-[#F7931A]/10 border border-[#F7931A]/30 rounded-lg p-4 mb-4">
                  <p className="text-[#F7931A] font-semibold mb-2">📚 This is your demo vault</p>
                  <p className="text-sm text-[#94A3B8]">
                    You can recreate the demo vault anytime from Settings → Onboarding → Recreate Demo Vault.
                    All the original demo content will be restored.
                  </p>
                </div>
              )}

              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                <p className="text-red-400 font-semibold mb-2">⚠️ This action cannot be undone</p>
                <p className="text-sm text-[#94A3B8]">
                  Deleting this vault will permanently remove:
                </p>
                <ul className="list-disc list-inside space-y-1 ml-2 text-sm text-[#94A3B8] mt-2">
                  <li>All sources and citations</li>
                  <li>All annotations and notes</li>
                  <li>All member access and permissions</li>
                  <li>All vault history and audit logs</li>
                </ul>
              </div>

              <div className="space-y-2">
                <label htmlFor="delete-confirm" className="block text-sm font-medium text-white">
                  Type <span className="font-mono text-[#F7931A]">{vault.name}</span> to confirm:
                </label>
                <div className="relative">
                  <input
                    id="delete-confirm"
                    type="text"
                    value={deleteConfirmText}
                    onChange={(e) => setDeleteConfirmText(e.target.value)}
                    disabled={deleteVault.isPending}
                    className="w-full bg-black/50 border-2 border-white/20 rounded-lg h-12 px-4 pr-10 text-white focus:border-red-500 focus:outline-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    placeholder="Enter vault name"
                  />
                  {deleteConfirmText && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      {isDeleteConfirmed ? (
                        <CheckCircle2 className="w-5 h-5 text-green-500" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-500" />
                      )}
                    </div>
                  )}
                </div>
              </div>
            </Dialog.Description>

            <div className="flex gap-3 justify-end">
              <Dialog.Close asChild>
                <button
                  disabled={deleteVault.isPending}
                  className="px-6 py-2.5 bg-white/5 text-white rounded-full font-semibold hover:bg-white/10 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
              </Dialog.Close>
              <button
                onClick={handleDelete}
                disabled={!isDeleteConfirmed || deleteVault.isPending}
                className="px-6 py-2.5 bg-red-600 text-white rounded-full font-semibold hover:bg-red-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleteVault.isPending ? 'Deleting...' : 'Delete Vault'}
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
}
