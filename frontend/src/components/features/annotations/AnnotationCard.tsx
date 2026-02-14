'use client';

import { Annotation } from '@/lib/types/annotations';
import { format } from 'date-fns';

interface AnnotationCardProps {
  annotation: Annotation;
}

export function AnnotationCard({ annotation }: AnnotationCardProps) {
  return (
    <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-6 hover:-translate-y-1 hover:border-[#F7931A]/50 transition-all duration-300">
      {/* Header with author avatar and timestamp */}
      <div className="flex items-start gap-3 mb-4">
        {/* Author avatar */}
        <div className="w-10 h-10 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center text-sm font-bold text-white flex-shrink-0">
          {annotation.author.username.charAt(0).toUpperCase()}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-baseline justify-between gap-2">
            <span className="font-semibold text-white">
              {annotation.author.username}
            </span>
            <span className="text-xs text-[#94A3B8]">
              {format(new Date(annotation.createdAt), 'MMM d, yyyy h:mm a')}
            </span>
          </div>
          {annotation.pageNumber && (
            <span className="text-xs text-[#94A3B8]">
              Page {annotation.pageNumber}
            </span>
          )}
        </div>
      </div>

      {/* Annotation text */}
      <p className="text-sm text-white/90 whitespace-pre-wrap">
        {annotation.text}
      </p>

      {/* Replies count */}
      {annotation.replies && annotation.replies.length > 0 && (
        <div className="mt-4 pt-4 border-t border-white/10">
          <span className="text-xs text-[#94A3B8]">
            {annotation.replies.length} {annotation.replies.length === 1 ? 'reply' : 'replies'}
          </span>
        </div>
      )}
    </div>
  );
}
