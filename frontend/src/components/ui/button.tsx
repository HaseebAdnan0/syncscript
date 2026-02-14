import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center font-bold uppercase tracking-wider transition-all duration-300 disabled:opacity-50 disabled:pointer-events-none',
  {
    variants: {
      variant: {
        primary:
          'bg-gradient-to-r from-secondary to-primary text-white shadow-glow-orange hover:scale-105',
        outline:
          'border-2 border-primary text-primary hover:bg-primary/10 bg-transparent',
        ghost: 'text-muted hover:text-foreground hover:bg-white/5 bg-transparent',
      },
      size: {
        sm: 'h-9 px-4 text-xs rounded-full',
        md: 'h-12 px-6 text-sm rounded-full',
        lg: 'h-14 px-8 text-base rounded-full',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };
