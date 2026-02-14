'use client';

import React from 'react';
import { useOnboarding } from '@/providers/OnboardingProvider';
import { useAuthStore } from '@/stores/authStore';
import { useRouter } from 'next/navigation';
import WelcomeModal from './WelcomeModal';
import PathSelection from './PathSelection';
import GuidedVaultWizard from './GuidedVaultWizard';
import InteractiveTutorial from './InteractiveTutorial';
import CompletionCelebration from './CompletionCelebration';

/**
 * OnboardingFlow orchestrator component
 * Manages the onboarding flow state machine and renders appropriate component based on current step
 */
export default function OnboardingFlow() {
  const { step, completed, updateOnboarding, completeOnboarding } = useOnboarding();
  const { user } = useAuthStore();
  const router = useRouter();

  // Don't render if onboarding is already completed or user not loaded
  if (completed || !user) {
    return null;
  }

  // Get user's display name
  const userName = user.first_name || user.username || 'there';

  // Render appropriate component based on current step
  const renderCurrentStep = () => {
    switch (step) {
      case 'welcome':
        return (
          <WelcomeModal
            isOpen={true}
            userName={userName}
            onGetStarted={async () => {
              await updateOnboarding({ step: 'path' });
            }}
          />
        );

      case 'path':
        return (
          <PathSelection
            onPathSelected={() => {
              // Path selection already handles state updates
              // This callback is just for any additional orchestration if needed
            }}
          />
        );

      case 'guided-1':
      case 'guided-2':
      case 'guided-3':
        return <GuidedVaultWizard />;

      case 'demo':
        // For demo path, redirect to demo vault and then start tutorial
        handleDemoPath();
        return null;

      case 'tutorial':
        return (
          <InteractiveTutorial
            onComplete={async () => {
              await updateOnboarding({ step: 'complete' });
            }}
            onSkip={async () => {
              await updateOnboarding({ step: 'complete' });
            }}
          />
        );

      case 'complete':
        return (
          <CompletionCelebration
            onComplete={async () => {
              await completeOnboarding();
            }}
          />
        );

      default:
        // Default to welcome step if step is null or unrecognized
        if (!step) {
          // Initialize onboarding with welcome step
          updateOnboarding({ step: 'welcome' }).catch(console.error);
        }
        return null;
    }
  };

  // Handle demo path navigation
  const handleDemoPath = async () => {
    try {
      // Get demo vault status
      const { getDemoVaultStatus, createDemoVault } = await import('@/lib/api');
      const status = await getDemoVaultStatus();

      let vaultId: string | number | null = status.vault_id;

      // Create demo vault if it doesn't exist
      if (!status.exists) {
        const vault = await createDemoVault();
        vaultId = vault.id;
      }

      // Navigate to demo vault
      if (vaultId) {
        router.push(`/dashboard/vaults/${vaultId}`);
      }

      // Transition to tutorial step
      await updateOnboarding({ step: 'tutorial' });
    } catch (error) {
      console.error('Failed to handle demo path:', error);
      // Fallback: go to tutorial anyway
      await updateOnboarding({ step: 'tutorial' });
    }
  };

  return <div className="onboarding-flow">{renderCurrentStep()}</div>;
}
