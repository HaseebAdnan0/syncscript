import { api } from '@/lib/api';

// ============================================================================
// Types
// ============================================================================

export interface DashboardStats {
  vaults_count: number;
  sources_count: number;
  annotations_this_week: number;
}

export interface RecentVault {
  id: number;
  name: string;
  description: string;
  last_accessed_at: string | null;
  sources_count: number;
  role: 'OWNER' | 'CONTRIBUTOR' | 'VIEWER';
}

export interface ActivityFeedItem {
  id: number;
  action: string;
  description: string;
  actor: {
    id: number;
    name: string;
    email: string;
    avatar_url?: string;
  } | null;
  vault_id: number;
  vault_name: string;
  target_type: string;
  target_id: number;
  created_at: string;
}

export interface SourcesTimelineDataPoint {
  date: string;
  count: number;
}

export interface SourceTypeDataPoint {
  type: string;
  count: number;
  percentage: number;
}

export interface TopCollaborator {
  user_id: number;
  name: string;
  avatar_url?: string;
  contributions_count: number;
}

// ============================================================================
// Dashboard Stats
// ============================================================================

/**
 * Get dashboard stats for the current user
 * Returns: vaults count, sources count, annotations this week
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  const response = await api.get<DashboardStats>('/dashboard/stats/');
  return response.data;
}

// ============================================================================
// Recent Vaults
// ============================================================================

/**
 * Get the 3 most recently accessed vaults for the current user
 */
export async function getRecentVaults(): Promise<RecentVault[]> {
  const response = await api.get<RecentVault[]>('/dashboard/recent-vaults/');
  return response.data;
}

// ============================================================================
// Activity Feed
// ============================================================================

/**
 * Get recent activity across all accessible vaults
 * @param limit Number of items to return (default 10, max 50)
 */
export async function getActivityFeed(limit?: number): Promise<ActivityFeedItem[]> {
  const params = limit ? { limit } : {};
  const response = await api.get<ActivityFeedItem[]>('/dashboard/activity/', { params });
  return response.data;
}

// ============================================================================
// Analytics
// ============================================================================

/**
 * Get sources added per day for the last 30 days
 */
export async function getSourcesTimeline(): Promise<SourcesTimelineDataPoint[]> {
  const response = await api.get<SourcesTimelineDataPoint[]>('/dashboard/analytics/sources-timeline/');
  return response.data;
}

/**
 * Get breakdown of sources by type with counts and percentages
 */
export async function getSourceTypes(): Promise<SourceTypeDataPoint[]> {
  const response = await api.get<SourceTypeDataPoint[]>('/dashboard/analytics/source-types/');
  return response.data;
}

/**
 * Get top 5 collaborators by contribution count
 */
export async function getTopCollaborators(): Promise<TopCollaborator[]> {
  const response = await api.get<TopCollaborator[]>('/dashboard/analytics/top-collaborators/');
  return response.data;
}

// ============================================================================
// Notifications (re-export from notifications.ts for convenience)
// ============================================================================

export {
  getNotifications,
  getUnreadCount,
  markAsRead as markNotificationRead,
  markAllAsRead as markAllNotificationsRead,
} from './notifications';
