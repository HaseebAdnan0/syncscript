'use client';

import { useState } from 'react';
import { Download } from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { useToast } from '@/hooks/useToast';
import { exportVaultCitations } from '@/lib/api/citations';

interface ExportCitationsButtonProps {
  vaultId: number;
  vaultName: string;
  sourceCount: number;
  disabled?: boolean;
}

const CITATION_FORMATS = [
  { value: 'bibtex', label: 'BibTeX', ext: 'bib' },
  { value: 'apa7', label: 'APA 7th', ext: 'txt' },
  { value: 'mla9', label: 'MLA 9th', ext: 'txt' },
  { value: 'chicago17', label: 'Chicago 17th', ext: 'txt' },
  { value: 'ieee', label: 'IEEE', ext: 'txt' },
  { value: 'harvard', label: 'Harvard', ext: 'txt' },
];

export function ExportCitationsButton({
  vaultId,
  vaultName,
  sourceCount,
  disabled = false,
}: ExportCitationsButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const { toast } = useToast();

  const handleExport = async (format: string, ext: string) => {
    setIsExporting(true);
    setIsOpen(false);

    try {
      const blob = await exportVaultCitations(vaultId, format);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${vaultName}-citations.${ext}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast({
        title: 'Export successful',
        description: `Downloaded ${sourceCount} citation${sourceCount === 1 ? '' : 's'} in ${format.toUpperCase()} format.`,
      });
    } catch (error: any) {
      // Handle large vault async export (202 response)
      if (error.response?.status === 202) {
        toast({
          title: 'Export started',
          description: "Your vault is large. You'll be notified when the export is ready.",
        });
      } else {
        toast({
          title: 'Export failed',
          description: error.response?.data?.error || 'Failed to export citations. Please try again.',
        });
      }
    } finally {
      setIsExporting(false);
    }
  };

  const tooltipMessage = sourceCount === 0 ? 'No sources to export' : undefined;

  return (
    <DropdownMenu.Root open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenu.Trigger asChild>
        <button
          disabled={disabled || isExporting || sourceCount === 0}
          title={tooltipMessage}
          className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center gap-2"
        >
          <Download className="w-5 h-5" />
          {isExporting ? 'Exporting...' : 'Export Citations'}
        </button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content
          className="bg-[#0F1115] border border-white/10 rounded-xl shadow-[0_0_30px_-5px_rgba(234,88,12,0.3)] min-w-[200px] p-2 z-50"
          sideOffset={8}
          align="end"
        >
          <div className="px-3 py-2 text-xs text-[#94A3B8] uppercase tracking-wider border-b border-white/10 mb-2">
            Select Format
          </div>

          {CITATION_FORMATS.map((format) => (
            <DropdownMenu.Item
              key={format.value}
              className="px-3 py-2 text-white hover:bg-white/10 rounded-lg cursor-pointer outline-none transition-colors"
              onSelect={() => handleExport(format.value, format.ext)}
            >
              {format.label}
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
