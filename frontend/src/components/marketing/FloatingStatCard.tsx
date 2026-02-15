
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
  // Position classes based on prop
  const positionClasses = {
    top: 'top-0 left-1/2 -translate-x-1/2 -translate-y-1/2',
    left: 'left-0 top-1/2 -translate-x-1/2 -translate-y-1/2',
    right: 'right-0 top-1/2 translate-x-1/2 -translate-y-1/2',
  };

  // Mobile stacking classes (stack vertically below orb)
  const mobilePositionClasses = {
    top: 'md:top-0 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2',
    left: 'md:left-0 md:top-1/2 md:-translate-x-1/2 md:-translate-y-1/2',
    right: 'md:right-0 md:top-1/2 md:translate-x-1/2 md:-translate-y-1/2',
  };

  return (
    <div
      className={`
        absolute ${positionClasses[position]}
        ${mobilePositionClasses[position]}
        /* Mobile: stack below orb */
        static mb-6 translate-x-0 translate-y-0
        md:absolute
        /* Glass morphism */
        backdrop-blur-lg bg-white/5 border border-white/10
        rounded-2xl p-4 md:p-6
        min-w-[160px] md:min-w-[200px]
        /* Staggered bounce animation */
        animate-bounce-slow
        hover:scale-105 transition-transform duration-300
      `}
      style={{
        animationDelay: `${delay}s`,
      }}
    >
      {/* Icon with orange accent */}
      <div className="flex items-center justify-center w-10 h-10 md:w-12 md:h-12 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] mb-3">
        <Icon className="w-5 h-5 md:w-6 md:h-6 text-white" />
      </div>

      {/* Number (large) */}
      <div className="text-2xl md:text-3xl font-bold text-white mb-1">
        {number}
      </div>

      {/* Label (muted) */}
      <div className="text-sm md:text-base text-[#94A3B8]">
        {label}
      </div>
    </div>
  );
}
