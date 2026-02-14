'use client';

import { AppHeader } from '@/components/features/notifications/AppHeader';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-[#030304]">
      <AppHeader />
      {children}
    </div>
  );
}
