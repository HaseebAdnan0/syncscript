'use client';

import { Bell } from 'lucide-react';

interface NotificationBellProps {
  unreadCount: number;
  onClick: () => void;
}

export function NotificationBell({ unreadCount, onClick }: NotificationBellProps) {
  const displayCount = unreadCount > 9 ? '9+' : unreadCount.toString();
  const showBadge = unreadCount > 0;

  return (
    <button
      onClick={onClick}
      className="relative p-2 hover:bg-white/5 rounded-full transition-colors"
      aria-label={`Notifications (${unreadCount} unread)`}
    >
      <Bell className="w-5 h-5 text-white/80 hover:text-white" />
      {showBadge && (
        <span className="absolute -top-1 -right-1 bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white text-xs font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
          {displayCount}
        </span>
      )}
    </button>
  );
}
