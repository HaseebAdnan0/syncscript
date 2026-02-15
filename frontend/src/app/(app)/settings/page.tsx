'use client';

import { useState, useEffect } from 'react';
import { Bell, User, Shield, Palette, Link, GraduationCap, Sparkles, Quote } from 'lucide-react';
import { NotificationPreferences } from '@/components/features/notifications/NotificationPreferences';
import { ConnectedAccounts } from '@/components/features/settings/ConnectedAccounts';
import { OnboardingSettings } from '@/components/features/settings/OnboardingSettings';
import { CitationPreferences } from '@/components/features/settings/CitationPreferences';
import TokenUsageDisplay from '@/components/features/ai/TokenUsageDisplay';
import { getAIUsage } from '@/lib/api/ai';
import { AIUsageStats } from '@/lib/types/ai';
import { useToast } from '@/hooks/useToast';

export default function SettingsPage() {
  const { toast } = useToast();
  const [aiUsage, setAiUsage] = useState<AIUsageStats | null>(null);
  const [isLoadingUsage, setIsLoadingUsage] = useState(true);

  // Fetch AI usage stats on mount
  useEffect(() => {
    const fetchAIUsage = async () => {
      try {
        const usage = await getAIUsage();
        setAiUsage(usage);
      } catch (error) {
        console.error('Failed to fetch AI usage:', error);
        toast({
          title: 'Error',
          description: 'Failed to load AI usage statistics',
        });
      } finally {
        setIsLoadingUsage(false);
      }
    };

    fetchAIUsage();
  }, [toast]);

  return (
    <div className="min-h-screen bg-[#030304] py-12">
      <div className="max-w-4xl mx-auto px-6">
        {/* Page Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-heading font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent mb-2">
            Settings
          </h1>
          <p className="text-[#94A3B8] text-lg">
            Manage your account preferences and application settings
          </p>
        </div>

        {/* Settings Sections */}
        <div className="space-y-8">
          {/* AI Usage Section */}
          <section className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
              <div className="h-10 w-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-heading font-bold text-white">AI Usage</h2>
                <p className="text-[#94A3B8] text-sm">Monitor your AI research assistant usage</p>
              </div>
            </div>
            {isLoadingUsage ? (
              <div className="flex items-center justify-center py-8">
                <div className="h-8 w-8 border-4 border-[#F7931A] border-t-transparent rounded-full animate-spin" />
              </div>
            ) : aiUsage ? (
              <TokenUsageDisplay usage={aiUsage} />
            ) : (
              <p className="text-[#94A3B8]">Unable to load usage statistics</p>
            )}
          </section>

          {/* Citation Preferences Section */}
          <section className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
              <div className="h-10 w-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center">
                <Quote className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-heading font-bold text-white">Citation Preferences</h2>
                <p className="text-[#94A3B8] text-sm">Set your default citation format</p>
              </div>
            </div>
            <CitationPreferences />
          </section>

          {/* Notifications Section */}
          <section className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
              <div className="h-10 w-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center">
                <Bell className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-heading font-bold text-white">Notifications</h2>
                <p className="text-[#94A3B8] text-sm">Configure your notification preferences</p>
              </div>
            </div>
            <NotificationPreferences />
          </section>

          {/* Profile Section */}
          <section className="bg-[#0F1115] border border-white/10 rounded-2xl p-8 hover:border-[#F7931A]/50 transition-all group">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/10">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center">
                  <User className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-heading font-bold text-white">Profile</h2>
                  <p className="text-[#94A3B8] text-sm">Update your personal information</p>
                </div>
              </div>
            </div>
            <p className="text-[#94A3B8] mb-4">
              Manage your name, bio, and other profile details.
            </p>
            <a
              href="/profile"
              className="inline-flex items-center gap-2 bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider text-sm rounded-full px-6 py-2.5 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
            >
              Edit Profile
            </a>
          </section>

          {/* Privacy & Security Section */}
          <section className="bg-[#0F1115] border border-white/10 rounded-2xl p-8 hover:border-[#F7931A]/50 transition-all group">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/10">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center">
                  <Shield className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-heading font-bold text-white">Privacy & Security</h2>
                  <p className="text-[#94A3B8] text-sm">Manage your privacy and security settings</p>
                </div>
              </div>
            </div>
            <p className="text-[#94A3B8] mb-4">
              Change your password and manage security settings.
            </p>
            <a
              href="/profile#security"
              className="inline-flex items-center gap-2 bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider text-sm rounded-full px-6 py-2.5 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
            >
              Security Settings
            </a>
          </section>

          {/* Onboarding Section */}
          <section className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
              <div className="h-10 w-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center">
                <GraduationCap className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-heading font-bold text-white">Onboarding</h2>
                <p className="text-[#94A3B8] text-sm">Manage your tutorial and demo vault</p>
              </div>
            </div>
            <OnboardingSettings />
          </section>

          {/* Connected Accounts Section */}
          <section className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
              <div className="h-10 w-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center">
                <Link className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-heading font-bold text-white">Connected Accounts</h2>
                <p className="text-[#94A3B8] text-sm">Manage your OAuth provider connections</p>
              </div>
            </div>
            <ConnectedAccounts />
          </section>

          {/* Appearance Section */}
          <section className="bg-[#0F1115] border border-white/10 rounded-2xl p-8">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
              <div className="h-10 w-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center">
                <Palette className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-heading font-bold text-white">Appearance</h2>
                <p className="text-[#94A3B8] text-sm">Customize the look and feel of the app</p>
              </div>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="h-8 w-8 rounded-full bg-[#F7931A]/20 flex items-center justify-center">
                  <Sparkles className="h-4 w-4 text-[#F7931A]" />
                </div>
                <span className="text-white font-medium">Theme customization in development</span>
              </div>
              <p className="text-[#94A3B8] text-sm">
                Light mode, custom accent colors, and display density options will be available in a future update.
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
