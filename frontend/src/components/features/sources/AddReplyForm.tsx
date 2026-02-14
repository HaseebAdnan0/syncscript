'use client';

import React, { useState, KeyboardEvent } from 'react';
import { Send, X } from 'lucide-react';

interface AddReplyFormProps {
  onSubmit: (text: string) => void | Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  currentUserName?: string;
  maxLength?: number;
}

export function AddReplyForm({
  onSubmit,
  onCancel,
  isLoading = false,
  currentUserName = 'You',
  maxLength = 500,
}: AddReplyFormProps) {
  const [text, setText] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const handleSubmit = async () => {
    if (text.trim() && !isLoading) {
      await onSubmit(text.trim());
      setText('');
      setIsFocused(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
    if (e.key === 'Escape') {
      e.preventDefault();
      setText('');
      setIsFocused(false);
      onCancel();
    }
  };

  const handleCancel = () => {
    setText('');
    setIsFocused(false);
    onCancel();
  };

  const isSubmitDisabled = !text.trim() || text.length > maxLength || isLoading;
  const remainingChars = maxLength - text.length;

  return (
    <div className="mt-3 pl-4 border-l-2 border-[#F7931A]/30">
      <div className="flex items-start gap-2">
        {/* Author Avatar */}
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] flex items-center justify-center text-white text-xs font-bold">
          {currentUserName.charAt(0).toUpperCase()}
        </div>

        {/* Input Container */}
        <div className="flex-1">
          <div className="relative">
            <input
              type="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              placeholder="Write a reply... (Enter to submit, Escape to cancel)"
              disabled={isLoading}
              maxLength={maxLength}
              className={`w-full bg-black/50 border-b-2 ${
                isFocused ? 'border-[#F7931A]' : 'border-white/20'
              } px-3 py-2 text-sm text-white placeholder:text-white/40 focus:outline-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
            />
          </div>

          {/* Character Count & Actions (shown when focused or has text) */}
          {(isFocused || text) && (
            <div className="flex items-center justify-between mt-2">
              <div className="flex items-center gap-2">
                {/* Character Count */}
                <span
                  className={`text-xs ${
                    remainingChars < 50
                      ? remainingChars < 0
                        ? 'text-red-400'
                        : 'text-[#F7931A]'
                      : 'text-[#94A3B8]'
                  }`}
                >
                  {remainingChars < 100 && `${remainingChars} chars left`}
                </span>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCancel}
                  type="button"
                  disabled={isLoading}
                  className="p-1.5 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 text-white/60 hover:text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Cancel (Escape)"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={handleSubmit}
                  type="button"
                  disabled={isSubmitDisabled}
                  className="p-1.5 rounded-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] hover:scale-105 text-white transition-all shadow-[0_0_15px_-3px_rgba(234,88,12,0.5)] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
                  title="Send reply (Enter)"
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
