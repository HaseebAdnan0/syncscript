'use client';

import { useQuery } from '@tanstack/react-query';
import { Bell, Mail, VolumeX, ChevronLeft } from 'lucide-react';
import Link from 'next/link';
import { getMutedVaults } from '@/lib/api';
import type { MutedVault } from '@/types/notifications';

export default function NotificationPreferencesPage() {
  // Fetch muted vaults
  const { data: mutedVaults, isLoading } = useQuery<MutedVault[]>({
    queryKey: ['muted-vaults'],
    queryFn: getMutedVaults,
  });

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
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                <div className="h-10 w-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center">
                  <Mail className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-heading font-bold text-white">Email Notifications</h2>
                  <p className="text-[#94A3B8] text-sm">Configure your email notification settings</p>
                </div>
              </div>
              <div className="space-y-4">
                <p className="text-[#94A3B8]">Email preferences will be added in US-037 and US-038</p>
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
