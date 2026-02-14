'use client';

import { usePresence } from '@/hooks/usePresence';

interface PresenceIndicatorProps {
  vaultId: string;
  currentUserId?: number;
  maxDisplay?: number;
}

export function PresenceIndicator({
  vaultId,
  currentUserId,
  maxDisplay = 5
}: PresenceIndicatorProps) {
  const { activeMembers, activeMembersCount } = usePresence({ vaultId, currentUserId });

  // Show empty state if no active members
  if (activeMembersCount === 0) {
    return null;
  }

  const displayMembers = activeMembers.slice(0, maxDisplay);
  const overflowCount = activeMembersCount - maxDisplay;

  return (
    <div className="flex items-center gap-2 backdrop-blur-lg bg-white/5 border border-white/10 rounded-full px-4 py-2">
      {/* Active members avatars */}
      <div className="flex -space-x-2">
        {displayMembers.map((member) => (
          <div key={member.userId} className="relative group">
            {/* Avatar circle */}
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#F7931A] to-[#EA580C] flex items-center justify-center text-white font-bold text-xs border-2 border-[#0F1115]">
              {member.username.charAt(0).toUpperCase()}
            </div>

            {/* Green presence dot with animate-ping */}
            <div className="absolute -bottom-0.5 -right-0.5">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500 border border-[#0F1115]"></span>
              </span>
            </div>

            {/* Tooltip on hover */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-[#0F1115] border border-white/10 rounded text-white text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
              {member.username}
              <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-0.5 border-4 border-transparent border-t-[#0F1115]"></div>
            </div>
          </div>
        ))}

        {/* Overflow indicator */}
        {overflowCount > 0 && (
          <div className="w-8 h-8 rounded-full bg-[#0F1115] border-2 border-white/20 flex items-center justify-center text-[#94A3B8] font-bold text-xs">
            +{overflowCount}
          </div>
        )}
      </div>

      {/* Count text */}
      <span className="text-sm text-[#94A3B8]">
        {activeMembersCount} {activeMembersCount === 1 ? 'member' : 'members'} online
      </span>
    </div>
  );
}
