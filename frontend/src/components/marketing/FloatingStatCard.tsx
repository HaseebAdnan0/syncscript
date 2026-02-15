
import { LucideIcon } from 'lucide-react';

interface FloatingStatCardProps {
  icon: LucideIcon;
  number: string;
  label: string;
  position: 'top' | 'left' | 'right';
  delay?: number;
}

export default function FloatingStatCard({
  icon: Icon,
  number,
  label,
  position,
  delay = 0,
}: FloatingStatCardProps) {
  // Position classes based on prop - spread around the orb without overlap
  const positionClasses = {
    top: 'top-0 right-0 translate-x-1/3 -translate-y-1/4',
    left: 'bottom-24 -left-16',
    right: 'bottom-24 -right-16',
  };

  // Mobile stacking classes (stack vertically below orb)
  const mobilePositionClasses = {
    top: 'md:top-0 md:right-0 md:translate-x-1/3 md:-translate-y-1/4',
    left: 'md:bottom-24 md:-left-16',
    right: 'md:bottom-24 md:-right-16',
  };

  return (
    <div
      className={`
        absolute ${positionClasses[position]}
        ${mobilePositionClasses[position]}
        /* Mobile: stack below orb */
        static mb-6 translate-x-0 translate-y-0
        md:absolute
        /* Solid dark background */
        bg-[#0F1115] border border-white/20
        rounded-2xl p-4 md:p-5
        /* Staggered bounce animation */
        animate-bounce-slow
        hover:scale-105 transition-transform duration-300
        z-10
      `}
      style={{
        animationDelay: `${delay}s`,
      }}
    >
      {/* Icon with orange accent */}
      <div className="flex items-center justify-center w-10 h-10 md:w-11 md:h-11 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] mb-2">
        <Icon className="w-5 h-5 md:w-5 md:h-5 text-white" />
      </div>

      {/* Number (large) */}
      <div className="text-xl md:text-2xl font-bold text-white mb-0.5">
        {number}
      </div>

      {/* Label (muted) */}
      <div className="text-xs md:text-sm text-[#94A3B8] whitespace-nowrap">
        {label}
      </div>
    </div>
  );
}
