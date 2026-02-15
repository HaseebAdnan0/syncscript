'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useVault } from '@/hooks/useVaults';
import { useSources } from '@/hooks/useSources';
import { useVaultMembers } from '@/hooks/useVaultMembers';
import { useVaultPermissions } from '@/hooks/useVaultPermissions';
import { useVaultsStore } from '@/stores/vaultsStore';
import { useAuthStore } from '@/stores/authStore';
import { useReconnectionHandler } from '@/hooks/useReconnectionHandler';
import { SourcesList } from '@/components/features/vaults/SourcesList';
import { MembersList } from '@/components/features/vaults/MembersList';
import { VaultSettings } from '@/components/features/vaults/VaultSettings';
import { VaultDetailSkeleton } from '@/components/features/vaults/VaultDetailSkeleton';
import { PresenceIndicator } from '@/components/features/notifications/PresenceIndicator';
import { ResearchInsightsPanel } from '@/components/features/ai/ResearchInsightsPanel';
import { AILoadingSkeleton } from '@/components/features/ai/AILoadingSkeleton';
import ChatHistory from '@/components/features/ai/ChatHistory';
import AskAIChat from '@/components/features/ai/AskAIChat';
import { ExportCitationsButton } from '@/components/features/vaults/ExportCitationsButton';
import { VaultRole, VaultInsights, Conversation, ChatMessage } from '@/lib/types/vault';
import { getVaultInsights, getConversations, getConversation, askQuestion } from '@/lib/api/vaults';
import { useToast } from '@/hooks/useToast';
import * as Tabs from '@radix-ui/react-tabs';
import * as Collapsible from '@radix-ui/react-collapsible';
import { ArrowLeft, ChevronDown, MessageSquare } from 'lucide-react';

