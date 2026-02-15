'use client';

import { useEffect, useRef, useState } from 'react';
import { useOnboarding } from '@/providers/OnboardingProvider';
import { useAuthStore } from '@/stores/authStore';
import { useRouter } from 'next/navigation';
import { toast } from '@/hooks/useToast';
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
  const { step, completed, updateOnboarding, completeOnboarding, isLoading } = useOnboarding();
  const { user } = useAuthStore();
  const router = useRouter();
  const hasShownResumeToast = useRef(false);
  const [needsWelcomeInit, setNeedsWelcomeInit] = useState(false);

  // Check if onboarding is enabled via feature flag
  const _onboardingEnabled = process.env.NEXT_PUBLIC_ONBOARDING_ENABLED !== 'false';

  // Show "resuming" toast when user returns to incomplete onboarding
  useEffect(() => {
    // Only show toast if:
    // 1. Onboarding is not completed
    // 2. There is a step set (user was in progress)
    // 3. Step is not 'welcome' (not starting fresh)
    // 4. Toast hasn't been shown yet (ref prevents multiple triggers)
    // 5. Not loading (data is ready)
    if (
      !completed &&
      step &&
      step !== 'welcome' &&
      !hasShownResumeToast.current &&
      !isLoading &&
      user
    ) {
      hasShownResumeToast.current = true;

      // Show resume toast with appropriate message based on step
      let resumeMessage = 'Continuing where you left off...';

      if (step === 'path') {
        resumeMessage = 'Choose your onboarding path to continue';
      } else if (step.startsWith('guided-')) {
        resumeMessage = 'Continue creating your vault';
      } else if (step === 'demo') {
        resumeMessage = 'Loading demo vault...';
      } else if (step === 'tutorial') {
        resumeMessage = 'Resume your interactive tutorial';
      } else if (step === 'complete') {
        resumeMessage = 'Almost done! Complete your onboarding';
      }

      toast({
        title: 'Welcome back!',
        description: resumeMessage,
      });
    }
  }, [completed, step, isLoading, user]);

  // Handle welcome step initialization in useEffect to avoid setState during render
  useEffect(() => {
    if (needsWelcomeInit) {
      setNeedsWelcomeInit(false);
      updateOnboarding({ step: 'welcome' }).catch(console.error);
    }
  }, [needsWelcomeInit, updateOnboarding]);

  // Don't render if feature flag is disabled
  if (!_onboardingEnabled) {
    return null;
  }

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
            onPathSelected={(_path) => {
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
        if (!step && !needsWelcomeInit) {
          // Schedule initialization in useEffect to avoid setState during render
          setNeedsWelcomeInit(true);
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
        router.push(`/vaults/${vaultId}`);
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
