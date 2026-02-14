import { useQuery } from '@tanstack/react-query';
import {
  getDashboardStats,
  getRecentVaults,
  getActivityFeed,
  getSourcesTimeline,
  getSourceTypes,
  getTopCollaborators,
  type DashboardStats,
  type RecentVault,
  type ActivityFeedItem,
  type SourcesTimelineDataPoint,
  type SourceTypeDataPoint,
  type TopCollaborator,
} from '@/lib/api/dashboard';

// ============================================================================
// Query Keys
// ============================================================================

export const dashboardKeys = {
  all: ['dashboard'] as const,
  stats: () => [...dashboardKeys.all, 'stats'] as const,
  recentVaults: () => [...dashboardKeys.all, 'recent-vaults'] as const,
  activity: (limit?: number) => [...dashboardKeys.all, 'activity', { limit }] as const,
  analytics: () => [...dashboardKeys.all, 'analytics'] as const,
  sourcesTimeline: () => [...dashboardKeys.analytics(), 'sources-timeline'] as const,
  sourceTypes: () => [...dashboardKeys.analytics(), 'source-types'] as const,
  topCollaborators: () => [...dashboardKeys.analytics(), 'top-collaborators'] as const,
};

// ============================================================================
// Dashboard Stats Hook
// ============================================================================

/**
 * Fetch dashboard stats: vaults count, sources count, annotations this week
 * Stale time: 5 minutes (stats don't change frequently)
 */
export function useDashboardStats() {
  return useQuery<DashboardStats, Error>({
    queryKey: dashboardKeys.stats(),
    queryFn: getDashboardStats,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// ============================================================================
// Recent Vaults Hook
// ============================================================================

/**
 * Fetch 3 most recently accessed vaults
 * Stale time: 2 minutes (recent vaults change moderately)
 */
export function useRecentVaults() {
  return useQuery<RecentVault[], Error>({
    queryKey: dashboardKeys.recentVaults(),
    queryFn: getRecentVaults,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

// ============================================================================
// Activity Feed Hook
// ============================================================================

/**
 * Fetch recent activity across all accessible vaults
 * @param limit Number of items to return (default 10, max 50)
 * Stale time: 1 minute (activity should be relatively fresh)
 */
export function useActivityFeed(limit?: number) {
  return useQuery<ActivityFeedItem[], Error>({
    queryKey: dashboardKeys.activity(limit),
    queryFn: () => getActivityFeed(limit),
    staleTime: 60 * 1000, // 1 minute
  });
}

// ============================================================================
// Analytics Hooks
// ============================================================================

/**
 * Fetch sources timeline for last 30 days
 * Stale time: 10 minutes (historical data changes infrequently)
 */
export function useSourcesTimeline() {
  return useQuery<SourcesTimelineDataPoint[], Error>({
    queryKey: dashboardKeys.sourcesTimeline(),
    queryFn: getSourcesTimeline,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Fetch source types breakdown with percentages
 * Stale time: 10 minutes (type distribution changes slowly)
 */
export function useSourceTypes() {
  return useQuery<SourceTypeDataPoint[], Error>({
    queryKey: dashboardKeys.sourceTypes(),
    queryFn: getSourceTypes,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Fetch top 5 collaborators by contribution count
 * Stale time: 10 minutes (contributions change gradually)
 */
export function useTopCollaborators() {
  return useQuery<TopCollaborator[], Error>({
    queryKey: dashboardKeys.topCollaborators(),
    queryFn: getTopCollaborators,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

// ============================================================================
// Re-export Notifications Hooks
// ============================================================================

export { useNotifications } from './useNotifications';
