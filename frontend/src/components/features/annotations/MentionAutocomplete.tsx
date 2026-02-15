'use client';

import { useState, useEffect, useRef } from 'react';
import { User } from '@/lib/types/user';

interface MentionAutocompleteProps {
  vaultMembers: User[];
  onSelect: (username: string) => void;
  trigger: string; // The current input after @
  position: { top: number; left: number };
  onClose: () => void;
}

export function MentionAutocomplete({
  vaultMembers,
  onSelect,
  trigger,
  position,
  onClose,
}: MentionAutocompleteProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Filter members based on trigger text
  const filteredMembers = vaultMembers.filter((member) =>
    member.username.toLowerCase().startsWith(trigger.toLowerCase())
  );

  // Reset selected index when filtered members change
  useEffect(() => {
    setSelectedIndex(0);
  }, [trigger]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (filteredMembers.length === 0) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((prev) =>
            prev < filteredMembers.length - 1 ? prev + 1 : prev
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : prev));
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredMembers[selectedIndex]) {
            onSelect(filteredMembers[selectedIndex].username);
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [filteredMembers, selectedIndex, onSelect, onClose]);

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        onClose();
      }
    };

    setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
    }, 0);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose]);

  // Scroll selected item into view
  useEffect(() => {
    const selectedElement = dropdownRef.current?.querySelector(
      `[data-index="${selectedIndex}"]`
    );
    selectedElement?.scrollIntoView({ block: 'nearest' });
  }, [selectedIndex]);

  if (filteredMembers.length === 0) {
    return null;
  }

  return (
    <div
      ref={dropdownRef}
      className="absolute z-50 bg-[#0F1115] border border-white/10 rounded-lg shadow-[0_0_20px_-5px_rgba(247,147,26,0.3)] overflow-hidden"
      style={{
        top: position.top,
        left: position.left,
        minWidth: '200px',
        maxHeight: '200px',
        overflowY: 'auto',
      }}
    >
      {filteredMembers.map((member, index) => (
        <button
          key={member.id}
          data-index={index}
          onClick={() => onSelect(member.username)}
          className={`w-full px-4 py-2 flex items-center gap-3 hover:bg-white/5 transition-colors border-b border-white/5 last:border-b-0 ${
            index === selectedIndex ? 'bg-[#F7931A]/10 border-l-2 border-l-[#F7931A]' : ''
          }`}
        >
          {/* Avatar circle with first letter */}
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#EA580C] to-[#F7931A] flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
            {member.username.charAt(0).toUpperCase()}
          </div>

          {/* User info */}
          <div className="flex flex-col items-start min-w-0">
            <span className="text-white font-medium text-sm truncate w-full">
              {member.first_name && member.last_name
                ? `${member.first_name} ${member.last_name}`
                : member.username}
            </span>
            <span className="text-[#94A3B8] text-xs truncate w-full">
              @{member.username}
            </span>
          </div>
        </button>
      ))}
    </div>
  );
}
