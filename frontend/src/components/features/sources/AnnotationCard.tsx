import { useState } from 'react';
import { Annotation } from '@/lib/types/annotations';
import { format } from 'date-fns';
import { MessageCircle, Edit2, Trash2 } from 'lucide-react';

interface AnnotationCardProps {
  annotation: Annotation;
  onEdit?: (annotation: Annotation) => void;
  onDelete?: (annotationId: number) => void;
  onReply?: (annotation: Annotation) => void;
  canEdit?: boolean;
  canDelete?: boolean;
}

export function AnnotationCard({
  annotation,
  onEdit,
  onDelete,
  onReply,
  canEdit = false,
  canDelete = false,
}: AnnotationCardProps) {
  const [isRepliesExpanded, setIsRepliesExpanded] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const replyCount = annotation.replies?.length || 0;
  const hasReplies = replyCount > 0;

  return (
    <div
      className="backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl p-4 transition-all duration-300 hover:border-[#F7931A]/50"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Header with author info and timestamp */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {/* Author avatar - gradient circle with first letter */}
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center text-white text-sm font-bold">
            {(annotation.author?.username || 'U').charAt(0).toUpperCase()}
          </div>
          <div>
            <div className="text-white font-medium text-sm">
              {annotation.author?.username || 'Unknown User'}
            </div>
            <div className="text-[#94A3B8] text-xs">
              {annotation.createdAt ? format(new Date(annotation.createdAt), 'MMM d, yyyy • h:mm a') : 'Unknown date'}
            </div>
          </div>
        </div>

        {/* Page number badge (if linked to specific page) */}
        {annotation.pageNumber && (
          <div className="bg-[#F7931A]/20 text-[#F7931A] border border-[#F7931A]/30 px-2 py-1 rounded-full text-xs font-medium">
            Page {annotation.pageNumber}
          </div>
        )}
      </div>

      {/* Annotation text */}
      <div className="text-white/90 text-sm leading-relaxed mb-3">
        {annotation.text}
      </div>

      {/* Footer with reply indicator and action buttons */}
      <div className="flex items-center justify-between pt-3 border-t border-white/5">
        {/* Reply count and expand toggle */}
        {hasReplies && (
          <button
            onClick={() => setIsRepliesExpanded(!isRepliesExpanded)}
            className="flex items-center gap-2 text-[#94A3B8] hover:text-[#F7931A] transition-colors text-xs"
          >
            <MessageCircle className="w-4 h-4" />
            <span>
              {replyCount} {replyCount === 1 ? 'reply' : 'replies'}
            </span>
            <span className="text-[#94A3B8]">•</span>
            <span className="text-[#F7931A]">
              {isRepliesExpanded ? 'Hide' : 'Show'}
            </span>
          </button>
        )}

        {!hasReplies && (
          <div className="flex-1" />
        )}

        {/* Quick action buttons (visible on hover) */}
        {isHovered && (
          <div className="flex items-center gap-2">
            {/* Reply button */}
            {onReply && (
              <button
                onClick={() => onReply(annotation)}
                className="p-1.5 rounded-lg bg-white/5 border border-white/10 hover:border-[#F7931A]/50 hover:bg-white/10 transition-all"
                title="Reply"
              >
                <MessageCircle className="w-4 h-4 text-white" />
              </button>
            )}

            {/* Edit button */}
            {canEdit && onEdit && (
              <button
                onClick={() => onEdit(annotation)}
                className="p-1.5 rounded-lg bg-white/5 border border-white/10 hover:border-[#F7931A]/50 hover:bg-white/10 transition-all"
                title="Edit"
              >
                <Edit2 className="w-4 h-4 text-white" />
              </button>
            )}

            {/* Delete button */}
            {canDelete && onDelete && (
              <button
                onClick={() => onDelete(annotation.id)}
                className="p-1.5 rounded-lg bg-red-500/10 border border-red-500/30 hover:bg-red-500/20 transition-all"
                title="Delete"
              >
                <Trash2 className="w-4 h-4 text-red-400" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Expanded replies section */}
      {isRepliesExpanded && hasReplies && (
        <div className="mt-4 space-y-3 pl-4 border-l-2 border-[#F7931A]/30">
          {annotation.replies?.map((reply) => (
            <div key={reply.id} className="text-sm">
              <div className="flex items-center gap-2 mb-1">
                {/* Reply author avatar - smaller */}
                <div className="w-6 h-6 rounded-full bg-gradient-to-r from-[#EA580C]/70 to-[#F7931A]/70 flex items-center justify-center text-white text-xs font-bold">
                  {(reply.author?.username || 'U').charAt(0).toUpperCase()}
                </div>
                <span className="text-white font-medium text-xs">
                  {reply.author?.username || 'Unknown User'}
                </span>
                <span className="text-[#94A3B8] text-xs">
                  {reply.createdAt ? format(new Date(reply.createdAt), 'MMM d • h:mm a') : ''}
                </span>
              </div>
              <div className="text-white/80 text-xs leading-relaxed pl-8">
                {reply.text}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
