'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { useToast } from '@/hooks/useToast';
import { CitationFormat } from '@/lib/types/user';
import { api } from '@/lib/api';

const CITATION_FORMATS: { value: CitationFormat | 'none'; label: string }[] = [
  { value: 'none', label: 'Always Ask' },
  { value: 'apa7', label: 'APA 7th Edition' },
  { value: 'mla9', label: 'MLA 9th Edition' },
  { value: 'chicago17', label: 'Chicago 17th Edition' },
  { value: 'bibtex', label: 'BibTeX' },
  { value: 'ieee', label: 'IEEE' },
  { value: 'harvard', label: 'Harvard' },
];

export function CitationPreferences() {
  const { user, setUser } = useAuthStore();
  const { toast } = useToast();
  const [selectedFormat, setSelectedFormat] = useState<CitationFormat | 'none'>('none');
  const [isSaving, setIsSaving] = useState(false);

  // Initialize selected format from user preference
  useEffect(() => {
    if (user?.default_citation_format) {
      setSelectedFormat(user.default_citation_format);
    } else {
      setSelectedFormat('none');
    }
  }, [user?.default_citation_format]);

  const handleFormatChange = async (format: CitationFormat | 'none') => {
    setSelectedFormat(format);
    setIsSaving(true);

    try {
      // PATCH /api/v1/users/me/ with default_citation_format
      const response = await api.patch('/users/me/', {
        default_citation_format: format === 'none' ? null : format,
      });

      // Update auth store with new user data
      setUser(response.data);

      toast({
        title: 'Success',
        description: `Citation format preference ${format === 'none' ? 'cleared' : `set to ${CITATION_FORMATS.find(f => f.value === format)?.label}`}`,
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.message || 'Failed to update citation format preference',
      });

      // Revert to previous value on error
      if (user?.default_citation_format) {
        setSelectedFormat(user.default_citation_format);
      } else {
        setSelectedFormat('none');
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="citation-format" className="block text-sm font-medium text-white/80 mb-2">
          Default Citation Format
        </label>
        <p className="text-sm text-[#94A3B8] mb-4">
          Choose your preferred citation format for all citations. Select &quot;Always Ask&quot; to choose the format each time.
        </p>
      </div>

      <div className="relative">
        <select
          id="citation-format"
          value={selectedFormat}
          onChange={(e) => handleFormatChange(e.target.value as CitationFormat | 'none')}
          disabled={isSaving}
          className="w-full bg-black/50 border border-white/20 rounded-lg px-4 py-3 text-white
                     focus:border-[#F7931A] focus:outline-none transition-colors
                     disabled:opacity-50 disabled:cursor-not-allowed
                     appearance-none cursor-pointer"
        >
          {CITATION_FORMATS.map((format) => (
            <option key={format.value} value={format.value} className="bg-[#0F1115] text-white">
              {format.label}
            </option>
          ))}
        </select>

        {/* Custom dropdown arrow */}
        <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
          <svg
            className={`h-5 w-5 text-[#94A3B8] transition-opacity ${isSaving ? 'opacity-0' : 'opacity-100'}`}
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </div>

        {/* Loading spinner */}
        {isSaving && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            <div className="h-5 w-5 border-2 border-[#F7931A] border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      {/* Info message */}
      <div className="bg-[#F7931A]/10 border border-[#F7931A]/20 rounded-lg p-4">
        <p className="text-sm text-[#F7931A]">
          💡 <strong>Tip:</strong> This preference will be used as the default format when generating citations.
          You can still choose a different format for individual citations.
        </p>
      </div>
    </div>
  );
}
