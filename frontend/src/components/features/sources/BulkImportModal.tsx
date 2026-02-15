'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Link } from 'lucide-react';

interface BulkImportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onParsedUrls: (urls: ParsedUrl[]) => void;
}

export interface ParsedUrl {
  url: string;
  isValid: boolean;
  error?: string;
}

// URL validation regex - basic HTTP/HTTPS URLs
const URL_REGEX = /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/;

export function BulkImportModal({
  open,
  onOpenChange,
  onParsedUrls,
}: BulkImportModalProps) {
  const [urlsText, setUrlsText] = useState('');
  const [isParsing, setIsParsing] = useState(false);
  const [parsedResults, setParsedResults] = useState<ParsedUrl[] | null>(null);

  const handleParseUrls = () => {
    setIsParsing(true);

    // Simulate parsing delay for UX (can be removed if real async parsing is needed)
    setTimeout(() => {
      // Split by newlines and filter out empty lines
      const lines = urlsText
        .split('\n')
        .map((line) => line.trim())
        .filter((line) => line.length > 0);

      // Parse and validate each URL
      const parsed: ParsedUrl[] = lines.map((line) => {
        const isValid = URL_REGEX.test(line);
        return {
          url: line,
          isValid,
          error: isValid ? undefined : 'Invalid URL format',
        };
      });

      setParsedResults(parsed);
      setIsParsing(false);
    }, 500);
  };

  const handleContinue = () => {
    if (parsedResults) {
      onParsedUrls(parsedResults);
      // Don't close modal - parent will handle showing preview
    }
  };

  const handleClose = () => {
    setUrlsText('');
    setParsedResults(null);
    onOpenChange(false);
  };

  const validCount = parsedResults?.filter((p) => p.isValid).length || 0;
  const invalidCount = parsedResults?.filter((p) => !p.isValid).length || 0;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-2xl">Bulk Import Sources</DialogTitle>
          <DialogDescription className="text-[#94A3B8]">
            Paste multiple URLs (one per line) to import sources in bulk.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Textarea for URL input */}
          <div>
            <label htmlFor="urls-input" className="block text-sm font-medium text-[#94A3B8] mb-2">
              URLs (one per line)
            </label>
            <Textarea
              id="urls-input"
              placeholder="https://example.com/article1&#10;https://example.com/article2&#10;https://example.com/paper.pdf"
              value={urlsText}
              onChange={(e) => setUrlsText(e.target.value)}
              rows={10}
              className="font-mono text-sm"
              disabled={isParsing}
            />
          </div>

          {/* Parse results summary */}
          {parsedResults && (
            <div className="bg-[#0F1115] border border-white/10 rounded-xl p-4 space-y-2">
              <div className="flex items-center gap-2">
                <Link className="h-5 w-5 text-[#F7931A]" />
                <p className="font-semibold text-white">URLs Detected</p>
              </div>
              <div className="flex gap-4 text-sm">
                <span className="text-green-400">
                  {validCount} valid
                </span>
                {invalidCount > 0 && (
                  <span className="text-red-400">
                    {invalidCount} invalid
                  </span>
                )}
              </div>

              {/* Invalid URLs list */}
              {invalidCount > 0 && (
                <div className="mt-4 space-y-2">
                  <p className="text-sm font-medium text-[#94A3B8]">Invalid URLs:</p>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {parsedResults
                      .filter((p) => !p.isValid)
                      .map((p, i) => (
                        <div
                          key={i}
                          className="bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2"
                        >
                          <p className="text-sm text-red-400 font-mono break-all">
                            {p.url}
                          </p>
                          <p className="text-xs text-red-300 mt-1">{p.error}</p>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-3 justify-end pt-4">
            <Button
              type="button"
              onClick={handleClose}
              className="bg-[#0F1115] border border-white/20 hover:border-white/40 hover:bg-[#0F1115] text-white transition-all"
            >
              Cancel
            </Button>

            {!parsedResults ? (
              <Button
                type="button"
                onClick={handleParseUrls}
                disabled={!urlsText.trim() || isParsing}
                className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                {isParsing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Parse URLs
              </Button>
            ) : (
              <Button
                type="button"
                onClick={handleContinue}
                disabled={validCount === 0}
                className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                Continue with {validCount} URL{validCount !== 1 ? 's' : ''}
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
