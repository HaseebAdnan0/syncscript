import { api } from '@/lib/api';
import type { PaginatedResponse } from '@/lib/types/api';

export interface Notification {
  id: number;
  user_id: number;
  vault_id?: number;
  type: 'source.created' | 'source.updated' | 'source.deleted' |
        'annotation.created' | 'annotation.updated' | 'annotation.deleted' |
        'member.joined' | 'member.left' | 'mention.created' | 'vault.updated';
  title: string;
  message: string;
  data?: Record<string, any>;
  is_read: boolean;
  created_at: string;
}

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
export async function markAsRead(notificationId: number): Promise<Notification> {
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
