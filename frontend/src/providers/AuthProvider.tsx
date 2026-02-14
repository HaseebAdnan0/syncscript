'use client';

import { useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useAuthStore } from '@/stores/authStore';

interface AuthProviderProps {
  children: React.ReactNode;
}

/**
 * AuthProvider hydrates user state on app load
 * Checks for existing session via /auth/me/ endpoint
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const { refreshUser } = useAuth();
  const { isLoading } = useAuthStore();

  useEffect(() => {
    // Check for existing session on mount
    refreshUser();
  }, [refreshUser]);

  // Show loading spinner while checking auth
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#030304]">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-white/20 border-t-[#F7931A]" />
          <p className="text-sm text-white/60">Loading...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
