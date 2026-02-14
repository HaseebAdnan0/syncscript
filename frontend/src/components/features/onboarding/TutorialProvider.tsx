'use client';

import React, { ReactNode } from 'react';
import Joyride, { Step, Styles, CallBackProps, STATUS, ACTIONS, EVENTS } from 'react-joyride';

interface TutorialProviderProps {
  steps: Step[];
  run: boolean;
  onFinish?: () => void;
  onSkip?: () => void;
  onStepChange?: (stepIndex: number) => void;
  children?: ReactNode;
}

/**
 * TutorialProvider wraps react-joyride with custom Bitcoin DeFi styling
 * Provides glass morphism tooltips with orange accent matching the design system
 */
export function TutorialProvider({
  steps,
  run,
  onFinish,
  onSkip,
  onStepChange,
  children,
}: TutorialProviderProps) {
  const handleJoyrideCallback = (data: CallBackProps) => {
    const { status, action, type, index } = data;

    // Tutorial finished
    if (status === STATUS.FINISHED || status === STATUS.SKIPPED) {
      if (action === ACTIONS.SKIP || status === STATUS.SKIPPED) {
        onSkip?.();
      } else {
        onFinish?.();
      }
    }

    // Close button clicked
    if (action === ACTIONS.CLOSE && type === EVENTS.STEP_AFTER) {
      onSkip?.();
    }

    // Step changed (Next or Back clicked)
    if (type === EVENTS.STEP_AFTER && (action === ACTIONS.NEXT || action === ACTIONS.PREV)) {
      onStepChange?.(index);
    }
  };

  // Custom styles matching Bitcoin DeFi aesthetic
  const customStyles: Partial<Styles> = {
    options: {
      arrowColor: '#0F1115', // Dark Matter surface
      backgroundColor: '#0F1115', // Dark Matter surface
      overlayColor: 'rgba(3, 3, 4, 0.8)', // True Void with opacity
      primaryColor: '#F7931A', // Bitcoin Orange
      textColor: '#FFFFFF', // Pure Light
      width: typeof window !== 'undefined' && window.innerWidth < 768 ? 300 : 380,
      zIndex: 10000,
    },
    tooltip: {
      backgroundColor: '#0F1115',
      borderRadius: '1rem',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      backdropFilter: 'blur(16px)',
      boxShadow: '0 0 30px -5px rgba(247, 147, 26, 0.3)',
      padding: typeof window !== 'undefined' && window.innerWidth < 768 ? '1rem' : '1.5rem',
    },
    tooltipContainer: {
      textAlign: 'left',
    },
    tooltipTitle: {
      color: '#FFFFFF',
      fontSize: typeof window !== 'undefined' && window.innerWidth < 768 ? '1rem' : '1.125rem',
      fontWeight: '700',
      marginBottom: '0.5rem',
      fontFamily: 'var(--font-heading, "Space Grotesk", sans-serif)',
    },
    tooltipContent: {
      color: '#94A3B8', // Stardust (muted text)
      fontSize: typeof window !== 'undefined' && window.innerWidth < 768 ? '0.8125rem' : '0.875rem',
      lineHeight: '1.5',
      padding: '0.5rem 0',
      fontFamily: 'var(--font-body, "Inter", sans-serif)',
    },
    buttonNext: {
      backgroundColor: '#F7931A',
      backgroundImage: 'linear-gradient(to right, #EA580C, #F7931A)',
      borderRadius: '9999px',
      color: '#FFFFFF',
      fontSize: '0.875rem',
      fontWeight: '700',
      padding: typeof window !== 'undefined' && window.innerWidth < 768 ? '0.625rem 1.25rem' : '0.625rem 1.5rem',
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
      border: 'none',
      boxShadow: '0 0 20px -5px rgba(234, 88, 12, 0.5)',
      transition: 'transform 0.2s',
      minHeight: '44px',
    },
    buttonBack: {
      color: '#94A3B8',
      fontSize: '0.875rem',
      fontWeight: '600',
      marginRight: '1rem',
      border: 'none',
      background: 'transparent',
      minHeight: '44px',
      padding: '0.5rem 1rem',
    },
    buttonSkip: {
      color: '#94A3B8',
      fontSize: '0.875rem',
      fontWeight: '600',
      border: 'none',
      background: 'transparent',
      minHeight: '44px',
      padding: '0.5rem 1rem',
    },
    buttonClose: {
      color: '#94A3B8',
      width: '24px',
      height: '24px',
      padding: 0,
    },
    spotlight: {
      borderRadius: '0.5rem',
      boxShadow: '0 0 0 9999px rgba(3, 3, 4, 0.8)',
    },
    beacon: {
      backgroundColor: '#F7931A',
      border: '2px solid #FFD600',
      width: '36px',
      height: '36px',
    },
    beaconInner: {
      backgroundColor: '#F7931A',
      border: '2px solid #FFD600',
    },
    beaconOuter: {
      backgroundColor: 'rgba(247, 147, 26, 0.2)',
      border: '2px solid rgba(255, 214, 0, 0.2)',
    },
  };

  return (
    <>
      {children}
      <Joyride
        steps={steps}
        run={run}
        continuous
        showProgress
        showSkipButton
        scrollToFirstStep
        disableScrolling={false}
        callback={handleJoyrideCallback}
        styles={customStyles}
        locale={{
          back: 'Back',
          close: 'Close',
          last: 'Finish',
          next: 'Next',
          skip: 'Skip Tutorial',
        }}
        floaterProps={{
          disableAnimation: false,
        }}
      />
    </>
  );
}
