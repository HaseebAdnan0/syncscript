'use client';

import React, { useRef, useEffect } from 'react';
import NotificationItem from './NotificationItem';
import type { Notification } from '@/types/notifications';

interface NotificationDropdownProps {
  isOpen: boolean;
  onClose: () => void;
  notifications: Notification[];
  onMarkAllAsRead: () => void;
  onNotificationClick: (notification: Notification) => void;
  onViewAll: () => void;
}

export default function NotificationDropdown({
  isOpen,
  onClose,
  notifications,
  onMarkAllAsRead,
  onNotificationClick,
  onViewAll,
}: NotificationDropdownProps) {
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        onClose();
      }
    };

    // Add delay to avoid immediate closing on bell click
    setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
    }, 0);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  // Limit to 10 most recent notifications
  const displayNotifications = notifications.slice(0, 10);

  return (
    <div
      ref={dropdownRef}
      className="absolute right-0 top-full mt-2 w-96 max-w-[calc(100vw-2rem)] bg-[#0F1115] border border-white/10 rounded-2xl shadow-[0_0_30px_rgba(247,147,26,0.15)] z-50 overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <h3 className="text-base font-bold text-white">Notifications</h3>
        {displayNotifications.length > 0 && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onMarkAllAsRead();
            }}
            className="text-xs text-[#F7931A] hover:text-[#FFD600] font-medium transition-colors"
          >
            Mark all as read
          </button>
        )}
      </div>

      {/* Notification List */}
      <div className="max-h-[500px] overflow-y-auto">
        {displayNotifications.length > 0 ? (
          displayNotifications.map((notification) => (
            <NotificationItem
              key={notification.id}
              notification={notification}
              onClick={(notif) => {
                onNotificationClick(notif);
                onClose();
              }}
            />
          ))
        ) : (
          <div className="p-8 text-center">
            <p className="text-[#94A3B8] text-sm">No notifications yet</p>
          </div>
        )}
      </div>

      {/* Footer */}
      {displayNotifications.length > 0 && (
        <div className="p-3 border-t border-white/10 text-center">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onViewAll();
              onClose();
            }}
            className="text-sm text-[#F7931A] hover:text-[#FFD600] font-medium transition-colors"
          >
            View all notifications
          </button>
        </div>
      )}
    </div>
  );
}
