'use client';

import { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { Upload } from 'lucide-react';

interface FileUploadZoneProps {
  onFilesSelected: (files: File[]) => void;
  accept?: string; // e.g., "application/pdf,image/png,image/jpeg"
  maxFiles?: number;
  disabled?: boolean;
  helpText?: string; // Custom help text (e.g., "PDF files only")
}

export function FileUploadZone({
  onFilesSelected,
  accept = 'application/pdf,image/png,image/jpeg',
  maxFiles = 10,
  disabled = false,
  helpText,
}: FileUploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Validate file types based on MIME type
  const validateFileType = (file: File): boolean => {
    const acceptedTypes = accept.split(',').map(type => type.trim());
    return acceptedTypes.includes(file.type);
  };

  // Handle file selection (drag or click)
  const handleFiles = (files: FileList | null) => {
    if (!files || disabled) return;

    const validFiles: File[] = [];
    const fileArray = Array.from(files);

    for (const file of fileArray) {
      if (!validateFileType(file)) {
        console.warn(`File "${file.name}" rejected: invalid type (${file.type})`);
        continue;
      }
      validFiles.push(file);
    }

    if (validFiles.length > maxFiles) {
      console.warn(`Only the first ${maxFiles} files will be uploaded`);
      onFilesSelected(validFiles.slice(0, maxFiles));
    } else if (validFiles.length > 0) {
      onFilesSelected(validFiles);
    }
  };

  // Drag and drop handlers
  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragOver(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  // Click to browse handler
  const handleClick = () => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files);
    // Reset input so same file can be selected again
    e.target.value = '';
  };

  return (
    <>
      <div
        onClick={handleClick}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer
          transition-all duration-300
          ${isDragOver
            ? 'border-[#F7931A] bg-[#F7931A]/10 scale-[1.02]'
            : 'border-white/20 bg-black/20 hover:border-[#F7931A]/50 hover:bg-[#F7931A]/5'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        {/* Upload Icon */}
        <div className="flex flex-col items-center gap-4">
          <div
            className={`
              rounded-full p-4 transition-all
              ${isDragOver
                ? 'bg-[#F7931A]/20 scale-110'
                : 'bg-white/5'
              }
            `}
          >
            <Upload
              className={`
                h-12 w-12 transition-colors
                ${isDragOver ? 'text-[#F7931A]' : 'text-[#94A3B8]'}
              `}
            />
          </div>

          {/* Text */}
          <div className="space-y-2">
            <p className="text-lg font-medium text-white">
              {isDragOver ? 'Drop files here' : 'Drop files here or click to browse'}
            </p>
            <p className="text-sm text-[#94A3B8]">
              {helpText || `Supports PDF, PNG, and JPG files (max ${maxFiles} ${maxFiles === 1 ? 'file' : 'files'})`}
            </p>
          </div>
        </div>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          multiple
          onChange={handleInputChange}
          className="hidden"
          disabled={disabled}
        />
      </div>
    </>
  );
}
