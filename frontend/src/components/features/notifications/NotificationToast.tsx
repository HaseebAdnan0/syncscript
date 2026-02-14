'use client';

import React, { useEffect, useState } from 'react';
import { X, Bell, UserPlus, FileText, MessageCircle, AtSign } from 'lucide-react';
import type { Notification, NotificationType } from '@/types/notifications';

interface NotificationToastProps {
  notification: Notification;
  onDismiss: () => void;
  onNavigate?: (notification: Notification) => void;
}

const typeIcons: Record<NotificationType, React.ComponentType<{ className?: string }>> = {
  vault_invite: Bell,
  member_joined: UserPlus,
  source_added: FileText,
  annotation_reply: MessageCircle,
  mention: AtSign,
};

function truncateText(text: string, maxLength: number = 100): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

export function NotificationToast({ notification, onDismiss, onNavigate }: NotificationToastProps) {
  const [isExiting, setIsExiting] = useState(false);

  // Auto-dismiss after 5 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      handleDismiss();
    }, 5000);

    return () => clearTimeout(timer);
  }, []);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => {
      onDismiss();
    }, 300); // Match animation duration
  };

  const handleClick = () => {
    if (onNavigate) {
      onNavigate(notification);
    }
    handleDismiss();
  };

  const Icon = typeIcons[notification.type];

  return (
    <div
      className={`
        bg-[#0F1115] border border-white/10 rounded-xl shadow-[0_0_20px_-5px_rgba(247,147,26,0.3)]
        p-4 max-w-sm w-full cursor-pointer
        transition-all duration-300 ease-out
        ${isExiting ? 'translate-x-full opacity-0' : 'translate-x-0 opacity-100'}
        hover:border-[#F7931A]/50 hover:-translate-y-1
      `}
      onClick={handleClick}
      role="alert"
      aria-live="polite"
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="flex-shrink-0 mt-0.5">
          <Icon className="w-5 h-5 text-[#F7931A]" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h4 className="font-bold text-white text-sm mb-1">
            {notification.title}
          </h4>
          <p className="text-sm text-[#94A3B8]">
            {truncateText(notification.body, 100)}
          </p>
        </div>

        {/* Dismiss button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            handleDismiss();
          }}
          className="flex-shrink-0 p-1 rounded-lg hover:bg-white/5 transition-colors"
          aria-label="Dismiss notification"
        >
          <X className="w-4 h-4 text-[#94A3B8]" />
        </button>
      </div>
    </div>
  );
}

interface NotificationToastContainerProps {
  notifications: Notification[];
  onDismiss: (id: string) => void;
  onNavigate?: (notification: Notification) => void;
}

export function NotificationToastContainer({
  notifications,
  onDismiss,
  onNavigate,
}: NotificationToastContainerProps) {
  // Stack up to 3 toasts, newest at bottom
  const visibleNotifications = notifications.slice(0, 3);

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col-reverse gap-3 pointer-events-none">
      {visibleNotifications.map((notification) => (
        <div key={notification.id} className="pointer-events-auto">
          <NotificationToast
            notification={notification}
            onDismiss={() => onDismiss(notification.id)}
            onNavigate={onNavigate}
          />
        </div>
      ))}
    </div>
  );
}
