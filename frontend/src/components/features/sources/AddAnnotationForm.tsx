'use client';

import { useState, useRef } from 'react';
import { MessageSquarePlus, X } from 'lucide-react';
import { MentionAutocomplete } from '../annotations/MentionAutocomplete';
import type { User } from '@/lib/types/user';

interface AddAnnotationFormProps {
  onSubmit: (text: string, pageNumber?: number) => void;
  onCancel: () => void;
  isLoading?: boolean;
  maxLength?: number;
  vaultMembers?: User[];
}

export function AddAnnotationForm({
  onSubmit,
  onCancel,
  isLoading = false,
  maxLength = 2000,
  vaultMembers = [],
}: AddAnnotationFormProps) {
  const [text, setText] = useState('');
  const [pageNumber, setPageNumber] = useState<string>('');
  const [showMentions, setShowMentions] = useState(false);
  const [mentionTrigger, setMentionTrigger] = useState('');
  const [cursorPosition, setCursorPosition] = useState({ top: 0, left: 0 });
  const [mentionStartIndex, setMentionStartIndex] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Detect @ mentions
  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    setText(newText);

    const cursorPos = e.target.selectionStart;

    // Find last @ before cursor
    const textBeforeCursor = newText.substring(0, cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf('@');

    if (lastAtIndex !== -1) {
      // Check if @ is at start or after whitespace
      const charBeforeAt = lastAtIndex === 0 ? ' ' : newText[lastAtIndex - 1];
      if (charBeforeAt === ' ' || lastAtIndex === 0) {
        const textAfterAt = newText.substring(lastAtIndex + 1, cursorPos);
        // Only show if no spaces after @ and valid username chars
        if (!textAfterAt.includes(' ') && /^[\w]*$/.test(textAfterAt)) {
          setMentionTrigger(textAfterAt);
          setMentionStartIndex(lastAtIndex);
          setShowMentions(true);

          // Calculate cursor position for dropdown
          if (textareaRef.current) {
            const textarea = textareaRef.current;
            const rect = textarea.getBoundingClientRect();
            // Position dropdown near textarea (simplified positioning)
            setCursorPosition({
              top: rect.bottom + window.scrollY,
              left: rect.left + window.scrollX,
            });
          }
          return;
        }
      }
    }

    setShowMentions(false);
  };

  const handleMentionSelect = (username: string) => {
    if (!textareaRef.current) return;

    const cursorPos = textareaRef.current.selectionStart;
    const beforeMention = text.substring(0, mentionStartIndex);
    const afterMention = text.substring(cursorPos);
    const newText = `${beforeMention}@${username} ${afterMention}`;

    setText(newText);
    setShowMentions(false);
    setMentionTrigger('');

    // Set cursor position after inserted mention
    setTimeout(() => {
      if (textareaRef.current) {
        const newCursorPos = mentionStartIndex + username.length + 2; // +2 for @ and space
        textareaRef.current.focus();
        textareaRef.current.setSelectionRange(newCursorPos, newCursorPos);
      }
    }, 0);
  };

  const handleCloseMentions = () => {
    setShowMentions(false);
    setMentionTrigger('');
  };

  const handleSubmit = () => {
    if (!text.trim()) return;

    const pageNum = pageNumber ? parseInt(pageNumber, 10) : undefined;
    onSubmit(text.trim(), pageNum);

    // Reset form
    setText('');
    setPageNumber('');
    setShowMentions(false);
    setMentionTrigger('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Submit on Cmd/Ctrl + Enter
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
    // Cancel on Escape
    if (e.key === 'Escape') {
      e.preventDefault();
      onCancel();
    }
  };

  const isValid = text.trim().length > 0 && text.length <= maxLength;
  const remainingChars = maxLength - text.length;

  return (
    <div className="bg-[#0F1115] border border-white/10 rounded-xl p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageSquarePlus className="w-5 h-5 text-[#F7931A]" />
          <span className="font-medium text-white">Add Annotation</span>
        </div>
        <button
          type="button"
          onClick={onCancel}
          className="text-[#94A3B8] hover:text-white transition-colors"
          aria-label="Cancel"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Textarea */}
      <div className="space-y-2 relative">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleTextChange}
          onKeyDown={handleKeyDown}
          placeholder="Add your annotation... (Use @ to mention someone, Cmd/Ctrl + Enter to submit)"
          className="w-full h-32 bg-black/50 border-b-2 border-white/20 px-4 py-3 text-white placeholder:text-[#94A3B8] focus:border-[#F7931A] focus:outline-none resize-none rounded-t-lg transition-colors"
          disabled={isLoading}
          maxLength={maxLength}
        />

        {/* Mention Autocomplete */}
        {showMentions && vaultMembers.length > 0 && (
          <MentionAutocomplete
            vaultMembers={vaultMembers}
            trigger={mentionTrigger}
            position={cursorPosition}
            onSelect={handleMentionSelect}
            onClose={handleCloseMentions}
          />
        )}

        {/* Character count */}
        <div className={`text-xs text-right transition-colors ${
          remainingChars < 100 ? 'text-orange-400' :
          remainingChars < 0 ? 'text-red-400' :
          'text-[#94A3B8]'
        }`}>
          {remainingChars} characters remaining
        </div>
      </div>

      {/* Optional page number */}
      <div className="space-y-2">
        <label htmlFor="pageNumber" className="text-sm text-[#94A3B8]">
          Page Number (optional)
        </label>
        <input
          id="pageNumber"
          type="number"
          min="1"
          value={pageNumber}
          onChange={(e) => setPageNumber(e.target.value)}
          placeholder="e.g., 5"
          className="w-full bg-black/50 border-b-2 border-white/20 h-10 px-4 text-white placeholder:text-[#94A3B8] focus:border-[#F7931A] focus:outline-none transition-colors"
          disabled={isLoading}
        />
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3 pt-2">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!isValid || isLoading}
          className="flex-1 bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 py-2.5 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          {isLoading ? 'Adding...' : 'Add Annotation'}
        </button>

        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="px-6 py-2.5 bg-[#0F1115] border border-white/20 text-[#94A3B8] hover:text-white hover:border-white/40 rounded-full transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
