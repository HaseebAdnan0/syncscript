'use client';

import { useState } from 'react';
import { MessageSquarePlus, X } from 'lucide-react';

interface AddAnnotationFormProps {
  onSubmit: (text: string, pageNumber?: number) => void;
  onCancel: () => void;
  isLoading?: boolean;
  maxLength?: number;
}

export function AddAnnotationForm({
  onSubmit,
  onCancel,
  isLoading = false,
  maxLength = 2000,
}: AddAnnotationFormProps) {
  const [text, setText] = useState('');
  const [pageNumber, setPageNumber] = useState<string>('');

  const handleSubmit = () => {
    if (!text.trim()) return;

    const pageNum = pageNumber ? parseInt(pageNumber, 10) : undefined;
    onSubmit(text.trim(), pageNum);

    // Reset form
    setText('');
    setPageNumber('');
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
      <div className="space-y-2">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Add your annotation... (Cmd/Ctrl + Enter to submit)"
          className="w-full h-32 bg-black/50 border-b-2 border-white/20 px-4 py-3 text-white placeholder:text-[#94A3B8] focus:border-[#F7931A] focus:outline-none resize-none rounded-t-lg transition-colors"
          disabled={isLoading}
          maxLength={maxLength}
        />

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
