'use client';

import { useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from '@/hooks/useAuth';
import { useAuthStore } from '@/stores/authStore';

interface AuthProviderProps {
  children: React.ReactNode;
}

// Refresh token 5 minutes before expiry (access token is 1 hour)
const TOKEN_REFRESH_INTERVAL = 55 * 60 * 1000; // 55 minutes in ms

/**
 * AuthProvider hydrates user state on app load
 * Checks for existing session via /auth/me/ endpoint
 * Proactively refreshes tokens before they expire
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const { refreshUser } = useAuth();
  const { isLoading, accessToken, refreshToken, setTokens, isAuthenticated } = useAuthStore();
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Proactive token refresh function
  const proactiveRefresh = useCallback(async () => {
    if (!refreshToken || !isAuthenticated) return;

    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
        refresh: refreshToken,
      });

      const { access, refresh } = response.data;
      setTokens(access, refresh || refreshToken);
    } catch (error) {
      // If proactive refresh fails, the reactive interceptor will handle it
      console.warn('Proactive token refresh failed:', error);
    }
  }, [refreshToken, isAuthenticated, setTokens]);

  useEffect(() => {
    // Check for existing session on mount
    refreshUser();
  }, [refreshUser]);

  // Set up proactive token refresh interval
  useEffect(() => {
    if (!isAuthenticated || !accessToken) {
      return undefined;
    }

    // Clear any existing interval
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
    }

    // Set up new interval for proactive refresh
    refreshIntervalRef.current = setInterval(proactiveRefresh, TOKEN_REFRESH_INTERVAL);

    // Cleanup on unmount or when auth state changes
    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
        refreshIntervalRef.current = null;
      }
    };
  }, [isAuthenticated, accessToken, proactiveRefresh]);

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
