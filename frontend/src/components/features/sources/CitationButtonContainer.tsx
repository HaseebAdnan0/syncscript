'use client';

import { useState } from 'react';
import { CitationButton } from './CitationButton';
import { CitationPreviewModal } from './CitationPreviewModal';
import { generateCitation, pollCitationTask } from '@/lib/api/citations';
import type { CitationResponse } from '@/lib/api/citations';
import { toast } from '@/hooks/useToast';

interface CitationButtonContainerProps {
  sourceId: number;
  sourceTitle: string;
}

export function CitationButtonContainer({ sourceId, sourceTitle }: CitationButtonContainerProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [citation, setCitation] = useState<CitationResponse | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<string>('');

  const handleFormatSelect = async (format: string) => {
    setIsLoading(true);
    setSelectedFormat(format);

    try {
      // Call API to generate citation
      const response = await generateCitation(sourceId, format);

      // Check if this is an async AI citation (has task_id)
      if (response.task_id) {
        // Show loading toast for async citations
        toast({
          title: 'Generating citation...',
          description: 'AI is generating your citation. This may take a few seconds.',
        });

        // Poll for the result
        const result = await pollCitationTask(response.task_id);
        setCitation(result);
        setIsModalOpen(true);
      } else {
        // Structured citation returned immediately
        setCitation(response);
        setIsModalOpen(true);
      }
    } catch (error) {
      // Show error toast
      toast({
        title: 'Citation generation failed',
        description: error instanceof Error ? error.message : 'An error occurred while generating the citation.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setCitation(null);
    setSelectedFormat('');
  };

  return (
    <>
      <CitationButton onFormatSelect={handleFormatSelect} isLoading={isLoading} />
      {citation && (
        <CitationPreviewModal
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          citation={citation}
          format={selectedFormat}
          sourceTitle={sourceTitle}
        />
      )}
    </>
  );
}
