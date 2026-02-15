'use client';

import { useState, useCallback } from 'react';
import { Loader2, CheckCircle, AlertCircle, X, Link, FileText } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { previewUrl, type UrlPreviewResponse } from '@/lib/api/sources';
import { useAddSourceMutation } from '@/hooks/useAddSourceMutation';
import { SourceType } from '@/lib/types/sources';
import { FileUploadZone } from '@/components/features/uploads/FileUploadZone';
import { UploadProgressBar } from '@/components/features/uploads/UploadProgressBar';
import { useFileUpload, type UploadState } from '@/hooks/useFileUpload';

type SourceTab = 'url' | 'pdf';

interface AddSourceModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  vaultId: string;
}

export function AddSourceModal({ open, onOpenChange, vaultId }: AddSourceModalProps) {
  const [activeTab, setActiveTab] = useState<SourceTab>('url');

  // URL state
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [preview, setPreview] = useState<UrlPreviewResponse | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);

  // PDF upload state
  const { uploads, uploadFile, cancelUpload } = useFileUpload();
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isCreatingSource, setIsCreatingSource] = useState(false);

  const addSourceMutation = useAddSourceMutation();

  const resetState = () => {
    setActiveTab('url');
    setUrl('');
    setPreview(null);
    setPreviewError(null);
    setIsLoading(false);
    setUploadError(null);
    setIsCreatingSource(false);
  };

  const handleClose = (open: boolean) => {
    if (!open) {
      resetState();
    }
    onOpenChange(open);
  };

  const handleFetchMetadata = async () => {
    if (!url.trim()) return;

    setIsLoading(true);
    setPreviewError(null);
    setPreview(null);

    try {
      const result = await previewUrl(url.trim());
      setPreview(result);

      if (result.error) {
        setPreviewError(result.error);
      }
    } catch (error) {
      setPreviewError(
        error instanceof Error ? error.message : 'Failed to fetch metadata'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddSource = async () => {
    if (!preview) return;

    try {
      await addSourceMutation.mutateAsync({
        vault: vaultId,
        url: preview.url,
        title: preview.title,
        source_type: SourceType.URL,
        metadata: {
          author: preview.authors?.join(', '),
          description: preview.abstract,
          publishedDate: preview.publication_date || undefined,
        },
      });

      // Close modal on success
      handleClose(false);
    } catch {
      // Error is handled by the mutation hook (shows toast)
    }
  };

  // Handle PDF file selection
  const handleFilesSelected = useCallback(async (files: File[]) => {
    setUploadError(null);

    for (const file of files) {
      // Validate it's a PDF
      if (file.type !== 'application/pdf') {
        setUploadError('Only PDF files are supported');
        continue;
      }

      try {
        // Upload the file - the hook handles presigned URL, S3 upload, and completion
        await uploadFile(file, vaultId);
      } catch (error) {
        setUploadError(error instanceof Error ? error.message : 'Upload failed');
      }
    }
  }, [uploadFile, vaultId]);

  // Create source after upload completes
  const handleCreateSourceFromPdf = async (uploadState: UploadState) => {
    if (!uploadState.fileKey) {
      setUploadError('Upload incomplete - missing file key');
      return;
    }

    setIsCreatingSource(true);
    try {
      // Create a Source record with type PDF
      // The upload hook already called the complete endpoint
      await addSourceMutation.mutateAsync({
        vault: vaultId,
        title: uploadState.file.name.replace('.pdf', ''),
        source_type: SourceType.PDF,
        metadata: {
          filename: uploadState.file.name,
          fileSize: uploadState.file.size,
          fileKey: uploadState.fileKey,
          pdfUploadId: uploadState.uploadId,
        },
      });

      // Close modal on success
      handleClose(false);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Failed to create source');
    } finally {
      setIsCreatingSource(false);
    }
  };

  // Get current uploads as array
  const currentUploads = Array.from(uploads.entries());

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader>
          <DialogTitle>Add Source</DialogTitle>
          <DialogDescription>
            Add a URL or upload a PDF to your knowledge vault
          </DialogDescription>
        </DialogHeader>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-white/10 pb-2">
          <button
            onClick={() => setActiveTab('url')}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
              activeTab === 'url'
                ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white shadow-[0_0_15px_-5px_rgba(234,88,12,0.5)]'
                : 'text-[#94A3B8] hover:text-white hover:bg-white/5'
            }`}
          >
            <Link className="h-4 w-4" />
            URL
          </button>
          <button
            onClick={() => setActiveTab('pdf')}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
              activeTab === 'pdf'
                ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white shadow-[0_0_15px_-5px_rgba(234,88,12,0.5)]'
                : 'text-[#94A3B8] hover:text-white hover:bg-white/5'
            }`}
          >
            <FileText className="h-4 w-4" />
            PDF Upload
          </button>
        </div>

        <div className="space-y-4 py-4">
          {/* URL Tab */}
          {activeTab === 'url' && (
            <>
              {/* URL Input */}
              <div className="space-y-2">
                <label htmlFor="url" className="text-sm font-medium text-white">
                  URL
                </label>
                <input
                  id="url"
                  type="url"
                  placeholder="https://arxiv.org/abs/1234.56789"
                  value={url}
                  onChange={(e) => {
                    setUrl(e.target.value);
                    setPreview(null);
                    setPreviewError(null);
                  }}
                  className="w-full bg-black/50 border-b-2 border-white/20 h-12 px-4 text-white focus:border-[#F7931A] focus:outline-none transition-colors"
                  disabled={isLoading || addSourceMutation.isPending}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !isLoading && !preview) {
                      handleFetchMetadata();
                    }
                  }}
                />
              </div>

              {/* Fetch Metadata Button (only show if no preview yet) */}
              {!preview && (
                <Button
                  onClick={handleFetchMetadata}
                  disabled={!url.trim() || isLoading}
                  className="w-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Fetching Metadata...
                    </>
                  ) : (
                    'Fetch Metadata'
                  )}
                </Button>
              )}

              {/* Loading State */}
              {isLoading && (
                <div className="flex items-center justify-center py-8">
                  <div className="flex flex-col items-center gap-3">
                    <Loader2 className="h-8 w-8 animate-spin text-[#F7931A]" />
                    <p className="text-sm text-[#94A3B8]">Fetching metadata from URL...</p>
                  </div>
                </div>
              )}

              {/* Preview Error */}
              {previewError && !preview && (
                <div className="flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30">
                  <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-red-400">Failed to fetch metadata</p>
                    <p className="text-sm text-red-400/70 mt-1">{previewError}</p>
                  </div>
                </div>
              )}

              {/* Metadata Preview */}
              {preview && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm text-green-400">
                      <CheckCircle className="h-4 w-4" />
                      <span>Metadata fetched successfully</span>
                    </div>
                    <button
                      onClick={() => {
                        setPreview(null);
                        setPreviewError(null);
                      }}
                      className="text-[#94A3B8] hover:text-white transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>

                  <div className="p-4 rounded-xl bg-[#0F1115] border border-white/10 space-y-3">
                    <div>
                      <label className="text-xs text-[#94A3B8] uppercase tracking-wider">Title</label>
                      <p className="text-white font-medium mt-1">{preview.title}</p>
                    </div>

                    {preview.authors && preview.authors.length > 0 && (
                      <div>
                        <label className="text-xs text-[#94A3B8] uppercase tracking-wider">Authors</label>
                        <p className="text-white mt-1">{preview.authors.join(', ')}</p>
                      </div>
                    )}

                    {preview.publication_date && (
                      <div>
                        <label className="text-xs text-[#94A3B8] uppercase tracking-wider">Published</label>
                        <p className="text-white mt-1">
                          {new Date(preview.publication_date).toLocaleDateString()}
                        </p>
                      </div>
                    )}

                    {preview.abstract && (
                      <div>
                        <label className="text-xs text-[#94A3B8] uppercase tracking-wider">Abstract</label>
                        <p className="text-[#94A3B8] text-sm mt-1 line-clamp-3">{preview.abstract}</p>
                      </div>
                    )}

                    {preview.error && (
                      <div className="flex items-start gap-2 text-yellow-400/80 text-sm">
                        <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                        <span>Some metadata couldn&apos;t be extracted: {preview.error}</span>
                      </div>
                    )}
                  </div>

                  {/* Add Source Button */}
                  <div className="flex gap-3">
                    <Button
                      variant="outline"
                      onClick={() => handleClose(false)}
                      className="flex-1 rounded-full"
                      disabled={addSourceMutation.isPending}
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleAddSource}
                      disabled={addSourceMutation.isPending}
                      className="flex-1 bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
                    >
                      {addSourceMutation.isPending ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Adding...
                        </>
                      ) : (
                        'Add Source'
                      )}
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}

          {/* PDF Upload Tab */}
          {activeTab === 'pdf' && (
            <>
              {/* Upload Zone - show if no uploads in progress */}
              {currentUploads.length === 0 && (
                <FileUploadZone
                  onFilesSelected={handleFilesSelected}
                  accept="application/pdf"
                  maxFiles={1}
                  disabled={isCreatingSource}
                  helpText="PDF files only (max 50MB)"
                />
              )}

              {/* Upload Progress */}
              {currentUploads.map(([uploadId, uploadState]) => (
                <div key={uploadId} className="space-y-4">
                  <UploadProgressBar
                    filename={uploadState.file.name}
                    progress={uploadState.progress}
                    status={uploadState.status}
                  />

                  {/* Show action buttons based on status */}
                  {uploadState.status === 'error' && (
                    <div className="flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30">
                      <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-red-400">Upload failed</p>
                        <p className="text-sm text-red-400/70 mt-1">{uploadState.error}</p>
                      </div>
                    </div>
                  )}

                  {uploadState.status === 'complete' && (
                    <div className="space-y-4">
                      <div className="flex items-center gap-2 text-sm text-green-400">
                        <CheckCircle className="h-4 w-4" />
                        <span>File uploaded successfully</span>
                      </div>

                      <div className="p-4 rounded-xl bg-[#0F1115] border border-white/10 space-y-2">
                        <div>
                          <label className="text-xs text-[#94A3B8] uppercase tracking-wider">Filename</label>
                          <p className="text-white font-medium mt-1">{uploadState.file.name}</p>
                        </div>
                        <div>
                          <label className="text-xs text-[#94A3B8] uppercase tracking-wider">Size</label>
                          <p className="text-white mt-1">
                            {(uploadState.file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>

                      <div className="flex gap-3">
                        <Button
                          variant="outline"
                          onClick={() => handleClose(false)}
                          className="flex-1 rounded-full"
                          disabled={isCreatingSource}
                        >
                          Cancel
                        </Button>
                        <Button
                          onClick={() => handleCreateSourceFromPdf(uploadState)}
                          disabled={isCreatingSource}
                          className="flex-1 bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
                        >
                          {isCreatingSource ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Adding...
                            </>
                          ) : (
                            'Add Source'
                          )}
                        </Button>
                      </div>
                    </div>
                  )}

                  {(uploadState.status === 'uploading' || uploadState.status === 'processing') && (
                    <Button
                      variant="outline"
                      onClick={() => cancelUpload(uploadId)}
                      className="w-full rounded-full"
                    >
                      Cancel Upload
                    </Button>
                  )}
                </div>
              ))}

              {/* Upload Error */}
              {uploadError && currentUploads.length === 0 && (
                <div className="flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30">
                  <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-red-400">Upload Error</p>
                    <p className="text-sm text-red-400/70 mt-1">{uploadError}</p>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
