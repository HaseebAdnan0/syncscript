'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface ConnectedAccount {
  provider: 'google' | 'github';
  connected_at: string;
  email: string;
  profile_picture?: string;
  username?: string;
  avatar_url?: string;
}

const providerConfig = {
  google: {
    name: 'Google',
    icon: (
      <svg className="h-5 w-5" viewBox="0 0 24 24">
        <path
          fill="#4285F4"
          d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        />
        <path
          fill="#34A853"
          d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        />
        <path
          fill="#FBBC05"
          d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        />
        <path
          fill="#EA4335"
          d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        />
      </svg>
    ),
  },
  github: {
    name: 'GitHub',
    icon: (
      <svg className="h-5 w-5 fill-white" viewBox="0 0 24 24">
        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
      </svg>
    ),
  },
};

export function ConnectedAccounts() {
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [disconnecting, setDisconnecting] = useState<string | null>(null);
  const [confirmDisconnect, setConfirmDisconnect] = useState<'google' | 'github' | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchConnectedAccounts();
  }, []);

  const fetchConnectedAccounts = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get<ConnectedAccount[]>('/auth/oauth/connected/', {
        withCredentials: true,
      });
      setAccounts(response.data);
    } catch (err) {
      console.error('Failed to fetch connected accounts:', err);
      setError('Failed to load connected accounts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = (provider: 'google' | 'github') => {
    // Redirect to OAuth flow with next=/settings to return here after auth
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    window.location.href = `${apiUrl}/auth/${provider}/?next=/settings`;
  };

  const handleDisconnect = async (provider: 'google' | 'github') => {
    try {
      setDisconnecting(provider);
      setError(null);
      await api.delete(`/auth/oauth/connected/${provider}/`, {
        withCredentials: true,
      });

      // Remove from accounts list
      setAccounts(accounts.filter((acc) => acc.provider !== provider));
      setConfirmDisconnect(null);

      // Show success toast
      setSuccessMessage(`${providerConfig[provider].name} account disconnected successfully`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: any) {
      console.error('Failed to disconnect account:', err);

      // Handle "last auth method" error
      if (err.response?.status === 400) {
        setError(
          err.response?.data?.error ||
          'Cannot disconnect your only authentication method. Please set a password or connect another account first.'
        );
      } else {
        setError('Failed to disconnect account. Please try again.');
      }
      setConfirmDisconnect(null);
    } finally {
      setDisconnecting(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-white/20 border-t-[#F7931A]"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-4">
        <p className="text-red-500 text-sm">{error}</p>
        <button
          onClick={fetchConnectedAccounts}
          className="mt-2 text-sm text-[#F7931A] hover:text-[#FFD600] transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  const connectedProviders = new Set(accounts.map((acc) => acc.provider));
  const availableProviders: Array<'google' | 'github'> = ['google', 'github'].filter(
    (p) => !connectedProviders.has(p as 'google' | 'github')
  ) as Array<'google' | 'github'>;

  return (
    <div className="space-y-4">
      {/* Connected Accounts List */}
      {accounts.length > 0 && (
        <div className="space-y-3">
          {accounts.map((account) => {
            const config = providerConfig[account.provider];
            return (
              <div
                key={account.provider}
                className="flex items-center justify-between p-4 rounded-lg border border-white/10 bg-black/20 hover:border-white/20 transition-colors"
              >
                {/* Provider Info */}
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded-full bg-white/10 flex items-center justify-center">
                    {config.icon}
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">{config.name}</h3>
                    <p className="text-[#94A3B8] text-sm">
                      {account.email}
                      {account.username && ` (@${account.username})`}
                    </p>
                    <p className="text-[#94A3B8] text-xs mt-1">
                      Connected {new Date(account.connected_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                {/* Disconnect Button */}
                <button
                  onClick={() => setConfirmDisconnect(account.provider)}
                  disabled={disconnecting === account.provider}
                  className="px-4 py-2 text-sm font-medium text-red-400 border border-red-500/20 rounded-lg hover:bg-red-500/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {disconnecting === account.provider ? 'Disconnecting...' : 'Disconnect'}
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Available Providers to Connect */}
      {availableProviders.length > 0 && (
        <div className="space-y-3">
          {accounts.length > 0 && (
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/10"></div>
              </div>
              <div className="relative flex justify-center">
                <span className="px-4 text-sm text-[#94A3B8] bg-[#0F1115]">
                  Available to connect
                </span>
              </div>
            </div>
          )}

          {availableProviders.map((provider) => {
            const config = providerConfig[provider];
            return (
              <div
                key={provider}
                className="flex items-center justify-between p-4 rounded-lg border border-white/10 bg-black/20 hover:border-white/20 transition-colors"
              >
                {/* Provider Info */}
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded-full bg-white/10 flex items-center justify-center">
                    {config.icon}
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">{config.name}</h3>
                    <p className="text-[#94A3B8] text-sm">Not connected</p>
                  </div>
                </div>

                {/* Connect Button */}
                <button
                  onClick={() => handleConnect(provider)}
                  className="px-4 py-2 text-sm font-medium bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white rounded-lg hover:scale-105 transition-all shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)]"
                >
                  Connect
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Empty State */}
      {accounts.length === 0 && availableProviders.length === 0 && (
        <div className="text-center py-12">
          <p className="text-[#94A3B8]">No OAuth providers available</p>
        </div>
      )}

      {/* Confirmation Dialog */}
      {confirmDisconnect && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 max-w-md w-full mx-4 shadow-[0_0_40px_-10px_rgba(247,147,26,0.3)]">
            <h3 className="text-xl font-bold text-white mb-2">
              Disconnect {providerConfig[confirmDisconnect].name}?
            </h3>
            <p className="text-[#94A3B8] text-sm mb-6">
              Are you sure you want to disconnect your {providerConfig[confirmDisconnect].name} account?
              You can reconnect it at any time.
            </p>

            <div className="flex gap-3">
              <button
                onClick={() => setConfirmDisconnect(null)}
                disabled={disconnecting !== null}
                className="flex-1 px-4 py-2 text-sm font-medium text-white border border-white/10 rounded-lg hover:bg-white/5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDisconnect(confirmDisconnect)}
                disabled={disconnecting !== null}
                className="flex-1 px-4 py-2 text-sm font-medium bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {disconnecting === confirmDisconnect ? 'Disconnecting...' : 'Disconnect'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Success Toast */}
      {successMessage && (
        <div className="fixed bottom-4 right-4 bg-green-500/20 border border-green-500/50 text-green-400 px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in">
          <div className="flex items-center gap-2">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <p className="text-sm font-medium">{successMessage}</p>
          </div>
        </div>
      )}
    </div>
  );
}
