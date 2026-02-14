'use client';

import { useEffect, useState } from 'react';

interface UnreadBadgeProps {
  count: number;
  className?: string;
}

export function UnreadBadge({ count, className = '' }: UnreadBadgeProps) {
  const [prevCount, setPrevCount] = useState(count);
  const [shouldPulse, setShouldPulse] = useState(false);

  // Trigger pulse animation when count increases
  useEffect(() => {
    let timer: NodeJS.Timeout | undefined;

    if (count > prevCount && count > 0) {
      setShouldPulse(true);
      timer = setTimeout(() => setShouldPulse(false), 1000);
    }

    setPrevCount(count);

    return () => {
      if (timer) {
        clearTimeout(timer);
      }
    };
  }, [count, prevCount]);

  // Hide badge when count is 0
  if (count === 0) {
    return null;
  }

  const displayCount = count > 9 ? '9+' : count.toString();

  return (
    <div
      className={`
        absolute -top-1 -right-1
        min-w-[18px] h-[18px]
        flex items-center justify-center
        bg-gradient-to-r from-[#EA580C] to-[#F7931A]
        text-white text-[10px] font-bold
        rounded-full
        px-1
        shadow-[0_0_10px_-2px_rgba(247,147,26,0.6)]
        ${shouldPulse ? 'animate-pulse' : ''}
        ${className}
      `}
    >
      {displayCount}
    </div>
  );
}
