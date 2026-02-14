'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bell, Mail, VolumeX, ChevronLeft, Check } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import { getMutedVaults, getPreferences, updatePreferences } from '@/lib/api';
import type { MutedVault, NotificationPreferences } from '@/types/notifications';

export default function NotificationPreferencesPage() {
  const queryClient = useQueryClient();
  const [showSaved, setShowSaved] = useState(false);

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
                    disabled={!preferences}
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
                    disabled={!preferences}
                  >
                    <span
                      className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${
                        preferences?.email_mentions ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <p className="text-[#94A3B8] text-sm">Email frequency selector will be added in US-038</p>
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
              <div className="space-y-4">
                <p className="text-[#94A3B8]">Push notification controls will be added in US-039</p>
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
