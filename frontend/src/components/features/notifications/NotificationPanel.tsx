'use client';

import { Bell } from 'lucide-react';
import { useNotifications } from '@/hooks/useNotifications';
import { formatDistanceToNow } from 'date-fns';
import type { Notification } from '@/lib/api/notifications';

export function NotificationPanel() {
  const {
    notifications,
    isLoadingNotifications,
    markAsRead,
    markAllAsRead,
    isMarkingAllAsRead
  } = useNotifications();

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.is_read) {
      markAsRead(notification.id);
    }
  };

  const handleMarkAllAsRead = () => {
    markAllAsRead();
  };

  // Get icon for notification type
  const getNotificationIcon = () => {
    // Simple icon mapping - can be expanded later
    return <Bell className="h-4 w-4 text-[#F7931A]" />;
  };

  return (
    <div className="absolute right-0 top-full mt-2 w-full sm:w-96 backdrop-blur-lg bg-white/5 border border-white/10 rounded-2xl shadow-xl overflow-hidden z-50">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <h3 className="text-white font-bold text-sm uppercase tracking-wider">
          Notifications
        </h3>
        {notifications.length > 0 && (
          <button
            onClick={handleMarkAllAsRead}
            disabled={isMarkingAllAsRead}
            className="text-xs text-[#F7931A] hover:text-[#FFD600] transition-colors uppercase tracking-wide font-medium disabled:opacity-50"
          >
            Mark all read
          </button>
        )}
      </div>

      {/* Notification List */}
      <div className="max-h-[500px] overflow-y-auto">
        {isLoadingNotifications ? (
          <div className="p-8 text-center text-muted">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-[#F7931A] border-t-transparent mx-auto"></div>
          </div>
        ) : notifications.length > 0 ? (
          <div className="divide-y divide-white/5">
            {notifications.slice(0, 20).map((notification) => (
              <button
                key={notification.id}
                onClick={() => handleNotificationClick(notification)}
                className={`w-full text-left p-4 hover:bg-white/5 transition-colors relative ${
                  !notification.is_read ? 'border-l-2 border-[#F7931A]' : ''
                }`}
              >
                <div className="flex gap-3">
                  {/* Icon */}
                  <div className="flex-shrink-0 mt-1">
                    {getNotificationIcon()}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm ${
                      notification.is_read ? 'text-muted' : 'text-white font-medium'
                    }`}>
                      {notification.message}
                    </p>
                    <p className="text-xs text-muted mt-1">
                      {formatDistanceToNow(new Date(notification.created_at), {
                        addSuffix: true
                      })}
                    </p>
                  </div>

                  {/* Read indicator */}
                  {!notification.is_read && (
                    <div className="flex-shrink-0">
                      <div className="h-2 w-2 rounded-full bg-[#F7931A]"></div>
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center">
            <Bell className="h-12 w-12 text-muted mx-auto mb-3 opacity-50" />
            <p className="text-muted text-sm">No notifications yet</p>
            <p className="text-muted text-xs mt-1">
              You'll see updates here when collaborators interact with your vaults
            </p>
          </div>
        )}
      </div>

      {/* Footer with settings link */}
      <div className="border-t border-white/10 p-3 text-center">
        <a
          href="/settings/notifications"
          className="text-xs text-[#F7931A] hover:text-[#FFD600] transition-colors uppercase tracking-wide font-medium"
        >
          Notification Settings
        </a>
      </div>
    </div>
  );
}
