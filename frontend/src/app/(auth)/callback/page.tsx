'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import GlassCard from '@/components/ui/GlassCard';
import { useAuthStore } from '@/stores/authStore';
import { api } from '@/lib/api';

export default function OAuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setTokens, setUser } = useAuthStore();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Processing authentication...');

  useEffect(() => {
    const success = searchParams.get('success');
    const error = searchParams.get('error');
    const linkRequired = searchParams.get('link_required');
    const emailRequired = searchParams.get('email_required');
    const provider = searchParams.get('provider');
    const accessToken = searchParams.get('access');
    const refreshToken = searchParams.get('refresh');

    // Handle success case with tokens
    if (success === 'true' && accessToken && refreshToken) {
      // Store tokens in auth store
      setTokens(accessToken, refreshToken);

      // Fetch user data with the new token
      api.get('/auth/me/', {
        headers: { Authorization: `Bearer ${accessToken}` }
      }).then((response) => {
        setUser(response.data);
        setStatus('success');
        setMessage('Successfully signed in! Redirecting to dashboard...');

        // Clear tokens from URL for security (replace history entry)
        window.history.replaceState({}, '', '/callback?success=true');

        setTimeout(() => {
          router.push('/dashboard');
        }, 1000);
      }).catch(() => {
        setStatus('error');
        setMessage('Failed to fetch user data. Please try again.');
      });
      return;
    }

    // Handle success without tokens (fallback - shouldn't happen)
    if (success === 'true') {
      setStatus('success');
      setMessage('Successfully signed in! Redirecting to dashboard...');
      setTimeout(() => {
        router.push('/dashboard');
      }, 1000);
      return;
    }

    // Handle account linking required
    if (linkRequired === 'true' && provider) {
      setStatus('loading');
      setMessage('Account linking required. Redirecting...');
      // Store provider in sessionStorage for linking modal
      sessionStorage.setItem('oauth_link_provider', provider);
      setTimeout(() => {
        router.push('/login?link_oauth=true');
      }, 500);
      return;
    }

    // Handle email required (GitHub private email)
    if (emailRequired === 'true' && provider) {
      setStatus('loading');
      setMessage('Email required. Redirecting...');
      // Store provider in sessionStorage for email prompt modal
      sessionStorage.setItem('oauth_email_provider', provider);
      setTimeout(() => {
        router.push('/register?email_required=true');
      }, 500);
      return;
    }

    // Handle error case
    if (error) {
      setStatus('error');
      const providerName = provider ? (provider.charAt(0).toUpperCase() + provider.slice(1)) : 'the provider';
      const errorMessages: Record<string, string> = {
        'access_denied': 'You cancelled the sign-in process',
        'invalid_request': 'Something went wrong. Please try again',
        'email_exists': 'This email is already registered. Please login with your password',
        'provider_error': `Could not connect to ${providerName}. Please try again`,
      };
      setMessage(errorMessages[error] || 'An unexpected error occurred. Please try again');
    } else if (status === 'loading') {
      // No recognized params, show generic error
      setStatus('error');
      setMessage('Invalid callback. Please try signing in again');
    }
  }, [searchParams, router, status]);

  const handleRetry = () => {
    router.push('/login');
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <GlassCard className="w-full max-w-md p-8">
        <div className="text-center">
          {/* Loading State */}
          {status === 'loading' && (
            <>
              <div className="w-16 h-16 border-4 border-white/20 border-t-[#F7931A] rounded-full animate-spin mx-auto mb-6"></div>
              <h2 className="text-2xl font-heading font-bold text-white mb-2">
                Please wait
              </h2>
              <p className="text-[#94A3B8]">{message}</p>
            </>
          )}

          {/* Success State */}
          {status === 'success' && (
            <>
              <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-6">
                <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-2xl font-heading font-bold text-white mb-2">
                Success!
              </h2>
              <p className="text-[#94A3B8]">{message}</p>
            </>
          )}

          {/* Error State */}
          {status === 'error' && (
            <>
              <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-6">
                <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h2 className="text-2xl font-heading font-bold text-white mb-2">
                Authentication Failed
              </h2>
              <p className="text-[#94A3B8] mb-6">{message}</p>
              <button
                onClick={handleRetry}
                className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
              >
                Try Again
              </button>
            </>
          )}
        </div>
      </GlassCard>
    </div>
  );
}
