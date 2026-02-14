'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AppHeader } from '@/components/features/notifications/AppHeader';
import { Sidebar } from '@/components/features/dashboard/Sidebar';
import { useAuthStore } from '@/stores/authStore';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const router = useRouter();
  const { user, isLoading } = useAuthStore();

  // Redirect unauthenticated users to login
  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login?returnUrl=' + encodeURIComponent(window.location.pathname));
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
      <AppHeader />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 min-h-[calc(100vh-72px)]">{children}</main>
      </div>
    </div>
  );
}
