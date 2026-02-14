'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useAuthStore } from '@/stores/authStore';
import {
  getOnboardingState,
  updateOnboardingState,
} from '@/lib/api';
import { OnboardingState, OnboardingUpdateData } from '@/lib/types/onboarding';

interface OnboardingContextValue {
  step: string | null;
  completed: boolean;
  path: 'guided' | 'demo' | 'skipped' | null;
  data: Record<string, unknown>;
  isLoading: boolean;
  error: string | null;
  updateOnboarding: (data: OnboardingUpdateData) => Promise<void>;
  completeOnboarding: () => Promise<void>;
  refetch: () => Promise<void>;
}

const OnboardingContext = createContext<OnboardingContextValue | undefined>(undefined);

export function useOnboarding() {
  const context = useContext(OnboardingContext);
  if (!context) {
    throw new Error('useOnboarding must be used within OnboardingProvider');
  }
  return context;
}

interface OnboardingProviderProps {
  children: React.ReactNode;
}

export function OnboardingProvider({ children }: OnboardingProviderProps) {
  const { isAuthenticated, user } = useAuthStore();

  const [state, setState] = useState<OnboardingState>({
    step: null,
    completed: false,
    path: null,
    data: {},
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch onboarding state on mount for authenticated users
  const fetchOnboardingState = useCallback(async () => {
    if (!isAuthenticated || !user) {
      // Reset to default state if not authenticated
      setState({
        step: null,
        completed: false,
        path: null,
        data: {},
      });
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await getOnboardingState();
      setState(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load onboarding state';
      setError(errorMessage);
      console.error('Failed to fetch onboarding state:', err);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, user]);

  useEffect(() => {
    fetchOnboardingState();
  }, [fetchOnboardingState]);

  // Update onboarding state and sync to backend
  const updateOnboarding = useCallback(async (data: OnboardingUpdateData) => {
    if (!isAuthenticated) {
      throw new Error('Must be authenticated to update onboarding');
    }

    setError(null);

    try {
      const updatedState = await updateOnboardingState(data);
      setState(updatedState);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update onboarding state';
      setError(errorMessage);
      console.error('Failed to update onboarding state:', err);
      throw err;
    }
  }, [isAuthenticated]);

  // Complete onboarding (convenience method)
  const completeOnboarding = useCallback(async () => {
    await updateOnboarding({ completed: true });
  }, [updateOnboarding]);

  const contextValue: OnboardingContextValue = {
    step: state.step,
    completed: state.completed,
    path: state.path,
    data: state.data,
    isLoading,
    error,
    updateOnboarding,
    completeOnboarding,
    refetch: fetchOnboardingState,
  };

  return (
    <OnboardingContext.Provider value={contextValue}>
      {children}
    </OnboardingContext.Provider>
  );
}
