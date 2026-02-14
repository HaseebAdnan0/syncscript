"use client";

import React from "react";
import { MessageSquare, Plus } from "lucide-react";

interface ConversationPreview {
  id: number;
  created_at: string;
  preview: string;
}

interface ChatHistoryProps {
  vaultId: string;
  conversations: ConversationPreview[];
  activeId: number | null;
  onSelect: (conversationId: number) => void;
  onNewChat: () => void;
}

export default function ChatHistory({
  conversations,
  activeId,
  onSelect,
  onNewChat,
}: ChatHistoryProps) {
  const getRelativeTime = (timestamp: string) => {
    const now = new Date();
    const then = new Date(timestamp);
    const diffMs = now.getTime() - then.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return then.toLocaleDateString();
  };

  return (
    <div className="flex flex-col h-full bg-[#0F1115] border-r border-white/10">
      {/* Header with New Chat button */}
      <div className="p-4 border-b border-white/10">
        <button
          onClick={onNewChat}
          className="w-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all flex items-center justify-center gap-2"
        >
          <Plus className="w-5 h-5" />
          New Chat
        </button>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {conversations.length === 0 ? (
          <div className="text-center text-[#94A3B8] py-8">
            <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="text-sm">No conversations yet</p>
            <p className="text-xs mt-1">Start a new chat to get started</p>
          </div>
        ) : (
          conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => onSelect(conv.id)}
              className={`w-full text-left p-3 rounded-lg transition-all ${
                activeId === conv.id
                  ? "bg-gradient-to-r from-[#EA580C]/20 to-[#F7931A]/20 border border-[#F7931A]/50"
                  : "bg-black/30 border border-white/10 hover:border-[#F7931A]/30 hover:bg-black/50"
              }`}
            >
              {/* Preview text */}
              <div className="text-white text-sm mb-2 line-clamp-2">
                {conv.preview}
              </div>

              {/* Timestamp */}
              <div className="text-[#94A3B8] text-xs">
                {getRelativeTime(conv.created_at)}
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
