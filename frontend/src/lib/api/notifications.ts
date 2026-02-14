import { api } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/types/api';
import type { Notification } from '@/types/notifications';

export type { Notification };

export type NotificationListResponse = PaginatedResponse<Notification>;

export interface UnreadCountResponse {
  unread_count: number;
}

/**
 * Fetch paginated list of notifications for the current user
 */
export async function getNotifications(params?: {
  page?: number;
  limit?: number;
  is_read?: boolean;
}): Promise<PaginatedResponse<Notification>> {
  const response = await api.get<PaginatedResponse<Notification>>('/notifications/', { params });
  return response.data;
}

/**
 * Mark a single notification as read
 */
export async function markAsRead(notificationId: string | number): Promise<Notification> {
  const response = await api.patch<Notification>(`/notifications/${notificationId}/read/`);
  return response.data;
}

/**
 * Mark all notifications as read for the current user
 */
export async function markAllAsRead(): Promise<{ message: string; updated_count: number }> {
  const response = await api.post<{ message: string; updated_count: number }>(
    '/notifications/mark-all-read/'
  );
  return response.data;
}

/**
 * Get unread notification count for the current user
 */
export async function getUnreadCount(): Promise<number> {
  const response = await api.get<UnreadCountResponse>('/notifications/unread-count/');
  return response.data.unread_count;
}

export interface NotificationPreferences {
  notifications_enabled: boolean;
  push_notifications_enabled: boolean;
  sound_enabled: boolean;
}

/**
 * Get user notification preferences
 */
export async function getPreferences(): Promise<NotificationPreferences> {
  const response = await api.get<NotificationPreferences>('/users/me/preferences/');
  return response.data;
}

/**
 * Update user notification preferences
 */
export async function updatePreferences(
  preferences: Partial<NotificationPreferences>
): Promise<NotificationPreferences> {
  const response = await api.patch<NotificationPreferences>('/users/me/preferences/', preferences);
  return response.data;
}
