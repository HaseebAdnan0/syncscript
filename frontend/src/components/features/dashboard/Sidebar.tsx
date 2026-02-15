'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname, useSearchParams } from 'next/navigation';
import {
  LayoutDashboard,
  Folder,
  Users,
  Settings,
  Menu,
  X,
  ChevronLeft,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface SidebarProps {
  className?: string;
}

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  {
    label: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    label: 'My Vaults',
    href: '/vaults',
    icon: Folder,
  },
  {
    label: 'Shared With Me',
    href: '/vaults?filter=shared',
    icon: Users,
  },
  {
    label: 'Settings',
    href: '/settings',
    icon: Settings,
  },
];

export function Sidebar({ className }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const toggleCollapse = () => setIsCollapsed(!isCollapsed);
  const toggleMobile = () => setIsMobileOpen(!isMobileOpen);

  // Helper to check if a nav item is active
  const isItemActive = (item: NavItem): boolean => {
    // Handle "Shared With Me" link specifically
    if (item.href === '/vaults?filter=shared') {
      return pathname === '/vaults' && searchParams.get('filter') === 'shared';
    }
    // Handle "My Vaults" - should be active only when on /vaults without filter=shared
    if (item.href === '/vaults') {
      return pathname === '/vaults' && searchParams.get('filter') !== 'shared';
    }
    // Default: exact match or path prefix match
    return pathname === item.href ||
      (item.href !== '/dashboard' && pathname?.startsWith(item.href));
  };

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={toggleMobile}
        className="fixed top-20 left-4 z-50 lg:hidden p-2 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-transform"
        aria-label="Toggle sidebar"
      >
        {isMobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>

      {/* Mobile overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={toggleMobile}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-[72px] left-0 h-[calc(100vh-72px)] bg-[#0F1115] border-r border-white/10 transition-all duration-300 z-40',
          isCollapsed && 'lg:w-20',
          !isCollapsed && 'lg:w-64',
          isMobileOpen && 'translate-x-0',
          !isMobileOpen && '-translate-x-full lg:translate-x-0',
          'w-64',
          className
        )}
      >
        {/* Collapse button (desktop only) */}
        <button
          onClick={toggleCollapse}
          className="hidden lg:flex absolute -right-3 top-6 h-6 w-6 items-center justify-center rounded-full bg-[#F7931A] text-white shadow-[0_0_15px_-3px_rgba(247,147,26,0.5)] hover:scale-110 transition-transform"
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <ChevronLeft
            className={cn(
              'h-4 w-4 transition-transform',
              isCollapsed && 'rotate-180'
            )}
          />
        </button>

        {/* Navigation items */}
        <nav className="p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = isItemActive(item);

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsMobileOpen(false)}
                className={cn(
                  'flex items-center gap-3 px-4 py-3 rounded-lg transition-all group',
                  isActive &&
                    'bg-gradient-to-r from-[#F7931A]/20 to-[#FFD600]/10 border-l-2 border-[#F7931A]',
                  !isActive && 'hover:bg-white/5',
                  isCollapsed && 'lg:justify-center lg:px-2'
                )}
              >
                <Icon
                  className={cn(
                    'h-5 w-5 transition-colors flex-shrink-0',
                    isActive && 'text-[#F7931A]',
                    !isActive && 'text-white/60 group-hover:text-white'
                  )}
                />
                <span
                  className={cn(
                    'text-sm font-medium transition-colors',
                    isActive && 'text-white',
                    !isActive && 'text-white/60 group-hover:text-white',
                    isCollapsed && 'lg:hidden'
                  )}
                >
                  {item.label}
                </span>
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Spacer to prevent content overlap on desktop */}
      <div
        className={cn(
          'hidden lg:block transition-all duration-300',
          isCollapsed && 'lg:w-20',
          !isCollapsed && 'lg:w-64'
        )}
      />
    </>
  );
}
