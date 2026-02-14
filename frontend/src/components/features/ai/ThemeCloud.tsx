'use client';

import { useState } from 'react';
import type { Theme } from './ResearchInsightsPanel';

export interface ThemeCloudProps {
  themes: Theme[];
  onClick?: (theme: Theme) => void;
}

export function ThemeCloud({ themes, onClick }: ThemeCloudProps) {
  const [hoveredTheme, setHoveredTheme] = useState<string | null>(null);

  if (themes.length === 0) {
    return (
      <div className="text-center py-8 text-[#94A3B8]">
        No themes identified yet
      </div>
    );
  }

  // Normalize weights for visual sizing
  const maxWeight = Math.max(...themes.map(t => t.weight));
  const minWeight = Math.min(...themes.map(t => t.weight));
  const weightRange = maxWeight - minWeight || 1;

  // Calculate font size based on weight (0.875rem to 1.5rem range)
  const getFontSize = (weight: number): number => {
    const normalized = (weight - minWeight) / weightRange;
    return 0.875 + (normalized * 0.625); // 0.875rem (14px) to 1.5rem (24px)
  };

  // Calculate orange gradient intensity based on weight
  const getGradientIntensity = (weight: number): number => {
    const normalized = (weight - minWeight) / weightRange;
    return 0.2 + (normalized * 0.3); // 20% to 50% opacity
  };

  return (
    <div className="flex flex-wrap gap-3 items-center justify-start">
      {themes.map((theme, idx) => {
        const fontSize = getFontSize(theme.weight);
        const gradientIntensity = getGradientIntensity(theme.weight);
        const isHovered = hoveredTheme === theme.name;
        const isClickable = onClick !== undefined;

        return (
          <div
            key={idx}
            className={`
              relative px-4 py-2 rounded-full text-white font-medium
              border transition-all duration-300
              ${isClickable ? 'cursor-pointer' : 'cursor-default'}
              ${isHovered ? 'scale-110 -translate-y-1' : ''}
            `}
            style={{
              fontSize: `${fontSize}rem`,
              background: `linear-gradient(135deg, rgba(234, 88, 12, ${gradientIntensity}) 0%, rgba(247, 147, 26, ${gradientIntensity}) 100%)`,
              borderColor: isHovered
                ? 'rgba(247, 147, 26, 0.8)'
                : `rgba(247, 147, 26, ${gradientIntensity + 0.1})`,
            }}
            onClick={() => isClickable && onClick(theme)}
            onMouseEnter={() => setHoveredTheme(theme.name)}
            onMouseLeave={() => setHoveredTheme(null)}
          >
            <span className="relative z-10">{theme.name}</span>
            <span className="ml-2 text-[#94A3B8] text-xs relative z-10">
              ({theme.source_count})
            </span>

            {/* Tooltip on hover */}
            {isHovered && (
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-[#0F1115] border border-[#F7931A]/50 rounded-lg whitespace-nowrap text-sm z-20">
                <div className="text-white font-medium">{theme.name}</div>
                <div className="text-[#94A3B8] text-xs">
                  {theme.source_count} {theme.source_count === 1 ? 'source' : 'sources'}
                  {' • '}
                  Weight: {theme.weight.toFixed(2)}
                </div>
                {/* Tooltip arrow */}
                <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px">
                  <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-[#F7931A]/50" />
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
