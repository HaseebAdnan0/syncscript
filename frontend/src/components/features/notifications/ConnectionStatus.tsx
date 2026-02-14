'use client';

import { cn } from '@/lib/utils';

type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

interface ConnectionStatusProps {
  status: ConnectionState;
  className?: string;
}

const statusConfig: Record<ConnectionState, { color: string; text: string; bgColor: string }> = {
  connected: {
    color: 'bg-green-500',
    bgColor: 'bg-green-500/20',
    text: 'Connected',
  },
  reconnecting: {
    color: 'bg-[#F7931A]', // Bitcoin primary orange
    bgColor: 'bg-[#F7931A]/20',
    text: 'Reconnecting...',
  },
  connecting: {
    color: 'bg-[#F7931A]',
    bgColor: 'bg-[#F7931A]/20',
    text: 'Connecting...',
  },
  disconnected: {
    color: 'bg-red-500',
    bgColor: 'bg-red-500/20',
    text: 'Disconnected',
  },
};

export function ConnectionStatus({ status, className }: ConnectionStatusProps) {
  const config = statusConfig[status];

  return (
    <div className={cn('relative inline-flex items-center gap-2', className)}>
      {/* Tooltip container with group hover */}
      <div className="group relative">
        {/* Status dot with background glow */}
        <div className={cn('relative flex items-center justify-center w-3 h-3 rounded-full', config.bgColor)}>
          <div className={cn('w-2 h-2 rounded-full', config.color)} />
        </div>

        {/* Tooltip */}
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 text-xs text-white bg-[#0F1115] border border-white/10 rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-200 whitespace-nowrap z-50">
          {config.text}
          {/* Tooltip arrow */}
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px">
            <div className="border-4 border-transparent border-t-[#0F1115]" />
          </div>
        </div>
      </div>
    </div>
  );
}
