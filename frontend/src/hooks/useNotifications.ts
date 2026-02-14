import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef } from 'react';
import type { PaginatedResponse } from '@/lib/types/api';
import {
  getNotifications,
  markAsRead,
  markAllAsRead,
  getUnreadCount,
  type Notification,
} from '@/lib/api/notifications';

const NOTIFICATIONS_QUERY_KEY = ['notifications'];
const UNREAD_COUNT_QUERY_KEY = ['notifications', 'unread-count'];

interface UseNotificationsOptions {
  /** Enable polling for unread count (default: true) */
  enablePolling?: boolean;
  /** Polling interval in milliseconds (default: 60000 = 1 minute) */
  pollingInterval?: number;
  /** Initial page to fetch (default: 1) */
  page?: number;
  /** Number of notifications per page (default: 20) */
  limit?: number;
  /** Filter by read status (default: undefined = all) */
  isRead?: boolean;
}

/**
 * Hook for managing notifications with TanStack Query
 * Provides notifications list, unread count, and mutation functions
 * Automatically polls for unread count when tab is visible
 */
export function useNotifications(options: UseNotificationsOptions = {}) {
  const {
    enablePolling = true,
    pollingInterval = 60000, // 60 seconds
    page = 1,
    limit = 20,
    isRead,
  } = options;

  const queryClient = useQueryClient();
  const isVisibleRef = useRef(true);

  // Track document visibility to pause polling when tab not visible
  useEffect(() => {
    const handleVisibilityChange = () => {
      isVisibleRef.current = !document.hidden;
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  // Fetch notifications list
  const {
    data: notificationsData,
    isLoading: isLoadingNotifications,
    error: notificationsError,
    refetch: refetchNotifications,
  } = useQuery<PaginatedResponse<Notification>>({
    queryKey: [...NOTIFICATIONS_QUERY_KEY, { page, limit, isRead }],
    queryFn: () => getNotifications({ page, limit, is_read: isRead }),
  });

  // Fetch unread count with polling
  const {
    data: unreadCount = 0,
    isLoading: isLoadingUnreadCount,
    error: unreadCountError,
    refetch: refetchUnreadCount,
  } = useQuery<number>({
    queryKey: UNREAD_COUNT_QUERY_KEY,
    queryFn: getUnreadCount,
    refetchInterval: enablePolling
      ? () => {
          // Only poll when tab is visible
          return isVisibleRef.current ? pollingInterval : false;
        }
      : false,
    refetchIntervalInBackground: false, // Never poll in background
  });

  // Mark notification as read mutation
  const markAsReadMutation = useMutation({
    mutationFn: markAsRead,
    onSuccess: (updatedNotification) => {
      // Update notifications list cache
      queryClient.setQueryData<PaginatedResponse<Notification>>(
        [...NOTIFICATIONS_QUERY_KEY, { page, limit, isRead }],
        (old: PaginatedResponse<Notification> | undefined) => {
          if (!old) return old;
          return {
            ...old,
            results: old.results.map((notification: Notification) =>
              notification.id === updatedNotification.id
                ? updatedNotification
                : notification
            ),
          };
        }
      );

      // Decrement unread count
      queryClient.setQueryData<number>(UNREAD_COUNT_QUERY_KEY, (old) => {
        return Math.max(0, (old ?? 0) - 1);
      });
    },
  });

  // Mark all as read mutation
  const markAllAsReadMutation = useMutation({
    mutationFn: markAllAsRead,
    onSuccess: () => {
      // Invalidate and refetch notifications list
      queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_QUERY_KEY });

      // Set unread count to 0
      queryClient.setQueryData<number>(UNREAD_COUNT_QUERY_KEY, 0);
    },
  });

  return {
    // Notifications list
    notifications: notificationsData?.results ?? [],
    notificationsCount: notificationsData?.count ?? 0,
    hasNextPage: !!notificationsData?.next,
    hasPreviousPage: !!notificationsData?.previous,
    isLoadingNotifications,
    notificationsError,

    // Unread count
    unreadCount,
    isLoadingUnreadCount,
    unreadCountError,

    // Actions
    markAsRead: markAsReadMutation.mutate,
    markAllAsRead: markAllAsReadMutation.mutate,
    refetchNotifications,
    refetchUnreadCount,

    // Mutation states
    isMarkingAsRead: markAsReadMutation.isPending,
    isMarkingAllAsRead: markAllAsReadMutation.isPending,
  };
}
