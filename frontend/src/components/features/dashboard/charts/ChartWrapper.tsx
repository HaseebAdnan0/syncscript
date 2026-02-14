import React from 'react';

interface ChartWrapperProps {
  title: string;
  children: React.ReactNode;
  className?: string;
}

/**
 * Base wrapper component for dashboard charts
 * Provides consistent styling and layout following Bitcoin DeFi design system
 */
export default function ChartWrapper({ title, children, className = '' }: ChartWrapperProps) {
  return (
    <div
      className={`bg-[#0F1115] border border-white/10 rounded-2xl p-6 hover:border-[#F7931A]/30 transition-all ${className}`}
    >
      <h3 className="text-lg font-bold text-white mb-6 font-heading">{title}</h3>
      <div className="w-full">{children}</div>
    </div>
  );
}

/**
 * Design system tokens for chart colors
 * These should be used across all chart components for consistency
 */
export const chartColors = {
  primary: '#F7931A',        // Bitcoin Orange
  secondary: '#EA580C',      // Burnt Orange
  accent: '#FFD600',         // Digital Gold
  muted: '#94A3B8',         // Stardust
  background: '#0F1115',     // Dark Matter
  border: '#1E293B',        // Dim Boundary
  foreground: '#FFFFFF',     // Pure Light
};

/**
 * Gradient color palette for multi-segment charts
 * Transitions from orange to gold across 5 shades
 */
export const chartGradient = [
  '#F7931A', // Bitcoin Orange
  '#F5A735', // Orange-Gold blend 1
  '#F3BB50', // Orange-Gold blend 2
  '#F1CF6B', // Orange-Gold blend 3
  '#FFD600', // Digital Gold
];

/**
 * Custom tooltip styling for Recharts
 * Apply these classes to Recharts Tooltip component
 */
export const tooltipStyles = {
  contentStyle: {
    backgroundColor: '#0F1115',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    padding: '12px',
    boxShadow: '0 0 20px -5px rgba(247, 147, 26, 0.3)',
  },
  labelStyle: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    marginBottom: '4px',
  },
  itemStyle: {
    color: '#F7931A',
    padding: '4px 0',
  },
};
