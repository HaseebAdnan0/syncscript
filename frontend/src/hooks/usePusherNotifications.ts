'use client';

import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { Channel } from 'pusher-js';
import { getPusherClient } from '@/lib/pusher';
import type { Notification } from '@/types/notifications';

interface UsePusherNotificationsOptions {
  userId: string | null;
  enabled?: boolean;
}

/**
 * Hook to subscribe to real-time notifications via Pusher
 * Listens for 'notification' and 'badge_update' events from private user channel
 */
export function usePusherNotifications({ userId, enabled = true }: UsePusherNotificationsOptions) {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!userId || !enabled) {
      return;
    }

    const pusher = getPusherClient();
    if (!pusher) {
      console.warn('Pusher client not configured');
      return;
    }

    const channelName = `private-user-${userId}`;
    let channel: Channel | null = null;

    try {
      // Subscribe to private user channel
      channel = pusher.subscribe(channelName);

      // Listen for new notification events
      channel.bind('notification', (notification: Notification) => {
        // Update React Query cache with new notification
        queryClient.setQueryData<{ results: Notification[]; count: number }>(
          ['notifications'],
          (oldData) => {
            if (!oldData) {
              return {
                results: [notification],
                count: 1,
              };
            }
            return {
              ...oldData,
              results: [notification, ...oldData.results],
              count: oldData.count + 1,
            };
          }
        );
      });

      // Listen for badge update events
      channel.bind('badge_update', (data: { count: number }) => {
        // Update unread count in React Query cache
        queryClient.setQueryData(['notifications', 'unread-count'], data.count);
      });
    } catch (error) {
      console.error('Failed to subscribe to Pusher channel:', error);
    }

    // Cleanup: unsubscribe on unmount
    return () => {
      if (channel) {
        channel.unbind_all();
        pusher.unsubscribe(channelName);
      }
    };
  }, [userId, enabled, queryClient]);
}
