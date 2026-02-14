'use client';

import { useState } from 'react';
import { Quote } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface CitationButtonProps {
  onFormatSelect: (format: string) => void;
  isLoading?: boolean;
}

const CITATION_FORMATS = [
  { value: 'apa7', label: 'APA 7th' },
  { value: 'mla9', label: 'MLA 9th' },
  { value: 'chicago17', label: 'Chicago 17th' },
  { value: 'bibtex', label: 'BibTeX' },
  { value: 'ieee', label: 'IEEE' },
  { value: 'harvard', label: 'Harvard' },
] as const;

export function CitationButton({ onFormatSelect, isLoading = false }: CitationButtonProps) {
  const [open, setOpen] = useState(false);

  const handleFormatClick = (format: string) => {
    onFormatSelect(format);
    setOpen(false);
  };

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <button
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          <Quote className="w-4 h-4" />
          <span className="text-sm">Cite</span>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        className="bg-[#0F1115] border border-white/10 rounded-xl shadow-[0_0_30px_-10px_rgba(247,147,26,0.3)] min-w-[180px]"
      >
        {CITATION_FORMATS.map((format) => (
          <DropdownMenuItem
            key={format.value}
            onClick={() => handleFormatClick(format.value)}
            className="text-white hover:bg-white/5 focus:bg-white/10 cursor-pointer px-4 py-2 rounded-lg transition-colors"
          >
            {format.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
