'use client';



interface Citation {
  source_id: number;
  source_title: string;
  excerpt: string;
}

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: string;
}

export default function ChatMessage({
  role,
  content,
  citations = [],
  timestamp,
}: ChatMessageProps) {
  const isUser = role === 'user';

  return (
    <div className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        {/* Message bubble */}
        <div
          className={`${
            isUser
              ? 'bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white rounded-2xl rounded-br-none'
              : 'bg-[#0F1115] border border-white/10 rounded-2xl rounded-bl-none backdrop-blur-lg'
          } px-4 py-3`}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
        </div>

        {/* Citations (only for assistant messages) */}
        {!isUser && citations && citations.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2 px-2">
            {citations.map((citation) => (
              <button
                key={`${citation.source_id}-${citation.source_title}`}
                className="group relative inline-flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r from-[#EA580C]/20 to-[#F7931A]/20 border border-[#F7931A]/30 rounded-full text-xs text-[#F7931A] hover:border-[#F7931A] hover:shadow-[0_0_12px_-3px_rgba(247,147,26,0.5)] transition-all"
                title={citation.source_title}
              >
                <svg
                  className="w-3 h-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <span className="font-medium truncate max-w-[150px]">
                  {citation.source_title}
                </span>

                {/* Hover tooltip showing excerpt */}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10 w-64 p-3 bg-[#0F1115] border border-[#F7931A]/30 rounded-lg shadow-xl">
                  <p className="text-xs text-white/90 leading-relaxed">
                    {citation.excerpt}
                  </p>
                  {/* Tooltip arrow */}
                  <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-[#F7931A]/30" />
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Timestamp */}
        <span className={`text-xs text-white/40 px-2 ${isUser ? 'text-right' : 'text-left'}`}>
          {new Date(timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>
    </div>
  );
}
