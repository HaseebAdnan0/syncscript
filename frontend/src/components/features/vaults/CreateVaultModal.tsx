'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { useCreateVault } from '@/hooks/useVaults';
import { useVaultsStore } from '@/stores/vaultsStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/useToast';

export function CreateVaultModal() {
  const router = useRouter();
  const { toast } = useToast();
  const { isCreateModalOpen, closeCreateModal } = useVaultsStore();
  const createVault = useCreateVault();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('Vault name is required');
      return;
    }

    try {
      const newVault = await createVault.mutateAsync({
        name: name.trim(),
        description: description.trim() || undefined,
      });

      toast({
        title: 'Vault created',
        description: `${newVault.name} has been created successfully.`,
      });

      // Reset form
      setName('');
      setDescription('');
      closeCreateModal();

      // Navigate to the new vault
      router.push(`/vaults/${newVault.id}`);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create vault');
    }
  };

  const handleClose = () => {
    if (!createVault.isPending) {
      setName('');
      setDescription('');
      setError('');
      closeCreateModal();
    }
  };

  return (
    <Dialog.Root open={isCreateModalOpen} onOpenChange={handleClose}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg bg-[#0F1115] backdrop-blur-lg border border-white/10 rounded-2xl p-8 shadow-[0_0_40px_-10px_rgba(247,147,26,0.3)]">
          <div className="flex items-center justify-between mb-6">
            <Dialog.Title className="text-2xl font-bold text-white">
              Create New Vault
            </Dialog.Title>
            <Dialog.Close asChild>
              <button
                type="button"
                className="text-white/60 hover:text-white transition-colors"
                aria-label="Close"
                disabled={createVault.isPending}
              >
                <X className="h-6 w-6" />
              </button>
            </Dialog.Close>
          </div>

          <Dialog.Description className="text-white/60 mb-6">
            Create a new Knowledge Vault to organize your research materials and collaborate with others.
          </Dialog.Description>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="vault-name" className="block text-sm font-medium text-white/80 mb-2">
                Vault Name *
              </label>
              <Input
                id="vault-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., AI Research 2026"
                className="w-full bg-black/50 border-b-2 border-white/20 h-12 px-4 text-white placeholder:text-white/40 focus:border-[#F7931A] focus:outline-none transition-colors"
                disabled={createVault.isPending}
                autoFocus
              />
            </div>

            <div>
              <label htmlFor="vault-description" className="block text-sm font-medium text-white/80 mb-2">
                Description (optional)
              </label>
              <Textarea
                id="vault-description"
                value={description}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setDescription(e.target.value)}
                placeholder="What is this vault about?"
                rows={4}
                className="w-full bg-black/50 border border-white/20 rounded-lg p-4 text-white placeholder:text-white/40 focus:border-[#F7931A] focus:outline-none transition-colors resize-none"
                disabled={createVault.isPending}
              />
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
                {error}
              </div>
            )}

            <div className="flex items-center justify-end gap-4 pt-4">
              <Button
                type="button"
                variant="ghost"
                onClick={handleClose}
                disabled={createVault.isPending}
                className="text-white/60 hover:text-white hover:bg-white/5"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createVault.isPending || !name.trim()}
                className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-8 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                {createVault.isPending ? 'Creating...' : 'Create Vault'}
              </Button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
