import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

// Container Props
export interface ContainerProps {
  children: ReactNode;
  className?: string;
}

export function Container({ children, className }: ContainerProps) {
  return (
    <div className={cn('max-w-7xl mx-auto px-4 sm:px-6 lg:px-8', className)}>
      {children}
    </div>
  );
}

// Section Props
export interface SectionProps {
  children: ReactNode;
  className?: string;
}

export function Section({ children, className }: SectionProps) {
  return <section className={cn('py-24', className)}>{children}</section>;
}

// PageLayout Props
export interface PageLayoutProps {
  children: ReactNode;
  header?: ReactNode;
  footer?: ReactNode;
  className?: string;
}

export function PageLayout({
  children,
  header,
  footer,
  className,
}: PageLayoutProps) {
  return (
    <div className={cn('min-h-screen flex flex-col', className)}>
      {header && <header>{header}</header>}
      <main className="flex-1">{children}</main>
      {footer && <footer>{footer}</footer>}
    </div>
  );
}
