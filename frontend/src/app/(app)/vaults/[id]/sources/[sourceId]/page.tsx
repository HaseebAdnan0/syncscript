'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Loader2, ExternalLink } from 'lucide-react';
import { useVault } from '@/hooks/useVaults';
import { useSourcesQuery } from '@/hooks/useSourcesQuery';
import { useAnnotationsQuery } from '@/hooks/useAnnotationsQuery';
import { useCreateAnnotation, useDeleteAnnotation } from '@/hooks/useAnnotationMutations';
import { useAnnotationsWebSocket } from '@/hooks/useAnnotationsWebSocket';
import { useAuthStore } from '@/stores/authStore';
import { SourceTypeBadge } from '@/components/features/sources/SourceTypeBadge';
import { PDFViewer } from '@/components/features/sources/PDFViewer';
import { AnnotationSidebar } from '@/components/features/sources/AnnotationSidebar';
import { AddAnnotationForm } from '@/components/features/sources/AddAnnotationForm';
import AISummaryCard from '@/components/features/ai/AISummaryCard';
import { AILoadingSkeleton } from '@/components/features/ai/AILoadingSkeleton';
import { summarizeSource, getPdfViewUrl } from '@/lib/api/sources';
import { toast } from '@/hooks/useToast';
import { SourceType } from '@/lib/types/sources';
import type { AISummary } from '@/lib/types/sources';

