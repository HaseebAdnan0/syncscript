
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
  // Position classes based on prop - spread around the orb
  const positionClasses = {
    top: 'top-4 right-0 translate-x-8',
    left: 'bottom-16 left-0 -translate-x-8',
    right: 'bottom-16 right-0 translate-x-8',
  };

  // Mobile stacking classes (stack vertically below orb)
  const mobilePositionClasses = {
    top: 'md:top-4 md:right-0 md:translate-x-8',
    left: 'md:bottom-16 md:left-0 md:-translate-x-8',
    right: 'md:bottom-16 md:right-0 md:translate-x-8',
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
