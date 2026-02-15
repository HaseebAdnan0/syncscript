'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppHeader } from '@/components/features/notifications/AppHeader';
import { Sidebar } from '@/components/features/dashboard/Sidebar';
import OnboardingFlow from '@/components/features/onboarding/OnboardingFlow';
import GlobalSearch from '@/components/features/search/GlobalSearch';
import EmailVerificationModal from '@/components/features/auth/EmailVerificationModal';
import { NotificationToastContainer } from '@/components/features/notifications/NotificationToast';
import { useAuthStore } from '@/stores/authStore';
import { useGlobalSearchShortcut } from '@/hooks/useGlobalSearchShortcut';
import { usePusherNotifications } from '@/hooks/usePusherNotifications';
import type { Notification } from '@/types/notifications';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const router = useRouter();
  const { user, isLoading } = useAuthStore();
  const { isOpen, open, close } = useGlobalSearchShortcut();
  const [showVerificationModal, setShowVerificationModal] = useState(false);
  const [toastNotifications, setToastNotifications] = useState<Notification[]>([]);
  const [isNotificationPanelOpen, setIsNotificationPanelOpen] = useState(false);

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

  // Track notification panel state from AppHeader
  useEffect(() => {
    const handlePanelOpen = () => setIsNotificationPanelOpen(true);
    const handlePanelClose = () => setIsNotificationPanelOpen(false);

    window.addEventListener('notification-panel-opened', handlePanelOpen);
    window.addEventListener('notification-panel-closed', handlePanelClose);

    return () => {
      window.removeEventListener('notification-panel-opened', handlePanelOpen);
      window.removeEventListener('notification-panel-closed', handlePanelClose);
    };
  }, []);

  // Subscribe to Pusher notifications and trigger toasts
  usePusherNotifications({
    userId: user?.id?.toString() || null,
    enabled: !!user,
    onNotification: (notification: Notification) => {
      // Don't show toast if notification panel is open
      if (isNotificationPanelOpen) {
        return;
      }

      // Don't show toast if page is not visible
      if (typeof document !== 'undefined' && document.hidden) {
        return;
      }

      // Add to toast notifications
      setToastNotifications((prev) => [notification, ...prev]);
    },
  });

  // Redirect unauthenticated users to login
  // Redirect unverified users to verification pending page
  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login?returnUrl=' + encodeURIComponent(window.location.pathname));
    } else if (!isLoading && user && !user.email_verified) {
      // Store redirect intent so user goes to original destination after verification
      const returnUrl = encodeURIComponent(window.location.pathname);
      router.push(`/verify-email/pending?email=${encodeURIComponent(user.email)}&returnUrl=${returnUrl}`);
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

  const handleDismissToast = (id: string) => {
    setToastNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  const handleNavigateFromToast = (notification: Notification) => {
    // Map notification type to route
    const routes: Record<string, string> = {
      vault_invite: `/vaults/${notification.data?.vault_id}`,
      member_joined: `/vaults/${notification.data?.vault_id}/members`,
      source_added: `/vaults/${notification.data?.vault_id}/sources/${notification.data?.source_id}`,
      annotation_reply: `/vaults/${notification.data?.vault_id}/sources/${notification.data?.source_id}#annotation-${notification.data?.annotation_id}`,
      mention: `/vaults/${notification.data?.vault_id}/sources/${notification.data?.source_id}#annotation-${notification.data?.annotation_id}`,
    };

    const route = routes[notification.type];
    if (route) {
      router.push(route);
    }
  };

  return (
    <div className="min-h-screen bg-[#030304]">
      <AppHeader onSearchClick={open} />
      <div className="flex">
        <Suspense fallback={<div className="hidden lg:block lg:w-64" />}>
          <Sidebar />
        </Suspense>
        <main className="flex-1 min-h-[calc(100vh-72px)]">{children}</main>
      </div>
      <OnboardingFlow />
      <GlobalSearch isOpen={isOpen} onClose={close} />
      <EmailVerificationModal
        isOpen={showVerificationModal}
        onClose={() => setShowVerificationModal(false)}
      />
      {/* Toast notifications for real-time Pusher events */}
      <NotificationToastContainer
        notifications={toastNotifications}
        onDismiss={handleDismissToast}
        onNavigate={handleNavigateFromToast}
      />
    </div>
  );
}
