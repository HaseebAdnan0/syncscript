import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-3 py-1 text-xs font-mono uppercase border transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-primary/20 text-primary border-primary/30',
        success: 'bg-green-500/20 text-green-400 border-green-500/30',
        warning: 'bg-accent/20 text-accent border-accent/30',
        error: 'bg-red-500/20 text-red-400 border-red-500/30',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
