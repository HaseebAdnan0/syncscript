'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';

interface AuthLayoutProps {
  children: React.ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isLoading } = useAuthStore();

  // Redirect logged-in users to dashboard (except for verify-email pages)
  useEffect(() => {
    const isVerifyEmailPage = pathname?.startsWith('/verify-email');
    const isCallbackPage = pathname?.startsWith('/callback');

    if (!isLoading && user && !isVerifyEmailPage && !isCallbackPage) {
      router.push('/dashboard');
    }
  }, [user, isLoading, pathname, router]);

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#030304] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-white/20 border-t-[#F7931A]" />
          <p className="text-sm text-white/60">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render auth pages if user is logged in (redirecting)
  const isVerifyEmailPage = pathname?.startsWith('/verify-email');
  const isCallbackPage = pathname?.startsWith('/callback');
  if (user && !isVerifyEmailPage && !isCallbackPage) {
    return null;
  }

  return (
    <div className="min-h-screen bg-[#030304] flex items-center justify-center relative overflow-hidden">
      {/* Decorative floating gradients */}
      <div className="absolute top-20 left-10 w-72 h-72 bg-[#F7931A]/10 rounded-full blur-3xl" />
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-[#EA580C]/10 rounded-full blur-3xl" />

      {/* Content */}
      <div className="relative z-10 w-full max-w-md px-4">
        {children}
      </div>
    </div>
  );
}
