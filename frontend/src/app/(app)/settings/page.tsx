'use client';

import { Bell, User, Shield, Palette, Link, GraduationCap } from 'lucide-react';
import { NotificationPreferences } from '@/components/features/notifications/NotificationPreferences';
import { ConnectedAccounts } from '@/components/features/settings/ConnectedAccounts';
import { OnboardingSettings } from '@/components/features/settings/OnboardingSettings';

export default function SettingsPage() {
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

          {/* Profile Section (Placeholder) */}
          <section className="bg-[#0F1115] border border-white/10 rounded-2xl p-8 opacity-50">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
              <div className="h-10 w-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center">
                <User className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-heading font-bold text-white">Profile</h2>
                <p className="text-[#94A3B8] text-sm">Update your personal information</p>
              </div>
            </div>
            <p className="text-[#94A3B8]">Coming soon...</p>
          </section>

          {/* Privacy & Security Section (Placeholder) */}
          <section className="bg-[#0F1115] border border-white/10 rounded-2xl p-8 opacity-50">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
              <div className="h-10 w-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center">
                <Shield className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-heading font-bold text-white">Privacy & Security</h2>
                <p className="text-[#94A3B8] text-sm">Manage your privacy and security settings</p>
              </div>
            </div>
            <p className="text-[#94A3B8]">Coming soon...</p>
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

          {/* Appearance Section (Placeholder) */}
          <section className="bg-[#0F1115] border border-white/10 rounded-2xl p-8 opacity-50">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
              <div className="h-10 w-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center">
                <Palette className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-heading font-bold text-white">Appearance</h2>
                <p className="text-[#94A3B8] text-sm">Customize the look and feel of the app</p>
              </div>
            </div>
            <p className="text-[#94A3B8]">Coming soon...</p>
          </section>
        </div>
      </div>
    </div>
  );
}
