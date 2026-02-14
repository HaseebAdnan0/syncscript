'use client';

import { useState, useEffect, useRef } from 'react';
import { Plus, FolderPlus, FileText, UserPlus, X } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface QuickAction {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  onClick: () => void;
}

export default function QuickActionsFAB() {
  const [isOpen, setIsOpen] = useState(false);
  const fabRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Close menu on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (fabRef.current && !fabRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const actions: QuickAction[] = [
    {
      icon: FolderPlus,
      label: 'New Vault',
      onClick: () => {
        setIsOpen(false);
        router.push('/vaults?action=create');
      },
    },
    {
      icon: FileText,
      label: 'Add Source',
      onClick: () => {
        setIsOpen(false);
        router.push('/vaults?action=add-source');
      },
    },
    {
      icon: UserPlus,
      label: 'Invite Collaborator',
      onClick: () => {
        setIsOpen(false);
        router.push('/vaults?action=invite');
      },
    },
  ];

  return (
    <div ref={fabRef} className="fixed bottom-8 right-8 z-50">
      {/* Action Menu */}
      <div
        className={`absolute bottom-16 right-0 flex flex-col gap-3 transition-all duration-300 ${
          isOpen
            ? 'opacity-100 translate-y-0 pointer-events-auto'
            : 'opacity-0 translate-y-4 pointer-events-none'
        }`}
      >
        {actions.map((action, index) => {
          const Icon = action.icon;
          return (
            <button
              key={action.label}
              onClick={action.onClick}
              className="flex items-center gap-3 bg-[#0F1115] border border-white/10 rounded-full px-4 py-3 shadow-lg hover:border-[#F7931A]/50 hover:scale-105 transition-all group"
              style={{
                transitionDelay: isOpen ? `${index * 50}ms` : '0ms',
              }}
            >
              <span className="text-white/70 font-medium text-sm whitespace-nowrap group-hover:text-white transition-colors">
                {action.label}
              </span>
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)]">
                <Icon className="w-5 h-5 text-white" />
              </div>
            </button>
          );
        })}
      </div>

      {/* Main FAB Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-14 h-14 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center shadow-[0_0_30px_-5px_rgba(234,88,12,0.6)] hover:scale-110 transition-all ${
          isOpen ? 'rotate-45' : 'rotate-0'
        }`}
        aria-label={isOpen ? 'Close quick actions' : 'Open quick actions'}
      >
        {isOpen ? (
          <X className="w-6 h-6 text-white" />
        ) : (
          <Plus className="w-6 h-6 text-white" />
        )}
      </button>
    </div>
  );
}
