'use client';

import { useRef, useEffect, useState } from 'react';
import { MessageSquarePlus, ArrowDown } from 'lucide-react';
import { AnnotationCard } from './AnnotationCard';
import type { Annotation } from '@/lib/types/annotations';

interface AnnotationSidebarProps {
  annotations: Annotation[];
  isLoading?: boolean;
  onAddAnnotation: () => void;
  onReply?: (annotationId: number) => void;
  onEdit?: (annotationId: number) => void;
  onDelete?: (annotationId: number) => void;
  currentUserId?: number;
}

export function AnnotationSidebar({
  annotations,
  isLoading = false,
  onAddAnnotation,
  onReply,
  onEdit,
  onDelete,
  currentUserId,
}: AnnotationSidebarProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [showScrollIndicator, setShowScrollIndicator] = useState(false);
  const previousAnnotationIdsRef = useRef<Set<number>>(new Set());

  // Detect when a new annotation is added below the fold
  useEffect(() => {
    if (annotations.length === 0) {
      previousAnnotationIdsRef.current = new Set();
      return;
    }

    const currentIds = new Set(annotations.map(a => a.id));
    const previousIds = previousAnnotationIdsRef.current;

    // Find new annotations (IDs that weren't in previous set)
    const newIds = annotations
      .filter(a => !previousIds.has(a.id))
      .map(a => a.id);

    if (newIds.length > 0 && scrollContainerRef.current) {
      const container = scrollContainerRef.current;
      const scrollBottom = container.scrollTop + container.clientHeight;
      const isScrolledUp = scrollBottom < container.scrollHeight - 50; // 50px threshold

      if (isScrolledUp) {
        // New annotation added below fold - show indicator
        setShowScrollIndicator(true);
      }
    }

    previousAnnotationIdsRef.current = currentIds;
  }, [annotations]);

  // Scroll to new annotation
  const scrollToNewAnnotation = () => {
    if (scrollContainerRef.current) {
      // Scroll to top where newest annotations appear (sorted by newest first)
      scrollContainerRef.current.scrollTo({
        top: 0,
        behavior: 'smooth',
      });
      setShowScrollIndicator(false);
    }
  };

  // Hide indicator when user manually scrolls to top
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      if (container.scrollTop < 50) { // Near top
        setShowScrollIndicator(false);
      }
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-heading font-bold">Annotations</h2>
          {annotations.length > 0 && (
            <span className="inline-flex items-center justify-center px-2 py-0.5 text-xs font-bold bg-[#F7931A]/20 text-[#F7931A] border border-[#F7931A]/30 rounded-full">
              {annotations.length}
            </span>
          )}
        </div>

        <button
          onClick={onAddAnnotation}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-bold uppercase tracking-wider bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white rounded-full shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
        >
          <MessageSquarePlus className="w-4 h-4" />
          Add
        </button>
      </div>

      {/* Scrollable content */}
      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto p-4 relative">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-[#94A3B8]">
              Loading annotations...
            </div>
          </div>
        ) : annotations.length === 0 ? (
          // Empty state
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-20 h-20 rounded-full bg-gradient-to-r from-[#EA580C]/20 to-[#F7931A]/20 flex items-center justify-center mb-4">
              <MessageSquarePlus className="w-10 h-10 text-[#F7931A]" />
            </div>
            <h3 className="text-lg font-heading font-bold mb-2">
              No annotations yet
            </h3>
            <p className="text-sm text-[#94A3B8] mb-4 max-w-xs">
              Be the first to add one! Share your insights and notes with your team.
            </p>
            <button
              onClick={onAddAnnotation}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-bold uppercase tracking-wider bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white rounded-full shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
            >
              <MessageSquarePlus className="w-4 h-4" />
              Add First Annotation
            </button>
          </div>
        ) : (
          // Annotations list - sorted by newest first
          <div className="space-y-4">
            {annotations.map((annotation) => (
              <AnnotationCard
                key={annotation.id}
                annotation={annotation}
                onReply={onReply ? () => onReply(annotation.id) : undefined}
                canEdit={currentUserId === annotation.author.id}
                onEdit={onEdit ? () => onEdit(annotation.id) : undefined}
                canDelete={currentUserId === annotation.author.id}
                onDelete={onDelete ? () => onDelete(annotation.id) : undefined}
              />
            ))}
          </div>
        )}

        {/* Scroll indicator for new annotations below fold */}
        {showScrollIndicator && (
          <button
            onClick={scrollToNewAnnotation}
            className="absolute bottom-4 left-1/2 -translate-x-1/2 inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white text-sm font-bold rounded-full shadow-[0_0_20px_rgba(234,88,12,0.8)] hover:scale-105 transition-all animate-bounce z-10"
          >
            <ArrowDown className="w-4 h-4" />
            New annotation
          </button>
        )}
      </div>
    </div>
  );
}