export default function VaultDetailPage() {
  const params = useParams();
  const router = useRouter();
  const vaultId = params.id as string;
  const { user } = useAuthStore();
  const { toast } = useToast();

  // Handle WebSocket reconnection with state recovery
  useReconnectionHandler({
    vaultId: vaultId,
    currentUserId: user?.id,
    enabled: !!vaultId,
  });

  // Fetch vault data
  const { data: vault, isLoading: vaultLoading, error: vaultError } = useVault(vaultId);

  // Fetch sources to get count
  const { data: sources = [] } = useSources(vaultId);

  // Fetch members to get count
  const { data: membersResponse } = useVaultMembers(vaultId);
  const members = membersResponse?.results || [];

  // Check user permissions (always call hook - conditionally use result)
  const permissions = useVaultPermissions(vault?.user_role || VaultRole.VIEWER);

  // Active tab from Zustand store
  const { activeTab, setActiveTab } = useVaultsStore();

  // AI Insights state
  const [insights, setInsights] = useState<VaultInsights | null>(null);
  const [isLoadingInsights, setIsLoadingInsights] = useState(false);
  const [isCachedInsights, setIsCachedInsights] = useState(false);

  // Chat state
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);

  // Fetch conversations on mount
  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const data = await getConversations(vaultId);
        setConversations(data);
      } catch (error) {
        console.error('Failed to fetch conversations:', error);
      }
    };

    if (vaultId) {
      fetchConversations();
    }
  }, [vaultId]);

  // Silently fetch cached insights when switching to insights tab
  useEffect(() => {
    const fetchCachedInsights = async () => {
      // Only fetch if we don't have insights yet and not already loading
      if (insights || isLoadingInsights) return;

      try {
        const data = await getVaultInsights(vaultId);
        setInsights(data);
        // Don't mark as cached - this is just normal loading of persisted data
      } catch {
        // Silently fail - user can click Generate to try again
        console.log('No cached insights available');
      }
    };

    if (activeTab === 'insights' && vaultId) {
      fetchCachedInsights();
    }
  }, [activeTab, vaultId, insights, isLoadingInsights]);

  // Load conversation messages when active conversation changes
  useEffect(() => {
    const loadConversation = async () => {
      if (!activeConversationId) {
        setMessages([]);
        return;
      }

      setIsLoadingMessages(true);
      try {
        const data = await getConversation(vaultId, activeConversationId);
        setMessages(data.messages);
      } catch (error: any) {
        toast({
          title: 'Failed to load conversation',
          description: error.response?.data?.error || 'Please try again.',
        });
      } finally {
        setIsLoadingMessages(false);
      }
    };

    loadConversation();
  }, [activeConversationId, vaultId, toast]);

  // Fetch insights handler
  const handleFetchInsights = async () => {
    setIsLoadingInsights(true);
    setIsCachedInsights(false);
    try {
      const data = await getVaultInsights(vaultId);
      setInsights(data);
      toast({
        title: 'Insights generated successfully',
      });
    } catch (error: any) {
      // Handle rate limit error (429)
      if (error.response?.status === 429) {
        // Show cached insights if available
        if (insights) {
          setIsCachedInsights(true);
          toast({
            title: 'Rate limit reached',
            description: 'Using cached insights. Try again later.',
          });
        } else {
          toast({
            title: 'Rate limit reached',
            description: error.response?.data?.error || 'Try again later.',
          });
        }
      } else {
        toast({
          title: 'Failed to generate insights',
          description: error.response?.data?.error || 'Please try again later.',
        });
      }
    } finally {
      setIsLoadingInsights(false);
    }
  };

  // Handle sending a message
  const handleSendMessage = async (question: string) => {
    setIsSending(true);
    try {
      const response = await askQuestion(vaultId, {
        question,
        conversation_id: activeConversationId || undefined,
      });

      // If this is a new conversation, update the active conversation ID
      if (!activeConversationId) {
        setActiveConversationId(response.conversation_id);
      }

      // Update conversation list
      const updatedConversations = await getConversations(vaultId);
      setConversations(updatedConversations);

      // Reload messages to get the latest
      const conversationData = await getConversation(vaultId, response.conversation_id);
      setMessages(conversationData.messages);

      toast({
        title: 'Response received',
      });
    } catch (error: any) {
      // Handle rate limit error (429)
      if (error.response?.status === 429) {
        toast({
          title: 'Rate limit reached',
          description: error.response?.data?.error || 'Try again later.',
        });
      } else {
        toast({
          title: 'Failed to send message',
          description: error.response?.data?.error || 'Please try again.',
        });
      }
    } finally {
      setIsSending(false);
    }
  };

  // Handle new chat
  const handleNewChat = () => {
    setActiveConversationId(null);
    setMessages([]);
  };

  // Handle conversation select
  const handleSelectConversation = (conversationId: number) => {
    setActiveConversationId(conversationId);
  };

  // Loading state
  if (vaultLoading) {
    return <VaultDetailSkeleton />;
  }

  // 404 handling
  if (vaultError || !vault) {
    return (
      <div className="min-h-screen bg-[#030304] flex flex-col items-center justify-center gap-4">
        <div className="text-red-500 text-xl">Vault not found</div>
        <button
          onClick={() => router.push('/vaults')}
          className="text-[#F7931A] hover:text-[#FFD600] transition-colors"
        >
          Return to vaults
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#030304] overflow-x-hidden">
      {/* Header */}
      <div className="bg-[#0F1115] border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-8">
          {/* Back button */}
          <button
            onClick={() => router.push('/vaults')}
            className="flex items-center gap-2 text-[#94A3B8] hover:text-white transition-colors mb-6"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to vaults</span>
          </button>

          {/* Vault name and description with presence indicator */}
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div className="flex-1">
              <h1 className="text-4xl font-bold text-white mb-2">{vault.name}</h1>
              {vault.description && (
                <p className="text-[#94A3B8] text-lg">{vault.description}</p>
              )}
            </div>
            {/* Active collaborators and export button */}
            <div className="flex-shrink-0 flex items-center gap-4">
              <PresenceIndicator
                vaultId={vaultId.toString()}
                currentUserId={user?.id}
              />
              <ExportCitationsButton
                vaultId={vaultId}
                vaultName={vault.name}
                sourceCount={sources.length}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Main content with tabs and sidebar */}
      <div className={`mx-auto px-6 py-12 transition-all duration-300 ${isChatOpen ? 'max-w-[1600px]' : 'max-w-7xl'}`}>
        <div className="flex flex-col lg:flex-row gap-8 min-w-0">
          {/* Main content area */}
          <div className={`min-w-0 transition-all duration-300 ${isChatOpen ? 'lg:w-1/2 lg:flex-shrink-0' : 'flex-1'}`}>
            <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
              {/* Tab list */}
              <Tabs.List className="flex gap-8 border-b border-white/10 mb-8">
                <Tabs.Trigger
                  value="sources"
                  className="pb-4 px-2 text-[#94A3B8] hover:text-white transition-colors relative data-[state=active]:text-white"
                >
                  <span className="text-lg font-medium">
                    Sources {sources.length > 0 && <span className="text-sm">({sources.length})</span>}
                  </span>
                  {/* Active indicator */}
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#F7931A] opacity-0 data-[state=active]:opacity-100 transition-opacity" />
                </Tabs.Trigger>

                <Tabs.Trigger
                  value="insights"
                  className="pb-4 px-2 text-[#94A3B8] hover:text-white transition-colors relative data-[state=active]:text-white"
                >
                  <span className="text-lg font-medium">Insights</span>
                  {/* Active indicator */}
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#F7931A] opacity-0 data-[state=active]:opacity-100 transition-opacity" />
                </Tabs.Trigger>

                <Tabs.Trigger
                  value="members"
                  className="pb-4 px-2 text-[#94A3B8] hover:text-white transition-colors relative data-[state=active]:text-white"
                >
                  <span className="text-lg font-medium">
                    Members {members.length > 0 && <span className="text-sm">({members.length})</span>}
                  </span>
                  {/* Active indicator */}
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#F7931A] opacity-0 data-[state=active]:opacity-100 transition-opacity" />
                </Tabs.Trigger>

                {/* Settings tab - hidden for Viewers */}
                {permissions && !permissions.isViewer && (
                  <Tabs.Trigger
                    value="settings"
                    className="pb-4 px-2 text-[#94A3B8] hover:text-white transition-colors relative data-[state=active]:text-white"
                  >
                    <span className="text-lg font-medium">Settings</span>
                    {/* Active indicator */}
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#F7931A] opacity-0 data-[state=active]:opacity-100 transition-opacity" />
                  </Tabs.Trigger>
                )}
              </Tabs.List>

              {/* Tab content */}
              <Tabs.Content value="sources">
                <SourcesList vaultId={vaultId} userRole={vault.user_role} />
              </Tabs.Content>

              <Tabs.Content value="insights">
                {isLoadingInsights ? (
                  <AILoadingSkeleton variant="insights" />
                ) : (
                  <div className="relative">
                    {isCachedInsights && (
                      <div className="mb-4 p-4 bg-[#F7931A]/10 border border-[#F7931A]/30 rounded-xl">
                        <p className="text-[#F7931A] text-sm">
                          <strong>Using cached data</strong> - You've reached your daily AI request limit. These insights may be outdated.
                        </p>
                      </div>
                    )}
                    <ResearchInsightsPanel
                      insights={insights}
                      onRefresh={handleFetchInsights}
                      sourceCount={sources.length}
                      isLoading={isLoadingInsights}
                      lastUpdated={insights?.generated_at}
                    />
                  </div>
                )}
              </Tabs.Content>

              <Tabs.Content value="members">
                <MembersList vaultId={vaultId} userRole={vault.user_role} currentUserId={user?.id} />
              </Tabs.Content>

              {/* Settings tab content - hidden for Viewers */}
              {permissions && !permissions.isViewer && (
                <Tabs.Content value="settings">
                  <VaultSettings vault={vault} userRole={vault.user_role} />
                </Tabs.Content>
              )}
            </Tabs.Root>
          </div>

          {/* Sidebar with Ask AI chat */}
          <div className={`w-full lg:flex-shrink-0 transition-all duration-300 ${isChatOpen ? 'lg:w-1/2' : 'lg:w-80'}`}>
            <Collapsible.Root open={isChatOpen} onOpenChange={setIsChatOpen}>
              <div className="bg-[#0F1115] border border-white/10 rounded-2xl overflow-hidden h-full">
                {/* Collapsible trigger */}
                <Collapsible.Trigger asChild>
                  <button className="w-full px-6 py-4 flex items-center justify-between text-white hover:bg-white/5 transition-colors">
                    <div className="flex items-center gap-3">
                      <MessageSquare className="w-5 h-5 text-[#F7931A]" />
                      <span className="font-bold text-lg">Ask AI</span>
                    </div>
                    <span className="text-xs text-[#94A3B8] flex items-center gap-1">
                      {isChatOpen ? 'Collapse' : 'Expand'}
                      <ChevronDown
                        className={`w-4 h-4 transition-transform ${
                          isChatOpen ? 'rotate-180' : ''
                        }`}
                      />
                    </span>
                  </button>
                </Collapsible.Trigger>

                {/* Collapsible content */}
                <Collapsible.Content className="border-t border-white/10">
                  <div className="flex h-[600px]">
                    {/* Chat history sidebar */}
                    <div className="w-44 border-r border-white/10 flex-shrink-0">
                      <ChatHistory
                        vaultId={vaultId.toString()}
                        conversations={conversations}
                        activeId={activeConversationId}
                        onSelect={handleSelectConversation}
                        onNewChat={handleNewChat}
                      />
                    </div>

                    {/* Chat area */}
                    <div className="flex-1 flex flex-col min-w-0">
                      {isLoadingMessages ? (
                        <div className="p-4">
                          <AILoadingSkeleton variant="chat" />
                        </div>
                      ) : (
                        <AskAIChat
                          vaultId={vaultId}
                          conversationId={activeConversationId || undefined}
                          onNewConversation={(id) => setActiveConversationId(id)}
                          messages={messages}
                          onSendMessage={handleSendMessage}
                          isLoading={isSending}
                        />
                      )}
                    </div>
                  </div>
                </Collapsible.Content>
              </div>
            </Collapsible.Root>
          </div>
        </div>
      </div>
    </div>
  );
}
