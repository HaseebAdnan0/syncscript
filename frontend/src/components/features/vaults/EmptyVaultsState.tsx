import { FolderOpen, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface EmptyVaultsStateProps {
  onCreateVault?: () => void;
  variant?: 'owned' | 'shared';
}

export function EmptyVaultsState({ onCreateVault, variant = 'owned' }: EmptyVaultsStateProps) {
  const isShared = variant === 'shared';

  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="mb-6 inline-flex h-24 w-24 items-center justify-center rounded-full bg-white/5 border border-white/10">
        {isShared ? (
          <Users className="h-12 w-12 text-[#F7931A]" />
        ) : (
          <FolderOpen className="h-12 w-12 text-[#F7931A]" />
        )}
      </div>

      <h2 className="mb-3 text-3xl font-bold font-heading text-white">
        {isShared ? 'No shared vaults' : 'No vaults yet'}
      </h2>

      <p className="mb-8 max-w-md text-lg text-muted">
        {isShared
          ? "You haven't been invited to any vaults yet. Ask a colleague to share their vault with you."
          : 'Create your first Knowledge Vault to start organizing research'
        }
      </p>

      {!isShared && onCreateVault && (
        <Button
          onClick={onCreateVault}
          className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-8 py-6 text-sm shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
        >
          Create Vault
        </Button>
      )}
    </div>
  );
}
