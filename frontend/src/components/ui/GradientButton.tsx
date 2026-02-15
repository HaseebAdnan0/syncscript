'use client';

import React from 'react';

interface GradientButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
  children: React.ReactNode;
}

const GradientButton = React.forwardRef<HTMLButtonElement, GradientButtonProps>(
  ({ isLoading = false, disabled, children, className = '', ...props }, ref) => {
    const isDisabled = disabled || isLoading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={`
          bg-gradient-to-r from-[#EA580C] to-[#F7931A]
          text-white font-bold uppercase tracking-wider
          rounded-full px-6 py-3
          shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)]
          hover:scale-105
          transition-all duration-300
          disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
          ${className}
        `}
        {...props}
      >
        {isLoading ? (
          <div className="flex items-center justify-center gap-2">
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            <span>Loading...</span>
          </div>
        ) : (
          <span className="flex items-center justify-center">{children}</span>
        )}
      </button>
    );
  }
);

GradientButton.displayName = 'GradientButton';

export default GradientButton;
