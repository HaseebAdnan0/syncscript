'use client';

import { useState, useRef, useEffect } from 'react';
import { Bell } from 'lucide-react';
import { useNotifications } from '@/hooks/useNotifications';
import { UnreadBadge } from './UnreadBadge';
import { NotificationPanel } from './NotificationPanel';
import { ConnectionStatus } from './ConnectionStatus';
import { useVaultSocket } from '@/hooks/useVaultSocket';
import Link from 'next/link';

interface AppHeaderProps {
  /** Optional vault ID to show connection status for */
  vaultId?: string;
}

export function AppHeader({ vaultId }: AppHeaderProps) {
  const [isNotificationPanelOpen, setIsNotificationPanelOpen] = useState(false);
  const { unreadCount } = useNotifications();
  // Always call hook, but pass undefined when vaultId is not provided
  const { status } = useVaultSocket(vaultId ? { vaultId } : { vaultId: '' });
  const panelRef = useRef<HTMLDivElement>(null);
  const bellButtonRef = useRef<HTMLButtonElement>(null);

  // Close panel when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        isNotificationPanelOpen &&
        panelRef.current &&
        bellButtonRef.current &&
        !panelRef.current.contains(event.target as Node) &&
        !bellButtonRef.current.contains(event.target as Node)
      ) {
        setIsNotificationPanelOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isNotificationPanelOpen]);

  // Close panel on Escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isNotificationPanelOpen) {
        setIsNotificationPanelOpen(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isNotificationPanelOpen]);

  const toggleNotificationPanel = () => {
    setIsNotificationPanelOpen((prev) => !prev);
  };

  return (
    <header className="sticky top-0 z-40 w-full backdrop-blur-lg bg-[#0F1115]/80 border-b border-white/10">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo / Brand */}
          <Link href="/vaults" className="flex items-center gap-3 group">
            <div className="h-10 w-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] group-hover:scale-105 transition-transform">
              <span className="text-white font-bold text-lg">S</span>
            </div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">
              SyncScript
            </h1>
          </Link>

          {/* Right section: Notifications + Connection Status */}
          <div className="flex items-center gap-6">
            {/* Notification Bell */}
            <div className="relative" ref={panelRef}>
              <button
                ref={bellButtonRef}
                onClick={toggleNotificationPanel}
                className="relative p-2 rounded-full hover:bg-white/5 transition-colors focus:outline-none focus:ring-2 focus:ring-[#F7931A] focus:ring-offset-2 focus:ring-offset-[#0F1115]"
                aria-label="Notifications"
                aria-expanded={isNotificationPanelOpen}
                aria-haspopup="true"
              >
                <Bell className="h-6 w-6 text-white" />
                <UnreadBadge count={unreadCount} />
              </button>

              {/* Notification Panel Dropdown */}
              {isNotificationPanelOpen && <NotificationPanel />}
            </div>

            {/* Connection Status (only shown when vaultId is provided) */}
            {vaultId && <ConnectionStatus status={status} />}
          </div>
        </div>
      </div>
    </header>
  );
}
