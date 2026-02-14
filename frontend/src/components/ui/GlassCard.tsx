'use client'

import React from 'react'

interface GlassCardProps {
  children: React.ReactNode
  className?: string
}

const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`backdrop-blur-lg bg-white/5 border border-white/10 rounded-2xl p-8 ${className}`}
        {...props}
      >
        {children}
      </div>
    )
  }
)

GlassCard.displayName = 'GlassCard'

export default GlassCard
