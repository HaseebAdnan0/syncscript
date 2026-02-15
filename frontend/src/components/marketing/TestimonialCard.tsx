'use client';

import { useState } from 'react';
import Image from 'next/image';

interface TestimonialCardProps {
  avatar?: string;
  name: string;
  title: string;
  institution: string;
  quote: string;
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) {
    return parts[0].substring(0, 2).toUpperCase();
  }
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export default function TestimonialCard({
  avatar,
  name,
  title,
  institution,
  quote,
}: TestimonialCardProps) {
  const [imageError, setImageError] = useState(false);
  const showFallback = !avatar || imageError;

  return (
    <div className="backdrop-blur-lg bg-white/5 border border-white/10 rounded-2xl p-8 hover:-translate-y-2 transition-all duration-300 h-full flex flex-col">
      {/* Quote */}
      <div className="flex-1 mb-6">
        <p className="text-white/90 leading-relaxed relative">
          <span className="text-[#F7931A] text-4xl font-serif absolute -top-4 -left-2">&ldquo;</span>
          <span className="relative z-10">{quote}</span>
          <span className="text-[#F7931A] text-4xl font-serif absolute -bottom-8 -right-2">&rdquo;</span>
        </p>
      </div>

      {/* Author Info */}
      <div className="flex items-center gap-4 pt-4 border-t border-white/10">
        {/* Avatar */}
        <div className="relative w-12 h-12 rounded-full overflow-hidden bg-gradient-to-br from-[#F7931A] to-[#FFD600] p-[2px]">
          <div className="w-full h-full rounded-full overflow-hidden bg-[#0F1115] flex items-center justify-center">
            {showFallback ? (
              <span className="text-white font-bold text-sm">
                {getInitials(name)}
              </span>
            ) : (
              <Image
                src={avatar!}
                alt={name}
                width={48}
                height={48}
                loading="lazy"
                className="w-full h-full object-cover"
                onError={() => setImageError(true)}
              />
            )}
          </div>
        </div>

        {/* Name and Title */}
        <div className="flex-1">
          <p className="text-white font-semibold">{name}</p>
          <p className="text-[#94A3B8] text-sm">{title}</p>
          <p className="text-[#94A3B8] text-sm">{institution}</p>
        </div>
      </div>
    </div>
  );
}
