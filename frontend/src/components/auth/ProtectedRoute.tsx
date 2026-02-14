'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading } = useAuthStore();

  useEffect(() => {
    // Only redirect if not loading and not authenticated
    if (!isLoading && !isAuthenticated) {
      // Build return URL with current path
      const returnUrl = encodeURIComponent(pathname);
      router.push(`/login?returnUrl=${returnUrl}`);
    }
  }, [isAuthenticated, isLoading, router, pathname]);

  // Show loading spinner while determining auth state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#030304]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#F7931A]" />
      </div>
    );
  }

  // Don't render children if not authenticated (redirect in progress)
  if (!isAuthenticated) {
    return null;
  }

  // Render children when authenticated
  return <>{children}</>;
}
