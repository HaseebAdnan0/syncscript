'use client';

import React, { useEffect } from 'react';
import { TutorialProvider } from './TutorialProvider';
import { useOnboarding } from '@/providers/OnboardingProvider';
import type { Step } from 'react-joyride';

interface InteractiveTutorialProps {
  onComplete: () => void;
  onSkip: () => void;
}

const InteractiveTutorial: React.FC<InteractiveTutorialProps> = ({ onComplete, onSkip }) => {
  const { updateOnboarding } = useOnboarding();

  // Define tutorial steps highlighting key UI elements
  const tutorialSteps: Step[] = [
    {
      target: '[data-tour="vault-list"]',
      content: 'This is your vault sidebar. All your knowledge vaults appear here. Click on any vault to view its contents.',
      title: 'Knowledge Vaults',
      placement: 'right',
      disableBeacon: false, // Enable beacon for first step to draw attention with pulse
    },
    {
      target: '[data-tour="add-source"]',
      content: 'Click here to add sources to your vault. You can add URLs, PDFs, or arXiv papers to build your research library.',
      title: 'Add Sources',
      placement: 'bottom',
      disableBeacon: true,
    },
    {
      target: '[data-tour="invite-collaborator"]',
      content: 'Collaborate with your team by inviting members. Set their role as Owner, Contributor, or Viewer.',
      title: 'Invite Collaborators',
      placement: 'bottom',
      disableBeacon: true,
    },
    {
      target: '[data-tour="annotations"]',
      content: 'Annotate your sources with notes, highlights, and citations. Thread discussions with your team for deeper collaboration.',
      title: 'Annotations & Notes',
      placement: 'left',
      disableBeacon: true,
    },
    {
      target: '[data-tour="search"]',
      content: 'Search across all your vaults and sources. Find specific citations, notes, or research papers instantly.',
      title: 'Powerful Search',
      placement: 'bottom',
      disableBeacon: true,
    },
    {
      target: '[data-tour="settings"]',
      content: 'Access your account settings, manage connected accounts, and customize your experience here.',
      title: 'Settings & Preferences',
      placement: 'left',
      disableBeacon: true,
    },
    {
      target: '[data-tour="vault-header"]',
      content: "You're all set! Start building your research library by adding sources and collaborating with your team.",
      title: 'Ready to Research!',
      placement: 'center',
      disableBeacon: true,
    },
  ];

  // Handle step changes - update backend on navigation
  const handleStepChange = async (stepIndex: number) => {
    try {
      // Persist current tutorial step to backend
      await updateOnboarding({
        step: 'tutorial',
        data: {
          tutorialStep: stepIndex,
        },
      });
    } catch (error) {
      // Non-blocking error - tutorial continues even if backend update fails
      console.error('Failed to update tutorial step:', error);
    }
  };

  // Scroll target element into view if needed
  useEffect(() => {
    // react-joyride handles scrolling with scrollToFirstStep prop
    // This effect is for any additional scroll behavior if needed
    const scrollToElement = (selector: string) => {
      const element = document.querySelector(selector);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    };

    // Example: scroll to first tutorial target on mount
    if (tutorialSteps.length > 0 && typeof tutorialSteps[0].target === 'string') {
      scrollToElement(tutorialSteps[0].target);
    }
  }, [tutorialSteps]);

  return (
    <TutorialProvider
      steps={tutorialSteps}
      run={true}
      onFinish={onComplete}
      onSkip={onSkip}
      onStepChange={handleStepChange}
    />
  );
};

export default InteractiveTutorial;
