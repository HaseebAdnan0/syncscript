'use client';

import { AppHeader } from '@/components/features/notifications/AppHeader';
import { Sidebar } from '@/components/features/dashboard/Sidebar';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
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
