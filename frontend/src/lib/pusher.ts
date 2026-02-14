import Pusher from 'pusher-js';
import api from '@/lib/api';

/**
 * Pusher client for browser push notifications
 *
 * Handles connection to Pusher for real-time notifications:
 * - notification events
 * - badge_update events
 */

// Pusher authorization data type (matches pusher-js internal types)
interface ChannelAuthorizationData {
  auth: string;
  channel_data?: string;
  shared_secret?: string;
}

let pusherInstance: Pusher | null = null;

/**
 * Initialize Pusher client
 * Returns existing instance if already initialized
 */
export function initializePusher(): Pusher | null {
  if (pusherInstance) {
    return pusherInstance;
  }

  const key = process.env.NEXT_PUBLIC_PUSHER_KEY;
  const cluster = process.env.NEXT_PUBLIC_PUSHER_CLUSTER;

  if (!key || !cluster) {
    console.warn('Pusher credentials not configured. Real-time notifications disabled.');
    return null;
  }

  pusherInstance = new Pusher(key, {
    cluster,
    // Custom authorizer for private channel authentication
    authorizer: (channel) => {
      return {
        authorize: (socketId: string, callback: (error: Error | null, authData: ChannelAuthorizationData | null) => void) => {
          // Call our auth endpoint with channel name and socket ID
          api.post<ChannelAuthorizationData>(
            '/notifications/pusher/auth/',
            {
              channel_name: channel.name,
              socket_id: socketId,
            }
          ).then((response) => {
            callback(null, response.data);
          }).catch((error) => {
            console.error('Pusher auth error:', error);
            callback(error as Error, null);
          });
        },
      };
    },
  });

  return pusherInstance;
}

/**
 * Subscribe to user's private notification channel
 * Channel name format: private-user-{userId}
 */
export function subscribeToUserChannel(userId: number | string) {
  const pusher = initializePusher();

  if (!pusher) {
    return null;
  }

  const channelName = `private-user-${userId}`;
  return pusher.subscribe(channelName);
}

/**
 * Unsubscribe from user's private channel
 */
export function unsubscribeFromUserChannel(userId: number | string): void {
  if (!pusherInstance) {
    return;
  }

  const channelName = `private-user-${userId}`;
  pusherInstance.unsubscribe(channelName);
}

/**
 * Disconnect Pusher client
 * Should be called on logout
 */
export function disconnectPusher(): void {
  if (pusherInstance) {
    pusherInstance.disconnect();
    pusherInstance = null;
  }
}

/**
 * Get or create the Pusher client instance (alias for initializePusher)
 * @returns Pusher client instance or null if not configured
 */
export function getPusherClient(): Pusher | null {
  return initializePusher();
}

/**
 * Request browser notification permission
 * Returns true if permission granted
 */
export async function requestNotificationPermission(): Promise<boolean> {
  if (!('Notification' in window)) {
    console.warn('Browser does not support notifications');
    return false;
  }

  if (Notification.permission === 'granted') {
    return true;
  }

  if (Notification.permission === 'denied') {
    return false;
  }

  const permission = await Notification.requestPermission();
  return permission === 'granted';
}

export default getPusherClient;
