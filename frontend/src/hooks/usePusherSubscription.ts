import { useEffect } from 'react';
import {
  subscribeToUserChannel,
  unsubscribeFromUserChannel,
  disconnectPusher,
} from '@/lib/pusher';

/**
 * Hook to manage Pusher subscription for browser push notifications
 * Should be called once at app level (e.g., in layout or root component)
 *
 * @param userId - Current logged-in user ID
 * @param enabled - Whether push notifications are enabled (from user preferences)
 */
export function usePusherSubscription(userId: number | null | undefined, enabled: boolean) {
  useEffect(() => {
    // Only subscribe if user is logged in and push enabled
    if (!userId || !enabled) {
      return;
    }

    try {
      subscribeToUserChannel(userId);
    } catch (error) {
      console.error('Failed to subscribe to Pusher channel:', error);
    }

    // Cleanup: unsubscribe on unmount or when dependencies change
    return () => {
      if (userId) {
        unsubscribeFromUserChannel(userId);
      }
    };
  }, [userId, enabled]);

  // Disconnect Pusher when component unmounts (app closes)
  useEffect(() => {
    return () => {
      disconnectPusher();
    };
  }, []);
}
