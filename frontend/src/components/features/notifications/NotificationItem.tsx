'use client';

import React from 'react';
import {
  Bell,
  UserPlus,
  FileText,
  MessageCircle,
  AtSign,
} from 'lucide-react';
import type { Notification } from '@/types/notifications';

interface NotificationItemProps {
  notification: Notification;
  onClick?: (notification: Notification) => void;
}

// Map notification types to icons
const getNotificationIcon = (type: Notification['type']) => {
  const iconProps = { className: 'h-5 w-5 text-[#F7931A]' };

  switch (type) {
    case 'vault_invite':
      return <Bell {...iconProps} />;
    case 'member_joined':
      return <UserPlus {...iconProps} />;
    case 'source_added':
      return <FileText {...iconProps} />;
    case 'annotation_reply':
      return <MessageCircle {...iconProps} />;
    case 'mention':
      return <AtSign {...iconProps} />;
    default:
      return <Bell {...iconProps} />;
  }
};

// Format relative timestamp
const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) {
    return 'just now';
  } else if (diffMins < 60) {
    return `${diffMins} ${diffMins === 1 ? 'minute' : 'minutes'} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} ${diffHours === 1 ? 'hour' : 'hours'} ago`;
  } else if (diffDays < 7) {
    return `${diffDays} ${diffDays === 1 ? 'day' : 'days'} ago`;
  } else {
    return date.toLocaleDateString();
  }
};

// Truncate long text
const truncateText = (text: string, maxLength: number = 100): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength).trim() + '...';
};

export default function NotificationItem({
  notification,
  onClick,
}: NotificationItemProps) {
  const isUnread = !notification.is_read;

  return (
    <div
      onClick={() => onClick?.(notification)}
      className={`
        flex items-start gap-3 p-4
        cursor-pointer
        transition-all duration-300
        hover:bg-white/5
        border-b border-white/10
        ${isUnread ? 'bg-[#F7931A]/5' : ''}
      `}
    >
      {/* Icon */}
      <div className="flex-shrink-0 mt-1">
        {getNotificationIcon(notification.type)}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {/* Title */}
        <div className="flex items-start justify-between gap-2">
          <h4 className="text-sm font-bold text-white">
            {notification.title}
          </h4>
          {isUnread && (
            <div className="flex-shrink-0 w-2 h-2 bg-gradient-to-r from-[#EA580C] to-[#F7931A] rounded-full mt-1" />
          )}
        </div>

        {/* Body preview */}
        <p className="text-sm text-[#94A3B8] mt-1">
          {truncateText(notification.body)}
        </p>

        {/* Timestamp */}
        <p className="text-xs text-[#94A3B8] mt-2">
          {formatRelativeTime(notification.created_at)}
        </p>
      </div>
    </div>
  );
}
