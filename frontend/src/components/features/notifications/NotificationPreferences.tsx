"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Switch } from "@/components/ui/switch";
import { Bell, Volume2, VolumeX } from "lucide-react";
import {
  getPreferences,
  updatePreferences,
  type NotificationPreferences as PreferencesType,
} from "@/lib/api/notifications";
import { requestNotificationPermission } from "@/lib/pusher";

export function NotificationPreferences() {
  const queryClient = useQueryClient();
  const [soundEnabled, setSoundEnabled] = useState(false);

  // Fetch preferences from backend
  const { data: preferences, isLoading } = useQuery({
    queryKey: ["notification-preferences"],
    queryFn: getPreferences,
  });

  // Load sound preference from localStorage on mount
  useEffect(() => {
    const storedSound = localStorage.getItem("notification-sound-enabled");
    if (storedSound !== null) {
      setSoundEnabled(storedSound === "true");
    } else if (preferences?.sound_enabled !== undefined) {
      setSoundEnabled(preferences.sound_enabled);
    }
  }, [preferences]);

  // Update preferences mutation
  const updateMutation = useMutation({
    mutationFn: (updates: Partial<PreferencesType>) => updatePreferences(updates),
    onSuccess: (data) => {
      queryClient.setQueryData(["notification-preferences"], data);
    },
  });

  const handleNotificationsToggle = (checked: boolean) => {
    updateMutation.mutate({ notifications_enabled: checked });
  };

  const handlePushToggle = async (checked: boolean) => {
    if (checked) {
      // Request browser notification permission
      const granted = await requestNotificationPermission();
      if (granted) {
        updateMutation.mutate({ push_notifications_enabled: true });
      } else {
        // Permission denied, don't update backend
        console.warn("Browser notification permission denied");
      }
    } else {
      updateMutation.mutate({ push_notifications_enabled: false });
    }
  };

  const handleSoundToggle = (checked: boolean) => {
    // Save to localStorage for immediate access
    localStorage.setItem("notification-sound-enabled", String(checked));
    setSoundEnabled(checked);
    // Also save to backend
    updateMutation.mutate({ sound_enabled: checked });
  };

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-16 bg-white/5 rounded-lg"></div>
        <div className="h-16 bg-white/5 rounded-lg"></div>
        <div className="h-16 bg-white/5 rounded-lg"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* All Notifications Toggle */}
      <div className="flex items-center justify-between p-4 bg-[#0F1115] border border-white/10 rounded-xl hover:border-[#F7931A]/30 transition-all">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A]">
            <Bell className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Enable Notifications</h3>
            <p className="text-sm text-[#94A3B8]">Receive all vault and collaboration updates</p>
          </div>
        </div>
        <Switch
          checked={preferences?.notifications_enabled ?? false}
          onCheckedChange={handleNotificationsToggle}
          disabled={updateMutation.isPending}
        />
      </div>

      {/* Browser Push Notifications Toggle */}
      <div className="flex items-center justify-between p-4 bg-[#0F1115] border border-white/10 rounded-xl hover:border-[#F7931A]/30 transition-all">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A]">
            <Bell className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Browser Push Notifications</h3>
            <p className="text-sm text-[#94A3B8]">
              Get notified even when tab is not focused (for high-priority events)
            </p>
          </div>
        </div>
        <Switch
          checked={preferences?.push_notifications_enabled ?? false}
          onCheckedChange={handlePushToggle}
          disabled={updateMutation.isPending || !(preferences?.notifications_enabled ?? false)}
        />
      </div>

      {/* Sound Toggle */}
      <div className="flex items-center justify-between p-4 bg-[#0F1115] border border-white/10 rounded-xl hover:border-[#F7931A]/30 transition-all">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A]">
            {soundEnabled ? (
              <Volume2 className="h-5 w-5 text-white" />
            ) : (
              <VolumeX className="h-5 w-5 text-white" />
            )}
          </div>
          <div>
            <h3 className="font-semibold text-white">Sound Notifications</h3>
            <p className="text-sm text-[#94A3B8]">Play sound when notifications arrive</p>
          </div>
        </div>
        <Switch
          checked={soundEnabled}
          onCheckedChange={handleSoundToggle}
          disabled={updateMutation.isPending || !(preferences?.notifications_enabled ?? false)}
        />
      </div>

      {/* Status message */}
      {updateMutation.isPending && (
        <p className="text-sm text-[#94A3B8] text-center">Saving preferences...</p>
      )}
    </div>
  );
}
