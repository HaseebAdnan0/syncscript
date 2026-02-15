'use client';

import { useEffect, useRef, useState } from 'react';
import { useVaultSocket } from './useVaultSocket';

export interface PresenceMember {
  userId: number;
  username: string;
  lastActivity: number; // timestamp
}

interface UsePresenceOptions {
  vaultId: string;
  currentUserId?: number;
}

export function usePresence({ vaultId, currentUserId }: UsePresenceOptions) {
  const [activeMembers, setActiveMembers] = useState<Map<number, PresenceMember>>(new Map());
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const inactivityCheckIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const { status, send, addEventListener } = useVaultSocket({ vaultId });

  // Send presence heartbeat every 30 seconds
  useEffect(() => {
    if (status !== 'connected' || !currentUserId) return;

    // Send initial heartbeat immediately
    send('presence.heartbeat', { userId: currentUserId });

    // Set up interval for subsequent heartbeats
    heartbeatIntervalRef.current = setInterval(() => {
      send('presence.heartbeat', { userId: currentUserId });
    }, 30000); // 30 seconds

    return () => {
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }
    };
  }, [status, currentUserId, send]);

  // Handle presence events
  useEffect(() => {
    // Handle full presence update from backend (sent on connect/disconnect)
    const handlePresenceUpdate = (data: { active_users?: Array<{ user_id: number; username: string; joined_at: number; status: string }> }) => {
      if (!data?.active_users) return;

      setActiveMembers(() => {
        const updated = new Map<number, PresenceMember>();
        for (const user of data.active_users!) {
          updated.set(user.user_id, {
            userId: user.user_id,
            username: user.username,
            lastActivity: user.joined_at * 1000, // Convert to ms
          });
        }
        return updated;
      });
    };

    const handlePresenceJoin = (data: { userId: number; username: string }) => {
      setActiveMembers(prev => {
        const updated = new Map(prev);
        updated.set(data.userId, {
          userId: data.userId,
          username: data.username,
          lastActivity: Date.now(),
        });
        return updated;
      });
    };

    const handlePresenceLeave = (data: { userId: number }) => {
      setActiveMembers(prev => {
        const updated = new Map(prev);
        updated.delete(data.userId);
        return updated;
      });
    };

    const handlePresenceHeartbeat = (data: { userId: number; username: string }) => {
      setActiveMembers(prev => {
        const updated = new Map(prev);
        updated.set(data.userId, {
          userId: data.userId,
          username: data.username,
          lastActivity: Date.now(),
        });
        return updated;
      });
    };

    const cleanupUpdate = addEventListener('presence.update', handlePresenceUpdate);
    const cleanupJoin = addEventListener('presence.join', handlePresenceJoin);
    const cleanupLeave = addEventListener('presence.leave', handlePresenceLeave);
    const cleanupHeartbeat = addEventListener('presence.heartbeat', handlePresenceHeartbeat);

    return () => {
      cleanupUpdate();
      cleanupJoin();
      cleanupLeave();
      cleanupHeartbeat();
    };
  }, [addEventListener]);

  // Mark members as inactive after 60 seconds without heartbeat
  useEffect(() => {
    inactivityCheckIntervalRef.current = setInterval(() => {
      const now = Date.now();
      const inactivityThreshold = 60000; // 60 seconds

      setActiveMembers(prev => {
        const updated = new Map(prev);
        let hasChanges = false;

        for (const [userId, member] of updated.entries()) {
          if (now - member.lastActivity > inactivityThreshold) {
            updated.delete(userId);
            hasChanges = true;
          }
        }

        return hasChanges ? updated : prev;
      });
    }, 10000); // Check every 10 seconds

    return () => {
      if (inactivityCheckIntervalRef.current) {
        clearInterval(inactivityCheckIntervalRef.current);
      }
    };
  }, []);

  // Return list of active member IDs with last activity timestamp
  const activeMembersList = Array.from(activeMembers.values());

  return {
    activeMembers: activeMembersList,
    activeMemberIds: activeMembersList.map(m => m.userId),
    isActive: (userId: number) => activeMembers.has(userId),
    activeMembersCount: activeMembers.size,
  };
}
