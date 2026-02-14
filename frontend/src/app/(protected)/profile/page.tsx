'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import * as Tabs from '@radix-ui/react-tabs';

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-[#030304] py-12">
        <div className="max-w-4xl mx-auto px-4">
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-heading font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent mb-2">
              Account Settings
            </h1>
            <p className="text-[#94A3B8]">
              Manage your profile information and security settings
            </p>
          </div>

          {/* Tabs Container */}
          <Tabs.Root defaultValue="profile" className="w-full">
            {/* Tab List */}
            <Tabs.List className="flex border-b border-white/10 mb-8">
              <Tabs.Trigger
                value="profile"
                className="px-6 py-3 text-[#94A3B8] font-semibold transition-colors relative data-[state=active]:text-[#F7931A] hover:text-white"
              >
                Profile
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#F7931A] opacity-0 data-[state=active]:opacity-100 transition-opacity" />
              </Tabs.Trigger>
              <Tabs.Trigger
                value="security"
                className="px-6 py-3 text-[#94A3B8] font-semibold transition-colors relative data-[state=active]:text-[#F7931A] hover:text-white"
              >
                Security
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#F7931A] opacity-0 data-[state=active]:opacity-100 transition-opacity" />
              </Tabs.Trigger>
            </Tabs.List>

            {/* Profile Tab Content */}
            <Tabs.Content value="profile" className="focus:outline-none">
              <div className="backdrop-blur-lg bg-white/5 border border-white/10 rounded-2xl p-8">
                <h2 className="text-2xl font-heading font-bold text-white mb-6">
                  Profile Information
                </h2>
                <p className="text-[#94A3B8]">
                  Profile form will be implemented in US-018
                </p>
              </div>
            </Tabs.Content>

            {/* Security Tab Content */}
            <Tabs.Content value="security" className="focus:outline-none">
              <div className="backdrop-blur-lg bg-white/5 border border-white/10 rounded-2xl p-8">
                <h2 className="text-2xl font-heading font-bold text-white mb-6">
                  Security Settings
                </h2>
                <p className="text-[#94A3B8]">
                  Password change form will be implemented in US-019
                </p>
              </div>
            </Tabs.Content>
          </Tabs.Root>
        </div>
      </div>
    </ProtectedRoute>
  );
}
