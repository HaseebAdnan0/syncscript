import { useState, useCallback, useRef } from 'react';
import { api } from '@/lib/api';

export type UploadStatus = 'uploading' | 'processing' | 'complete' | 'error';

export interface UploadState {
  file: File;
  progress: number;
  status: UploadStatus;
  error?: string;
  uploadId?: string; // For multipart uploads
  fileKey?: string;
}

const MULTIPART_THRESHOLD = 20 * 1024 * 1024; // 20MB
const PART_SIZE = 5 * 1024 * 1024; // 5MB per part

export function useFileUpload() {
  const [uploads, setUploads] = useState<Map<string, UploadState>>(new Map());
  const xhrRefs = useRef<Map<string, XMLHttpRequest>>(new Map());

  /**
   * Add or update an upload in state
   */
  const updateUpload = useCallback((uploadId: string, update: Partial<UploadState>) => {
    setUploads((prev) => {
      const newMap = new Map(prev);
      const existing = newMap.get(uploadId);
      if (existing) {
        newMap.set(uploadId, { ...existing, ...update });
      }
      return newMap;
    });
  }, []);

  /**
   * Remove an upload from state
   */
  const removeUpload = useCallback((uploadId: string) => {
    setUploads((prev) => {
      const newMap = new Map(prev);
      newMap.delete(uploadId);
      return newMap;
    });
    xhrRefs.current.delete(uploadId);
  }, []);

  /**
   * Upload a single file with progress tracking
   */
  const uploadFile = useCallback(
    async (file: File, vaultId: string): Promise<string> => {
      const uploadId = `${Date.now()}-${file.name}`;

      // Initialize upload state
      const initialState: UploadState = {
        file,
        progress: 0,
        status: 'uploading',
      };
      setUploads((prev) => new Map(prev).set(uploadId, initialState));

      try {
        // Determine if multipart upload is needed
        const isMultipart = file.size > MULTIPART_THRESHOLD;

        if (isMultipart) {
          await uploadMultipart(uploadId, file, vaultId);
        } else {
          await uploadSingleFile(uploadId, file, vaultId);
        }

        // Mark as processing (backend will process the file)
        updateUpload(uploadId, { status: 'processing', progress: 100 });

        // Complete after a short delay (simulating backend processing acknowledgment)
        setTimeout(() => {
          updateUpload(uploadId, { status: 'complete' });
        }, 1000);

        return uploadId;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Upload failed';
        updateUpload(uploadId, { status: 'error', error: errorMessage });
        throw error;
      }
    },
    [updateUpload]
  );

  /**
   * Upload file using single presigned URL (for files < 20MB)
   */
  const uploadSingleFile = async (uploadId: string, file: File, vaultId: string) => {
    // Get presigned URL from backend
    const response = await api.post('/sources/pdfs/upload-url/', {
      vault_id: vaultId,
      filename: file.name,
      content_type: file.type,
      file_size: file.size,
    });

    const { upload_url, file_key } = response.data;
    updateUpload(uploadId, { fileKey: file_key });

    // Upload file to S3 using XMLHttpRequest for progress tracking
    await uploadToS3(uploadId, file, upload_url);
  };

  /**
   * Upload file using multipart upload (for files > 20MB)
   */
  const uploadMultipart = async (uploadId: string, file: File, vaultId: string) => {
    // Initiate multipart upload
    const initiateResponse = await api.post('/sources/pdfs/multipart-upload/initiate/', {
      vault_id: vaultId,
      filename: file.name,
      content_type: file.type,
      file_size: file.size,
    });

    const { upload_id, file_key } = initiateResponse.data;
    updateUpload(uploadId, { uploadId: upload_id, fileKey: file_key });

    // Upload parts
    const partCount = Math.ceil(file.size / PART_SIZE);
    const parts: Array<{ ETag: string; PartNumber: number }> = [];

    for (let partNumber = 1; partNumber <= partCount; partNumber++) {
      const start = (partNumber - 1) * PART_SIZE;
      const end = Math.min(start + PART_SIZE, file.size);
      const partBlob = file.slice(start, end);

      // Get presigned URL for this part
      const partResponse = await api.post('/sources/pdfs/multipart-upload/part-url/', {
        upload_id,
        file_key,
        part_number: partNumber,
      });

      const { upload_url } = partResponse.data;

      // Upload part with progress tracking
      const partProgress = ((partNumber - 1) / partCount) * 100;
      const etag = await uploadPartToS3(
        uploadId,
        partBlob,
        upload_url,
        partProgress,
        100 / partCount
      );

      parts.push({ ETag: etag, PartNumber: partNumber });
    }

    // Complete multipart upload
    await api.post('/sources/pdfs/multipart-upload/complete/', {
      upload_id,
      file_key,
      parts,
    });
  };

  /**
   * Upload file/part to S3 using XMLHttpRequest for progress tracking
   */
  const uploadToS3 = (
    uploadId: string,
    data: File | Blob,
    url: string,
    baseProgress = 0,
    progressRange = 100
  ): Promise<string> => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhrRefs.current.set(uploadId, xhr);

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percentComplete = (e.loaded / e.total) * progressRange + baseProgress;
          updateUpload(uploadId, { progress: Math.round(percentComplete) });
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const etag = xhr.getResponseHeader('ETag') || '';
          resolve(etag.replace(/"/g, '')); // Remove quotes from ETag
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Network error during upload'));
      });

      xhr.addEventListener('abort', () => {
        reject(new Error('Upload cancelled'));
      });

      xhr.open('PUT', url, true);
      xhr.setRequestHeader('Content-Type', data instanceof File ? data.type : 'application/octet-stream');
      xhr.send(data);
    });
  };

  /**
   * Upload a single part in multipart upload
   */
  const uploadPartToS3 = (
    uploadId: string,
    data: Blob,
    url: string,
    baseProgress: number,
    progressRange: number
  ): Promise<string> => {
    return uploadToS3(uploadId, data, url, baseProgress, progressRange);
  };

  /**
   * Retry a failed upload
   */
  const retryUpload = useCallback(
    async (uploadId: string) => {
      const upload = uploads.get(uploadId);
      if (!upload || upload.status !== 'error') {
        throw new Error('Upload not found or not in error state');
      }

      // Extract vault ID from fileKey (format: vaults/{vault_id}/pdfs/{uuid}.pdf)
      const vaultId = upload.fileKey?.split('/')[1];
      if (!vaultId) {
        throw new Error('Could not determine vault ID from file key');
      }

      // Remove old upload and create new one
      removeUpload(uploadId);
      return uploadFile(upload.file, vaultId);
    },
    [uploads, uploadFile, removeUpload]
  );

  /**
   * Cancel an ongoing upload
   */
  const cancelUpload = useCallback(
    async (uploadId: string) => {
      const upload = uploads.get(uploadId);
      const xhr = xhrRefs.current.get(uploadId);

      // Abort XHR if exists
      if (xhr) {
        xhr.abort();
      }

      // If multipart upload, abort on backend
      if (upload?.uploadId && upload?.fileKey) {
        try {
          await api.post('/sources/pdfs/multipart-upload/abort/', {
            upload_id: upload.uploadId,
            file_key: upload.fileKey,
          });
        } catch (error) {
          console.error('Failed to abort multipart upload:', error);
        }
      }

      // Remove from state
      removeUpload(uploadId);
    },
    [uploads, removeUpload]
  );

  return {
    uploads,
    uploadFile,
    retryUpload,
    cancelUpload,
  };
}
