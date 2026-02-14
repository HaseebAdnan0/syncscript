'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bell, Mail, VolumeX, ChevronLeft, Check, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { useState, useEffect } from 'react';
import { getMutedVaults, getPreferences, updatePreferences } from '@/lib/api';
import type { MutedVault, NotificationPreferences } from '@/types/notifications';
import { requestNotificationPermission } from '@/lib/pusher';

export default function NotificationPreferencesPage() {
  const queryClient = useQueryClient();
  const [showSaved, setShowSaved] = useState(false);
  const [permissionStatus, setPermissionStatus] = useState<'granted' | 'denied' | 'default'>('default');

  // Fetch muted vaults
  const { data: mutedVaults, isLoading: isLoadingVaults } = useQuery<MutedVault[]>({
    queryKey: ['muted-vaults'],
    queryFn: getMutedVaults,
  });

  // Fetch preferences
  const { data: preferences, isLoading: isLoadingPreferences } = useQuery<NotificationPreferences>({
    queryKey: ['notification-preferences'],
    queryFn: getPreferences,
  });

  // Update preferences mutation
  const updatePreferencesMutation = useMutation({
    mutationFn: (data: Partial<NotificationPreferences>) => updatePreferences(data),
    onMutate: async (newData) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['notification-preferences'] });

      // Snapshot previous value
      const previousPreferences = queryClient.getQueryData<NotificationPreferences>(['notification-preferences']);

      // Optimistically update
      if (previousPreferences) {
        queryClient.setQueryData<NotificationPreferences>(['notification-preferences'], {
          ...previousPreferences,
          ...newData,
        });
      }

      return { previousPreferences };
    },
    onSuccess: () => {
      // Show saved confirmation
      setShowSaved(true);
      setTimeout(() => setShowSaved(false), 2000);
    },
    onError: (_error, _variables, context) => {
      // Rollback on error
      if (context?.previousPreferences) {
        queryClient.setQueryData(['notification-preferences'], context.previousPreferences);
      }
    },
    onSettled: () => {
      // Refetch to ensure sync with server
      queryClient.invalidateQueries({ queryKey: ['notification-preferences'] });
    },
  });

  const handleToggle = (field: keyof NotificationPreferences, value: boolean) => {
    updatePreferencesMutation.mutate({ [field]: value });
  };

  const handleFrequencyChange = (frequency: 'immediate' | 'daily' | 'weekly' | 'none') => {
    updatePreferencesMutation.mutate({ email_digest_frequency: frequency });
  };

  const handlePushToggle = async (field: keyof NotificationPreferences, value: boolean) => {
    // If enabling push_enabled, request browser permission first
    if (field === 'push_enabled' && value) {
      const granted = await requestNotificationPermission();
      if (!granted) {
        // Permission denied, don't enable push
        return;
      }
    }
    updatePreferencesMutation.mutate({ [field]: value });
  };

  // Check notification permission status on mount
  useEffect(() => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      setPermissionStatus(Notification.permission);
    }
  }, []);

  // Update permission status when push_enabled changes
  useEffect(() => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      setPermissionStatus(Notification.permission);
    }
  }, [preferences?.push_enabled]);

  const isLoading = isLoadingVaults || isLoadingPreferences;

  return (
    <div className="min-h-screen bg-[#030304] py-12">
      <div className="max-w-4xl mx-auto px-6">
        {/* Back Link */}
        <Link
          href="/settings"
          className="inline-flex items-center gap-2 text-[#94A3B8] hover:text-[#F7931A] transition-colors mb-6"
        >
          <ChevronLeft className="h-4 w-4" />
          Back to Settings
        </Link>

        {/* Page Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-heading font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent mb-2">
            Notification Preferences
          </h1>
          <p className="text-[#94A3B8] text-lg">
            Manage how and when you receive notifications
          </p>
        </div>

        {/* Loading State */}
        {isLoading ? (
          <div className="space-y-8">
            <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-8 animate-pulse">
              <div className="h-8 bg-white/5 rounded w-1/3 mb-6"></div>
              <div className="space-y-4">
                <div className="h-16 bg-white/5 rounded-lg"></div>
                <div className="h-16 bg-white/5 rounded-lg"></div>
                <div className="h-16 bg-white/5 rounded-lg"></div>
              </div>
            </div>
            <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-8 animate-pulse">
              <div className="h-8 bg-white/5 rounded w-1/3 mb-6"></div>
              <div className="space-y-4">
                <div className="h-16 bg-white/5 rounded-lg"></div>
                <div className="h-16 bg-white/5 rounded-lg"></div>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Email Notifications Section */}
            <section className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/10">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center">
                    <Mail className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-heading font-bold text-white">Email Notifications</h2>
                    <p className="text-[#94A3B8] text-sm">Configure your email notification settings</p>
                  </div>
                </div>
                {showSaved && (
                  <div className="flex items-center gap-2 text-[#F7931A] animate-fade-in">
                    <Check className="h-4 w-4" />
                    <span className="text-sm">Saved</span>
                  </div>
                )}
              </div>
              <div className="space-y-6">
                {/* Vault Activity Toggle */}
                <div className="flex items-center justify-between p-4 bg-black/30 rounded-lg border border-white/5 hover:border-[#F7931A]/20 transition-colors">
                  <div className="flex-1">
                    <h3 className="text-white font-medium mb-1">Vault activity</h3>
                    <p className="text-[#94A3B8] text-sm">
                      Receive notifications when members join or add sources to your vaults
                    </p>
                  </div>
                  <button
                    onClick={() => handleToggle('email_vault_activity', !preferences?.email_vault_activity)}
                    className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors ${
                      preferences?.email_vault_activity
                        ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A]'
                        : 'bg-[#1E293B]'
                    }`}
                    disabled={!preferences || preferences.email_digest_frequency === 'none'}
                  >
                    <span
                      className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${
                        preferences?.email_vault_activity ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* Mentions Toggle */}
                <div className="flex items-center justify-between p-4 bg-black/30 rounded-lg border border-white/5 hover:border-[#F7931A]/20 transition-colors">
                  <div className="flex-1">
                    <h3 className="text-white font-medium mb-1">Mentions</h3>
                    <p className="text-[#94A3B8] text-sm">
                      Receive notifications when someone @mentions you in an annotation or replies to your comment
                    </p>
                  </div>
                  <button
                    onClick={() => handleToggle('email_mentions', !preferences?.email_mentions)}
                    className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors ${
                      preferences?.email_mentions
                        ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A]'
                        : 'bg-[#1E293B]'
                    }`}
                    disabled={!preferences || preferences.email_digest_frequency === 'none'}
                  >
                    <span
                      className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${
                        preferences?.email_mentions ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* Email Frequency Selector */}
                <div className="pt-4 border-t border-white/10">
                  <h3 className="text-white font-medium mb-4">Email Digest Frequency</h3>
                  <div className="space-y-3">
                    {/* Immediate Option */}
                    <label
                      className={`flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition-all ${
                        preferences?.email_digest_frequency === 'immediate'
                          ? 'border-[#F7931A] bg-[#F7931A]/5'
                          : 'border-white/10 bg-black/30 hover:border-[#F7931A]/30'
                      }`}
                    >
                      <input
                        type="radio"
                        name="email_frequency"
                        value="immediate"
                        checked={preferences?.email_digest_frequency === 'immediate'}
                        onChange={() => handleFrequencyChange('immediate')}
                        className="mt-1 h-4 w-4 text-[#F7931A] border-white/20 focus:ring-[#F7931A] focus:ring-offset-0"
                        disabled={!preferences}
                      />
                      <div className="flex-1">
                        <div className="text-white font-medium">Immediate</div>
                        <div className="text-[#94A3B8] text-sm mt-1">
                          Receive an email for each notification as it happens
                        </div>
                      </div>
                    </label>

                    {/* Daily Digest Option */}
                    <label
                      className={`flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition-all ${
                        preferences?.email_digest_frequency === 'daily'
                          ? 'border-[#F7931A] bg-[#F7931A]/5'
                          : 'border-white/10 bg-black/30 hover:border-[#F7931A]/30'
                      }`}
                    >
                      <input
                        type="radio"
                        name="email_frequency"
                        value="daily"
                        checked={preferences?.email_digest_frequency === 'daily'}
                        onChange={() => handleFrequencyChange('daily')}
                        className="mt-1 h-4 w-4 text-[#F7931A] border-white/20 focus:ring-[#F7931A] focus:ring-offset-0"
                        disabled={!preferences}
                      />
                      <div className="flex-1">
                        <div className="text-white font-medium">Daily digest</div>
                        <div className="text-[#94A3B8] text-sm mt-1">
                          Get a summary of all notifications once per day at 9 AM UTC
                        </div>
                      </div>
                    </label>

                    {/* Weekly Digest Option */}
                    <label
                      className={`flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition-all ${
                        preferences?.email_digest_frequency === 'weekly'
                          ? 'border-[#F7931A] bg-[#F7931A]/5'
                          : 'border-white/10 bg-black/30 hover:border-[#F7931A]/30'
                      }`}
                    >
                      <input
                        type="radio"
                        name="email_frequency"
                        value="weekly"
                        checked={preferences?.email_digest_frequency === 'weekly'}
                        onChange={() => handleFrequencyChange('weekly')}
                        className="mt-1 h-4 w-4 text-[#F7931A] border-white/20 focus:ring-[#F7931A] focus:ring-offset-0"
                        disabled={!preferences}
                      />
                      <div className="flex-1">
                        <div className="text-white font-medium">Weekly digest</div>
                        <div className="text-[#94A3B8] text-sm mt-1">
                          Get a summary of all notifications once per week on Monday at 9 AM UTC
                        </div>
                      </div>
                    </label>

                    {/* None Option */}
                    <label
                      className={`flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition-all ${
                        preferences?.email_digest_frequency === 'none'
                          ? 'border-[#F7931A] bg-[#F7931A]/5'
                          : 'border-white/10 bg-black/30 hover:border-[#F7931A]/30'
                      }`}
                    >
                      <input
                        type="radio"
                        name="email_frequency"
                        value="none"
                        checked={preferences?.email_digest_frequency === 'none'}
                        onChange={() => handleFrequencyChange('none')}
                        className="mt-1 h-4 w-4 text-[#F7931A] border-white/20 focus:ring-[#F7931A] focus:ring-offset-0"
                        disabled={!preferences}
                      />
                      <div className="flex-1">
                        <div className="text-white font-medium">None</div>
                        <div className="text-[#94A3B8] text-sm mt-1">
                          Don&apos;t send email notifications (in-app and push notifications only)
                        </div>
                      </div>
                    </label>
                  </div>
                </div>
              </div>
            </section>

            {/* Push Notifications Section */}
            <section className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                <div className="h-10 w-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center">
                  <Bell className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-heading font-bold text-white">Push Notifications</h2>
                  <p className="text-[#94A3B8] text-sm">Configure browser push notification settings</p>
                </div>
              </div>
              <div className="space-y-6">
                {/* Permission Status Banner */}
                {permissionStatus === 'denied' && (
                  <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="text-red-300 font-medium">Browser notifications blocked</div>
                      <div className="text-red-300/80 text-sm mt-1">
                        You&apos;ve blocked notifications for this site. To enable them, update your browser settings.
                      </div>
                    </div>
                  </div>
                )}
                {permissionStatus === 'default' && preferences?.push_enabled && (
                  <div className="flex items-start gap-3 p-4 bg-[#F7931A]/10 border border-[#F7931A]/20 rounded-lg">
                    <AlertCircle className="h-5 w-5 text-[#F7931A] flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="text-[#F7931A] font-medium">Permission required</div>
                      <div className="text-[#F7931A]/80 text-sm mt-1">
                        Enable the master toggle below to grant browser notification permission.
                      </div>
                    </div>
                  </div>
                )}

                {/* Master Toggle */}
                <div className="flex items-center justify-between p-4 bg-black/30 rounded-lg border border-white/5 hover:border-[#F7931A]/20 transition-colors">
                  <div className="flex-1">
                    <h3 className="text-white font-medium mb-1">Enable push notifications</h3>
                    <p className="text-[#94A3B8] text-sm">
                      Receive real-time browser notifications when activity happens in your vaults
                    </p>
                    {permissionStatus === 'granted' && preferences?.push_enabled && (
                      <p className="text-green-400 text-xs mt-2">✓ Browser permission granted</p>
                    )}
                  </div>
                  <button
                    onClick={() => handlePushToggle('push_enabled', !preferences?.push_enabled)}
                    className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors ${
                      preferences?.push_enabled
                        ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A]'
                        : 'bg-[#1E293B]'
                    }`}
                    disabled={!preferences}
                  >
                    <span
                      className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${
                        preferences?.push_enabled ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* New Sources Sub-toggle */}
                <div className="flex items-center justify-between p-4 bg-black/30 rounded-lg border border-white/5 hover:border-[#F7931A]/20 transition-colors">
                  <div className="flex-1">
                    <h3 className="text-white font-medium mb-1">New sources</h3>
                    <p className="text-[#94A3B8] text-sm">
                      Get notified when new sources are added to your vaults
                    </p>
                  </div>
                  <button
                    onClick={() => handlePushToggle('push_sources', !preferences?.push_sources)}
                    className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors ${
                      preferences?.push_sources
                        ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A]'
                        : 'bg-[#1E293B]'
                    }`}
                    disabled={!preferences || !preferences.push_enabled}
                  >
                    <span
                      className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${
                        preferences?.push_sources ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* Annotation Activity Sub-toggle */}
                <div className="flex items-center justify-between p-4 bg-black/30 rounded-lg border border-white/5 hover:border-[#F7931A]/20 transition-colors">
                  <div className="flex-1">
                    <h3 className="text-white font-medium mb-1">Annotation activity</h3>
                    <p className="text-[#94A3B8] text-sm">
                      Get notified when someone replies to your annotations or mentions you
                    </p>
                  </div>
                  <button
                    onClick={() => handlePushToggle('push_annotations', !preferences?.push_annotations)}
                    className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors ${
                      preferences?.push_annotations
                        ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A]'
                        : 'bg-[#1E293B]'
                    }`}
                    disabled={!preferences || !preferences.push_enabled}
                  >
                    <span
                      className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${
                        preferences?.push_annotations ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </section>

            {/* Muted Vaults Section */}
            <section className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                <div className="h-10 w-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center">
                  <VolumeX className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-heading font-bold text-white">Muted Vaults</h2>
                  <p className="text-[#94A3B8] text-sm">Manage vaults you&apos;ve muted</p>
                </div>
              </div>
              <div className="space-y-4">
                {mutedVaults && mutedVaults.length > 0 ? (
                  <div className="space-y-2">
                    {mutedVaults.map((muted) => (
                      <div
                        key={muted.vault_id}
                        className="flex items-center justify-between p-4 bg-black/30 rounded-lg border border-white/5"
                      >
                        <span className="text-white">{muted.vault_name}</span>
                        <span className="text-[#94A3B8] text-sm">Unmute button will be added in US-040</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <VolumeX className="h-12 w-12 text-[#94A3B8] mx-auto mb-3 opacity-50" />
                    <p className="text-[#94A3B8]">No muted vaults</p>
                    <p className="text-[#94A3B8] text-sm mt-1">Mute vaults from the vault settings page</p>
                  </div>
                )}
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
