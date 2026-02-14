import Pusher from 'pusher-js';

/**
 * Pusher client for browser push notifications
 *
 * Handles connection to Pusher for high-priority notifications:
 * - member.joined events
 * - mention.created events
 */

let pusherInstance: Pusher | null = null;

/**
 * Initialize Pusher client
 * Returns existing instance if already initialized
 */
export function initializePusher(): Pusher {
  if (pusherInstance) {
    return pusherInstance;
  }

  const key = process.env.NEXT_PUBLIC_PUSHER_KEY;
  const cluster = process.env.NEXT_PUBLIC_PUSHER_CLUSTER;

  if (!key || !cluster) {
    throw new Error('Pusher configuration missing. Set NEXT_PUBLIC_PUSHER_KEY and NEXT_PUBLIC_PUSHER_CLUSTER');
  }

  pusherInstance = new Pusher(key, {
    cluster,
    authEndpoint: `${process.env.NEXT_PUBLIC_API_URL}/pusher/auth`,
    auth: {
      headers: {
        Authorization: `Bearer ${getAccessToken()}`,
      },
    },
  });

  return pusherInstance;
}

/**
 * Get access token from localStorage
 * Used for Pusher authentication
 */
function getAccessToken(): string {
  if (typeof window === 'undefined') {
    return '';
  }
  return localStorage.getItem('access_token') || '';
}

/**
 * Subscribe to user's private notification channel
 * Channel name format: private-user-{userId}
 */
export function subscribeToUserChannel(userId: number): void {
  const pusher = initializePusher();
  const channelName = `private-user-${userId}`;

  const channel = pusher.subscribe(channelName);

  // Handle member.joined events
  channel.bind('member.joined', (data: {
    vault_id: number;
    vault_name: string;
    member_name: string;
    member_role: string;
  }) => {
    showBrowserNotification({
      title: 'New Vault Member',
      body: `${data.member_name} joined "${data.vault_name}" as ${data.member_role}`,
      data: {
        type: 'member.joined',
        vaultId: data.vault_id,
      },
    });
  });

  // Handle mention.created events
  channel.bind('mention.created', (data: {
    vault_id: number;
    vault_name: string;
    source_title?: string;
    mentioned_by: string;
    annotation_text: string;
  }) => {
    showBrowserNotification({
      title: `You were mentioned in "${data.vault_name}"`,
      body: `${data.mentioned_by}: ${data.annotation_text.slice(0, 100)}${data.annotation_text.length > 100 ? '...' : ''}`,
      data: {
        type: 'mention.created',
        vaultId: data.vault_id,
      },
    });
  });
}

/**
 * Unsubscribe from user's private channel
 */
export function unsubscribeFromUserChannel(userId: number): void {
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

/**
 * Show native browser notification
 * Focuses app tab when notification is clicked
 */
function showBrowserNotification(options: {
  title: string;
  body: string;
  data?: any;
}): void {
  if (!('Notification' in window) || Notification.permission !== 'granted') {
    return;
  }

  const notification = new Notification(options.title, {
    body: options.body,
    icon: '/favicon.ico',
    badge: '/favicon.ico',
    data: options.data,
  });

  // Focus app tab when notification clicked
  notification.onclick = () => {
    window.focus();
    notification.close();

    // Navigate to vault if data includes vaultId
    if (options.data?.vaultId) {
      window.location.href = `/vaults/${options.data.vaultId}`;
    }
  };
}

/**
 * Check if browser notifications are supported
 */
export function isBrowserNotificationSupported(): boolean {
  return 'Notification' in window;
}

/**
 * Get current notification permission status
 */
export function getNotificationPermission(): NotificationPermission | null {
  if (!('Notification' in window)) {
    return null;
  }
  return Notification.permission;
}
