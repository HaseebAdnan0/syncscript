'use client';

import React, { useState } from 'react';
import { RotateCcw } from 'lucide-react';
import { useOnboarding } from '@/providers/OnboardingProvider';
import { useRouter } from 'next/navigation';
import { toast } from '@/hooks/useToast';
import GradientButton from '@/components/ui/GradientButton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

export function OnboardingSettings() {
  const { updateOnboarding } = useOnboarding();
  const router = useRouter();
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [isRestarting, setIsRestarting] = useState(false);

  const handleRestartTutorial = async () => {
    setIsRestarting(true);
    try {
      // Reset onboarding state to restart tutorial
      await updateOnboarding({
        completed: false,
        step: 'tutorial',
        data: {},
      });

      toast({
        title: 'Tutorial Restarted',
        description: 'The interactive tutorial will begin shortly.',
      });

      setIsConfirmOpen(false);

      // Reload the page to trigger the tutorial
      router.refresh();
    } catch (error) {
      console.error('Failed to restart tutorial:', error);
      toast({
        title: 'Error',
        description: 'Failed to restart tutorial. Please try again.',
      });
    } finally {
      setIsRestarting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Restart Tutorial */}
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-heading font-semibold text-white mb-1">
            Restart Tutorial
          </h3>
          <p className="text-[#94A3B8] text-sm">
            Replay the interactive tutorial to refresh your memory on key features
          </p>
        </div>
        <button
          onClick={() => setIsConfirmOpen(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-full border border-[#F7931A]/30 bg-[#F7931A]/10 text-[#F7931A] hover:bg-[#F7931A]/20 hover:border-[#F7931A]/50 transition-all"
        >
          <RotateCcw className="h-4 w-4" />
          Restart
        </button>
      </div>

      {/* Confirmation Dialog */}
      <Dialog open={isConfirmOpen} onOpenChange={setIsConfirmOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl font-heading">Restart Tutorial?</DialogTitle>
            <DialogDescription className="text-base">
              This will restart the interactive tutorial from the beginning. You'll be guided
              through the key features of SyncScript again.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <button
              onClick={() => setIsConfirmOpen(false)}
              disabled={isRestarting}
              className="px-4 py-2 rounded-full border border-white/20 text-white hover:bg-white/5 transition-all disabled:opacity-50"
            >
              Cancel
            </button>
            <GradientButton
              onClick={handleRestartTutorial}
              disabled={isRestarting}
              className="px-4 py-2"
            >
              {isRestarting ? 'Restarting...' : 'Restart Tutorial'}
            </GradientButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
