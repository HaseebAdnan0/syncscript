'use client';

import { useState, useRef, useEffect } from 'react';
import { Bell, User, LogOut } from 'lucide-react';
import { useNotifications } from '@/hooks/useNotifications';
import { UnreadBadge } from './UnreadBadge';
import { NotificationPanel } from './NotificationPanel';
import { ConnectionStatus } from './ConnectionStatus';
import { useVaultSocket } from '@/hooks/useVaultSocket';
import { useAuthStore } from '@/stores/authStore';
import { useAuth } from '@/hooks/useAuth';
import { useToast } from '@/hooks/useToast';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface AppHeaderProps {
  /** Optional vault ID to show connection status for */
  vaultId?: string;
}

export function AppHeader({ vaultId }: AppHeaderProps) {
  const [isNotificationPanelOpen, setIsNotificationPanelOpen] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const { unreadCount } = useNotifications();
  // Always call hook - it handles undefined vaultId internally
  const { status } = useVaultSocket({ vaultId });
  const { user } = useAuthStore();
  const { logout } = useAuth();
  const { toast } = useToast();
  const router = useRouter();
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

  const handleLogout = async () => {
    setIsLoggingOut(true);
    const { success } = await logout();
    setIsLoggingOut(false);

    if (success) {
      toast({
        title: 'Logged out successfully',
        description: 'You have been signed out of your account.',
      });
      router.push('/login');
    } else {
      toast({
        title: 'Logout failed',
        description: 'An error occurred while logging out. Please try again.',
      });
    }
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

          {/* Right section: Notifications + User Menu + Connection Status */}
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

            {/* User Dropdown Menu */}
            {user && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button
                    className="flex items-center gap-3 p-2 rounded-full hover:bg-white/5 transition-colors focus:outline-none focus:ring-2 focus:ring-[#F7931A] focus:ring-offset-2 focus:ring-offset-[#0F1115]"
                    aria-label="User menu"
                  >
                    {/* Avatar Circle */}
                    <div className="h-8 w-8 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center shadow-[0_0_15px_-3px_rgba(234,88,12,0.4)]">
                      <User className="h-4 w-4 text-white" />
                    </div>
                    {/* User Name */}
                    <span className="text-sm text-white font-medium hidden sm:block">
                      {user.first_name || user.email}
                    </span>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel className="text-white/80">
                    {user.email}
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link
                      href="/profile"
                      className="cursor-pointer text-white hover:text-[#F7931A]"
                    >
                      <User className="mr-2 h-4 w-4" />
                      Profile
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={handleLogout}
                    disabled={isLoggingOut}
                    className="cursor-pointer text-white hover:text-red-400 focus:text-red-400"
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    {isLoggingOut ? 'Logging out...' : 'Logout'}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}

            {/* Connection Status (only shown when vaultId is provided) */}
            {vaultId && <ConnectionStatus status={status} />}
          </div>
        </div>
      </div>
    </header>
  );
}
