'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppHeader } from '@/components/features/notifications/AppHeader';
import { Sidebar } from '@/components/features/dashboard/Sidebar';
import OnboardingFlow from '@/components/features/onboarding/OnboardingFlow';
import GlobalSearch from '@/components/features/search/GlobalSearch';
import EmailVerificationModal from '@/components/features/auth/EmailVerificationModal';
import { useAuthStore } from '@/stores/authStore';
import { useGlobalSearchShortcut } from '@/hooks/useGlobalSearchShortcut';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const router = useRouter();
  const { user, isLoading } = useAuthStore();
  const { isOpen, open, close } = useGlobalSearchShortcut();
  const [showVerificationModal, setShowVerificationModal] = useState(false);

  // Listen for email verification requirement from API interceptor
  useEffect(() => {
    const handleVerificationRequired = () => {
      setShowVerificationModal(true);
    };

    window.addEventListener('email-verification-required', handleVerificationRequired);
    return () => {
      window.removeEventListener('email-verification-required', handleVerificationRequired);
    };
  }, []);

  // Redirect unauthenticated users to login
  // Redirect unverified users to verification pending page
  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login?returnUrl=' + encodeURIComponent(window.location.pathname));
    } else if (!isLoading && user && !user.email_verified) {
      // Store redirect intent so user goes to original destination after verification
      const returnUrl = encodeURIComponent(window.location.pathname);
      router.push(`/auth/verify-email/pending?email=${encodeURIComponent(user.email)}&returnUrl=${returnUrl}`);
    }
  }, [user, isLoading, router]);

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

  // Don't render app if user is not logged in (redirecting)
  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-[#030304]">
      <AppHeader onSearchClick={open} />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 min-h-[calc(100vh-72px)]">{children}</main>
      </div>
      <OnboardingFlow />
      <GlobalSearch isOpen={isOpen} onClose={close} />
      <EmailVerificationModal
        isOpen={showVerificationModal}
        onClose={() => setShowVerificationModal(false)}
      />
    </div>
  );
}
