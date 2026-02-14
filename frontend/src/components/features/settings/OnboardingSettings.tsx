'use client';

import React, { useState, useEffect } from 'react';
import { RotateCcw, Database } from 'lucide-react';
import { useOnboarding } from '@/providers/OnboardingProvider';
import { useRouter } from 'next/navigation';
import { toast } from '@/hooks/useToast';
import GradientButton from '@/components/ui/GradientButton';
import { getDemoVaultStatus, resetDemoVault, createDemoVault } from '@/lib/api';
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
  const [isDemoConfirmOpen, setIsDemoConfirmOpen] = useState(false);
  const [isResettingDemo, setIsResettingDemo] = useState(false);
  const [demoVaultExists, setDemoVaultExists] = useState<boolean | null>(null);
  const [isLoadingStatus, setIsLoadingStatus] = useState(true);

  // Fetch demo vault status on mount
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const status = await getDemoVaultStatus();
        setDemoVaultExists(status.exists);
      } catch (error) {
        console.error('Failed to fetch demo vault status:', error);
        setDemoVaultExists(null);
      } finally {
        setIsLoadingStatus(false);
      }
    };

    fetchStatus();
  }, []);

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

  const handleResetDemoVault = async () => {
    setIsResettingDemo(true);
    try {
      if (demoVaultExists) {
        // Reset existing demo vault
        await resetDemoVault();
        toast({
          title: 'Demo Vault Reset',
          description: 'Your demo vault has been restored to its original state.',
        });
      } else {
        // Recreate deleted demo vault
        await createDemoVault();
        toast({
          title: 'Demo Vault Created',
          description: 'Your demo vault has been recreated with sample content.',
        });
      }

      setIsDemoConfirmOpen(false);
      setDemoVaultExists(true);

      // Reload to update vault list
      router.refresh();
    } catch (error) {
      console.error('Failed to reset demo vault:', error);
      toast({
        title: 'Error',
        description: 'Failed to reset demo vault. Please try again.',
      });
    } finally {
      setIsResettingDemo(false);
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

      {/* Reset Demo Vault */}
      <div className="flex items-start justify-between border-t border-white/10 pt-6">
        <div className="flex-1">
          <h3 className="text-lg font-heading font-semibold text-white mb-1">
            Demo Vault
          </h3>
          <p className="text-[#94A3B8] text-sm">
            {isLoadingStatus ? (
              'Loading status...'
            ) : demoVaultExists === null ? (
              'Unable to check vault status'
            ) : demoVaultExists ? (
              'Reset your demo vault to its original state with sample content'
            ) : (
              'Your demo vault has been deleted. Recreate it to explore sample content'
            )}
          </p>
        </div>
        <button
          onClick={() => setIsDemoConfirmOpen(true)}
          disabled={isLoadingStatus || demoVaultExists === null}
          className="flex items-center gap-2 px-4 py-2 rounded-full border border-[#F7931A]/30 bg-[#F7931A]/10 text-[#F7931A] hover:bg-[#F7931A]/20 hover:border-[#F7931A]/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Database className="h-4 w-4" />
          {demoVaultExists ? 'Reset' : 'Recreate'}
        </button>
      </div>

      {/* Tutorial Confirmation Dialog */}
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

      {/* Demo Vault Confirmation Dialog */}
      <Dialog open={isDemoConfirmOpen} onOpenChange={setIsDemoConfirmOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl font-heading">
              {demoVaultExists ? 'Reset Demo Vault?' : 'Recreate Demo Vault?'}
            </DialogTitle>
            <DialogDescription className="text-base">
              {demoVaultExists ? (
                <>
                  This will delete all your changes to the demo vault and restore it to its
                  original state with sample AI research papers and annotations. This action
                  cannot be undone.
                </>
              ) : (
                <>
                  This will create a new demo vault with sample AI research papers and
                  annotations to help you explore SyncScript's features.
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <button
              onClick={() => setIsDemoConfirmOpen(false)}
              disabled={isResettingDemo}
              className="px-4 py-2 rounded-full border border-white/20 text-white hover:bg-white/5 transition-all disabled:opacity-50"
            >
              Cancel
            </button>
            <GradientButton
              onClick={handleResetDemoVault}
              disabled={isResettingDemo}
              className="px-4 py-2"
            >
              {isResettingDemo
                ? demoVaultExists
                  ? 'Resetting...'
                  : 'Creating...'
                : demoVaultExists
                  ? 'Reset Demo Vault'
                  : 'Recreate Demo Vault'}
            </GradientButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
