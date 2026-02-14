'use client';

import { AnnotationReply } from '@/lib/types/annotations';
import { format } from 'date-fns';
import { Trash2 } from 'lucide-react';
import { useState } from 'react';

interface AnnotationReplyCardProps {
  reply: AnnotationReply;
  canDelete?: boolean;
  onDelete?: () => void;
}

export default function AnnotationReplyCard({
  reply,
  canDelete = false,
  onDelete,
}: AnnotationReplyCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  // Generate gradient circle with first letter of username
  const authorInitial = reply.author.username.charAt(0).toUpperCase();

  return (
    <div
      className="flex gap-3 pl-4 border-l-2 border-[#F7931A]/30 py-3"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Author Avatar - Smaller for replies */}
      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-gradient-to-br from-[#EA580C] to-[#F7931A] flex items-center justify-center text-white text-xs font-bold">
        {authorInitial}
      </div>

      {/* Reply Content */}
      <div className="flex-1 min-w-0">
        {/* Author and Timestamp */}
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-medium text-white/80">
            {reply.author.username}
          </span>
          <span className="text-xs text-[#94A3B8]">
            {format(new Date(reply.createdAt), 'MMM d, yyyy • h:mm a')}
          </span>
        </div>

        {/* Reply Text */}
        <p className="text-sm text-white/80 leading-relaxed">
          {reply.text}
        </p>
      </div>

      {/* Delete Button - Appears on hover if canDelete */}
      {isHovered && canDelete && onDelete && (
        <button
          onClick={onDelete}
          className="flex-shrink-0 p-2 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 transition-all"
          title="Delete reply"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}
