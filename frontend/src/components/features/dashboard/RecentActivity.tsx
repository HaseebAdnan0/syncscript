"use client";

import { Activity, User, FileText, Folder, MessageSquare } from "lucide-react";
import Link from "next/link";
import { useActivityFeed } from "@/hooks/useDashboard";

interface ActivityItem {
  id: number;
  action: string;
  description: string;
  actor: {
    id: number;
    first_name: string;
    last_name: string;
    email: string;
    name?: string;
  } | null;
  vault_id: number;
  vault_name: string;
  target_type: string;
  target_id: number | null;
  created_at: string;
}

export default function RecentActivity() {
  const { data, isLoading } = useActivityFeed(10);
  const activity: ActivityItem[] = (data || []) as ActivityItem[];

  // Format relative time
  const formatRelativeTime = (timestamp: string): string => {
    const now = new Date();
    const date = new Date(timestamp);
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  // Get icon for activity type
  const getActivityIcon = (action: string) => {
    if (action.includes("vault")) return Folder;
    if (action.includes("source")) return FileText;
    if (action.includes("annotation")) return MessageSquare;
    if (action.includes("member")) return User;
    return Activity;
  };

  // Get link for activity item
  const getActivityLink = (item: ActivityItem): string => {
    if (item.action.includes("vault")) {
      return `/vaults/${item.vault_id}`;
    }
    if (item.action.includes("source") && item.target_id) {
      return `/vaults/${item.vault_id}/sources/${item.target_id}`;
    }
    if (item.action.includes("annotation") && item.target_id) {
      return `/vaults/${item.vault_id}#annotation-${item.target_id}`;
    }
    return `/vaults/${item.vault_id}`;
  };

  // Get user initials for avatar
  const getUserInitials = (actor: ActivityItem["actor"]): string => {
    if (!actor) return "?";
    const first = actor.first_name?.[0] || "";
    const last = actor.last_name?.[0] || "";
    return (first + last).toUpperCase() || actor.email[0].toUpperCase();
  };

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-white">Recent Activity</h2>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="flex items-start gap-4 p-4 bg-[#0F1115] border border-white/10 rounded-xl animate-pulse"
            >
              <div className="w-10 h-10 bg-white/10 rounded-full"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-white/10 rounded w-3/4"></div>
                <div className="h-3 bg-white/10 rounded w-1/4"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Empty state
  if (activity.length === 0) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-white">Recent Activity</h2>
        <div className="flex flex-col items-center justify-center p-12 bg-[#0F1115] border border-white/10 rounded-2xl text-center">
          <Activity className="w-12 h-12 text-white/20 mb-4" />
          <p className="text-white/60 mb-2">No activity yet</p>
          <p className="text-white/40 text-sm">
            Start by adding sources to a vault.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-white">Recent Activity</h2>

      <div className="space-y-3">
        {activity.map((item) => {
          const Icon = getActivityIcon(item.action);
          const link = getActivityLink(item);

          return (
            <Link
              key={item.id}
              href={link}
              className="flex items-start gap-4 p-4 bg-[#0F1115] border border-white/10 rounded-xl hover:-translate-y-1 hover:border-[#F7931A]/50 transition-all group"
            >
              {/* Avatar */}
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#F7931A]/20 to-[#FFD600]/20 border border-[#F7931A]/30 flex items-center justify-center flex-shrink-0">
                <span className="text-sm font-bold text-[#F7931A]">
                  {getUserInitials(item.actor)}
                </span>
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start gap-2">
                  <Icon className="w-4 h-4 text-[#F7931A] mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm group-hover:text-[#F7931A] transition-colors">
                      {item.actor
                        ? `${item.actor.first_name} ${item.actor.last_name}`
                        : "Someone"}{" "}
                      <span className="text-white/60">
                        {item.description}
                      </span>
                    </p>
                    <p className="text-white/40 text-xs mt-1">
                      {item.vault_name} · {formatRelativeTime(item.created_at)}
                    </p>
                  </div>
                </div>
              </div>
            </Link>
          );
        })}
      </div>

      {/* View all link */}
      <div className="flex justify-center pt-2">
        <Link
          href="/activity"
          className="text-sm font-medium bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent hover:opacity-80 transition-opacity"
        >
          View all activity →
        </Link>
      </div>
    </div>
  );
}
