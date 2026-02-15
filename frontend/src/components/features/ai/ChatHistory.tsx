"use client";

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
  conversations: conversationsProp,
  activeId,
  onSelect,
  onNewChat,
}: ChatHistoryProps) {
  // Ensure conversations is always an array
  const conversations = Array.isArray(conversationsProp) ? conversationsProp : [];
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
      <div className="p-3 border-b border-white/10">
        <button
          onClick={onNewChat}
          className="w-full bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-semibold text-xs uppercase tracking-wider rounded-full px-3 py-2.5 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all flex items-center justify-center gap-1.5"
        >
          <Plus className="w-4 h-4" />
          New
        </button>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
        {conversations.length === 0 ? (
          <div className="text-center text-[#94A3B8] py-6">
            <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-xs">No chats yet</p>
          </div>
        ) : (
          conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => onSelect(conv.id)}
              className={`w-full text-left p-2 rounded-lg transition-all ${
                activeId === conv.id
                  ? "bg-gradient-to-r from-[#EA580C]/20 to-[#F7931A]/20 border border-[#F7931A]/50"
                  : "bg-black/30 border border-white/10 hover:border-[#F7931A]/30 hover:bg-black/50"
              }`}
            >
              {/* Preview text */}
              <div className="text-white text-xs mb-1 line-clamp-2">
                {conv.preview}
              </div>

              {/* Timestamp */}
              <div className="text-[#94A3B8] text-[10px]">
                {getRelativeTime(conv.created_at)}
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
