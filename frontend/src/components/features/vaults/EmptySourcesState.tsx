'use client';

import { FileText } from 'lucide-react';
import GradientButton from '@/components/ui/GradientButton';

interface EmptySourcesStateProps {
  onAddSource: () => void;
  canAddSource: boolean; // Only show CTA if user has Contributor or Owner role
}

export default function EmptySourcesState({ onAddSource, canAddSource }: EmptySourcesStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-24 px-6 text-center">
      {/* Icon container with glass morphism */}
      <div className="mb-8 flex h-24 w-24 items-center justify-center rounded-full bg-white/5 border border-white/10">
        <FileText className="h-12 w-12 text-[#F7931A]" />
      </div>

      {/* Heading */}
      <h3 className="mb-3 text-2xl font-bold text-white">
        No sources yet
      </h3>

      {/* Subtext */}
      <p className="mb-8 max-w-md text-base text-muted-foreground">
        Add URLs, PDFs, or citations to build your knowledge base
      </p>

      {/* CTA button - only shown if user can add sources */}
      {canAddSource && (
        <GradientButton onClick={onAddSource}>
          Add Source
        </GradientButton>
      )}
    </div>
  );
}
