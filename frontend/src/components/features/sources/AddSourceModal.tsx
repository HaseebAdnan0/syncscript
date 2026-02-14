'use client';

import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

interface AddSourceModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  vaultId: string;
}

export function AddSourceModal({ open, onOpenChange, vaultId }: AddSourceModalProps) {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- vaultId will be used in metadata fetching implementation
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleFetchMetadata = async () => {
    if (!url.trim()) return;

    setIsLoading(true);
    // TODO: Implement metadata fetching logic using vaultId (will be part of next user story)
    console.log('Fetching metadata for vault:', vaultId);
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add Source</DialogTitle>
          <DialogDescription>
            Enter a URL to add a new source to your knowledge vault
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* URL Input */}
          <div className="space-y-2">
            <label htmlFor="url" className="text-sm font-medium text-white">
              URL
            </label>
            <input
              id="url"
              type="url"
              placeholder="https://example.com/article"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full bg-black/50 border-b-2 border-white/20 h-12 px-4 text-white focus:border-[#F7931A] focus:outline-none transition-colors"
              disabled={isLoading}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !isLoading) {
                  handleFetchMetadata();
                }
              }}
            />
          </div>

          {/* Fetch Metadata Button */}
          <Button
            onClick={handleFetchMetadata}
            disabled={!url.trim() || isLoading}
            className="w-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Fetching Metadata...
              </>
            ) : (
              'Fetch Metadata'
            )}
          </Button>

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="h-8 w-8 animate-spin text-[#F7931A]" />
                <p className="text-sm text-[#94A3B8]">Fetching metadata from URL...</p>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