export default function SourceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const vaultId = params.id as string;
  const sourceId = parseInt(params.sourceId as string, 10);

  const { user } = useAuthStore();
  const { data: vault, isLoading: vaultLoading } = useVault(vaultId);
  const { data: sourcesResponse, isLoading: sourcesLoading, refetch: refetchSources } = useSourcesQuery({ vaultId });

  // Find the specific source from the sources list
  const source = sourcesResponse?.find((s) => s.id === sourceId);

  // Annotations data
  const { data: annotations = [], isLoading: annotationsLoading } = useAnnotationsQuery({ sourceId });
  const createAnnotationMutation = useCreateAnnotation();
  const deleteAnnotationMutation = useDeleteAnnotation();

  // AI Summary state
  const [aiSummary, setAiSummary] = useState<AISummary | null>(source?.ai_summary ?? null);
  const [isSummarizing, setIsSummarizing] = useState(false);

  // Annotation form state
  const [showAddForm, setShowAddForm] = useState(false);

  // PDF presigned URL state (for uploaded PDFs)
  const [presignedPdfUrl, setPresignedPdfUrl] = useState<string | null>(null);
  const [isPdfUrlLoading, setIsPdfUrlLoading] = useState(false);

  // Real-time annotation updates via WebSocket
  useAnnotationsWebSocket({ vaultId, sourceId });

  // Extract citation as string for type safety
  const citation = source?.metadata?.citation;
  const citationText = typeof citation === 'string' ? citation : null;

  // Determine if the source is a PDF that can be rendered
  const isPdfSource = source?.source_type === SourceType.PDF;

  // For arxiv links, convert abstract URL to PDF URL
  const getPdfUrl = (url: string): string | null => {
    if (!url) return null;

    // Handle arxiv URLs - convert abs to pdf
    const arxivAbsMatch = url.match(/arxiv\.org\/abs\/(\d+\.\d+)/);
    if (arxivAbsMatch) {
      return `https://arxiv.org/pdf/${arxivAbsMatch[1]}.pdf`;
    }

    // If URL ends with .pdf, use it directly
    if (url.toLowerCase().endsWith('.pdf')) {
      return url;
    }

    // If source type is PDF but URL is a placeholder, return null (will use presigned URL)
    if (isPdfSource && url.includes('pdf.internal')) {
      return null;
    }

    // If source type is PDF, assume the URL is a PDF
    if (isPdfSource) {
      return url;
    }

    return null;
  };

  // Use presigned URL for uploaded PDFs, otherwise use the source URL
  const pdfUrl = presignedPdfUrl || (source?.url ? getPdfUrl(source.url) : null);

  // Update AI summary when source data changes
  useEffect(() => {
    if (source?.ai_summary) {
      setAiSummary(source.ai_summary);
    }
  }, [source?.ai_summary]);

  useEffect(() => {
    if (vault && source) {
      document.title = `${source.title} - Sources | SyncScript`;
    }
  }, [vault, source]);

  // Fetch presigned URL for uploaded PDFs
  useEffect(() => {
    const fetchPdfUrl = async () => {
      if (!source) return;

      // Only fetch for PDF sources with a pdfUploadId in metadata
      const pdfUploadId = source.metadata?.pdfUploadId as string | undefined;
      if (source.source_type !== SourceType.PDF || !pdfUploadId) {
        return;
      }

      // Check if URL is the placeholder (pdf.internal)
      if (!source.url?.includes('pdf.internal')) {
        return; // URL is already valid, no need to fetch
      }

      setIsPdfUrlLoading(true);
      try {
        const response = await getPdfViewUrl(pdfUploadId);
        setPresignedPdfUrl(response.view_url);
      } catch (error) {
        console.error('Failed to fetch PDF download URL:', error);
        toast({
          title: 'PDF Load Error',
          description: 'Unable to load PDF. Please try again.',
        });
      } finally {
        setIsPdfUrlLoading(false);
      }
    };

    fetchPdfUrl();
  }, [source]);

  const handleGenerateSummary = async (regenerate = false) => {
    if (!source) return;

    setIsSummarizing(true);
    try {
      const updatedSource = await summarizeSource(sourceId, regenerate);
      setAiSummary(updatedSource.ai_summary ?? null);

      // Refetch sources to update cache
      await refetchSources();

      toast({
        title: regenerate ? 'Summary Regenerated' : 'Summary Generated',
        description: 'AI analysis completed successfully.',
      });
    } catch (error: unknown) {
      const err = error as { response?: { status?: number; data?: { error?: string } } };

      if (err.response?.status === 429) {
        toast({
          title: 'AI Request Limit Reached',
          description: err.response.data?.error || 'You have reached your daily AI request limit. Cached summaries are still available.',
        });
      } else {
        toast({
          title: 'Summary Generation Failed',
          description: 'Unable to generate AI summary. Please try again later.',
        });
      }
    } finally {
      setIsSummarizing(false);
    }
  };

  const handleAddAnnotation = async (text: string, pageNumber?: number) => {
    await createAnnotationMutation.mutateAsync({
      sourceId,
      text,
      pageNumber,
    });
    setShowAddForm(false);
  };

  const handleDeleteAnnotation = async (annotationId: number) => {
    await deleteAnnotationMutation.mutateAsync({
      annotationId,
      sourceId,
    });
  };

  if (vaultLoading || sourcesLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#030304]">
        <Loader2 className="w-8 h-8 animate-spin text-[#F7931A]" />
      </div>
    );
  }

  if (!vault || !source) {
    return (
      <div className="min-h-screen bg-[#030304] text-white p-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold mb-4">Source Not Found</h1>
          <button
            onClick={() => router.push(`/vaults/${vaultId}/sources`)}
            className="text-[#F7931A] hover:underline flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Sources
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#030304] text-white">
      {/* Header */}
      <div className="bg-[#0F1115] border-b border-white/10 sticky top-0 z-10">
        <div className="max-w-[1800px] mx-auto px-6 py-4">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-sm text-[#94A3B8] mb-3">
            <button
              onClick={() => router.push(`/vaults/${vaultId}`)}
              className="hover:text-white transition-colors"
            >
              {vault.name}
            </button>
            <span>/</span>
            <button
              onClick={() => router.push(`/vaults/${vaultId}/sources`)}
              className="hover:text-white transition-colors"
            >
              Sources
            </button>
            <span>/</span>
            <span className="text-white">{source.title}</span>
          </div>

          {/* Source Header */}
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4 flex-1">
              <button
                onClick={() => router.push(`/vaults/${vaultId}/sources`)}
                className="mt-1 text-[#94A3B8] hover:text-white transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h1 className="text-2xl font-bold font-heading">{source.title}</h1>
                  <SourceTypeBadge type={source.source_type} />
                </div>
                {/* Metadata */}
                <div className="flex items-center gap-4 text-sm text-[#94A3B8]">
                  {/* Show URL for non-PDF sources, or presigned URL for uploaded PDFs */}
                  {source.url && !source.url.includes('pdf.internal') && (
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-[#F7931A] transition-colors truncate max-w-md flex items-center gap-1"
                    >
                      {source.url}
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                  {isPdfSource && typeof source.metadata?.pdfUploadId === 'string' && (
                    <span className="text-[#F7931A]">Uploaded PDF</span>
                  )}
                  {citationText && (
                    <span className="font-mono text-xs">
                      {citationText}
                    </span>
                  )}
                  <span>Added by {source.created_by || 'Unknown'}</span>
                  <span>
                    {new Date(source.created_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Two-Column Layout */}
      <div className="max-w-[1800px] mx-auto px-6 py-8">
        <div className="flex gap-8">
          {/* Document Viewer (70%) */}
          <div className="flex-[7] space-y-8">
            {/* AI Summary Card */}
            {isSummarizing ? (
              <AILoadingSkeleton variant="summary" />
            ) : (
              <AISummaryCard
                summary={aiSummary}
                onRegenerate={() => handleGenerateSummary(aiSummary !== null)}
              />
            )}

            {/* Document Viewer */}
            <div className="bg-[#0F1115] border border-white/10 rounded-2xl p-4 min-h-[600px]">
              {isPdfUrlLoading ? (
                <div className="flex flex-col items-center justify-center h-[600px] text-[#94A3B8] gap-4">
                  <Loader2 className="w-8 h-8 animate-spin text-[#F7931A]" />
                  <p>Loading PDF...</p>
                </div>
              ) : pdfUrl ? (
                <PDFViewer url={pdfUrl} className="h-[700px]" />
              ) : (
                // Fallback for non-PDF sources - show external link
                <div className="flex flex-col items-center justify-center h-full text-[#94A3B8] gap-4">
                  <div className="text-center">
                    <p className="mb-4">This source cannot be previewed directly.</p>
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all"
                    >
                      <ExternalLink className="w-5 h-5" />
                      Open in New Tab
                    </a>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Annotation Sidebar (30%) */}
          <div className="flex-[3]">
            <div className="bg-[#0F1115] border border-white/10 rounded-2xl min-h-[600px] sticky top-24">
              {showAddForm ? (
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-heading font-bold">Add Annotation</h2>
                    <button
                      onClick={() => setShowAddForm(false)}
                      className="text-[#94A3B8] hover:text-white transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                  <AddAnnotationForm
                    vaultMembers={[]}
                    onSubmit={handleAddAnnotation}
                    onCancel={() => setShowAddForm(false)}
                    isLoading={createAnnotationMutation.isPending}
                  />
                </div>
              ) : (
                <AnnotationSidebar
                  annotations={annotations}
                  isLoading={annotationsLoading}
                  onAddAnnotation={() => setShowAddForm(true)}
                  onDelete={handleDeleteAnnotation}
                  currentUserId={user?.id}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
