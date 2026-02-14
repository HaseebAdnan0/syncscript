# PRD 15: AI Research Assistant

## Introduction

Add an AI-powered research assistant to SyncScript that helps researchers understand their sources faster and discover insights across their Knowledge Vaults. The assistant provides source summaries, vault-level thematic analysis, and natural language Q&A over vault contents.

This feature uses Claude as the AI backbone with a simple chunking strategy (no vector database initially), designed for future migration to semantic search. Rate limiting protects API costs while degraded mode ensures users always have access to cached results.

## Goals

- Generate structured academic summaries for any source (PDF or URL)
- Provide vault-level insights: common themes, research gaps, cross-references
- Enable natural language questions about vault contents with cited answers
- Track token usage per user for cost monitoring
- Enforce rate limits (20 AI requests/day) with graceful degradation
- Persist chat history (last 10 conversations per vault) for continuity

## User Stories

### US-001: Create AI app with core models
**Description:** As a developer, I need the database schema for AI features so I can track usage and store conversations.

**Acceptance Criteria:**
- [ ] Create `apps/ai/` Django app with models.py, views.py, urls.py, serializers.py
- [ ] `AIUsageLog` model: user (FK), request_type (enum: summary/insights/question), tokens_used (int), created_at
- [ ] `ChatConversation` model: vault (FK), user (FK), created_at, updated_at
- [ ] `ChatMessage` model: conversation (FK), role (enum: user/assistant), content (text), sources_cited (JSONField), created_at
- [ ] Add `ai_summary` JSONField to Source model (nullable)
- [ ] Add `ai_insights_cache` JSONField + `ai_insights_updated_at` to Vault model (nullable)
- [ ] Generate and run migrations
- [ ] Register app in INSTALLED_APPS
- [x] Typecheck passes

### US-002: Implement token usage tracking service
**Description:** As a developer, I need a service to track AI token usage so we can monitor costs and enforce limits.

**Acceptance Criteria:**
- [x] Create `apps/ai/services/usage.py`
- [x] `log_usage(user, request_type, tokens_used)` function saves AIUsageLog
- [x] `get_daily_usage(user)` returns total tokens and request count for today
- [x] `get_remaining_requests(user)` returns requests left (default limit: 20/day)
- [x] `AI_DAILY_LIMIT` setting in config (default 20)
- [x] Typecheck passes

### US-003: Create rate limiting decorator for AI endpoints
**Description:** As a developer, I need to rate limit AI requests so we control API costs.

**Acceptance Criteria:**
- [ ] Create `apps/ai/decorators.py` with `@ai_rate_limit` decorator
- [ ] Decorator checks `get_remaining_requests(user)` before allowing request
- [ ] Returns 429 with `{"error": "AI request limit reached", "resets_at": "<timestamp>", "cached_available": true}` when exceeded
- [ ] Decorator is reusable across all AI views
- [ ] Typecheck passes

### US-004: Implement Claude client service
**Description:** As a developer, I need a wrapper for Claude API calls with consistent error handling.

**Acceptance Criteria:**
- [ ] Create `apps/ai/services/claude_client.py`
- [ ] `ClaudeClient` class with `__init__` reading `ANTHROPIC_API_KEY` from settings
- [ ] `summarize(text, source_type)` method with academic summarization prompt
- [ ] `analyze_sources(sources_data)` method for vault insights
- [ ] `answer_question(question, context_chunks)` method for Q&A
- [ ] All methods return structured dict matching expected schema
- [ ] Graceful error handling: return `{"error": "..."}` on API failure
- [ ] Token counting using `anthropic` SDK's token counter
- [ ] Typecheck passes

### US-005: Add source text chunking utility
**Description:** As a developer, I need to chunk source text intelligently so it fits in Claude's context window for Q&A.

**Acceptance Criteria:**
- [ ] Create `apps/ai/services/chunking.py`
- [ ] `chunk_text(text, max_tokens=2000, overlap=200)` splits text into overlapping chunks
- [ ] `get_relevant_chunks(question, chunks, max_chunks=5)` returns most relevant chunks (keyword matching for now, vector-ready interface)
- [ ] Handles empty text gracefully
- [ ] Typecheck passes

### US-006: Implement source summarization endpoint
**Description:** As a user, I want to get an AI-generated summary of any source so I can quickly understand its contents.

**Acceptance Criteria:**
- [ ] `POST /api/v1/sources/{id}/summarize/` endpoint
- [ ] Requires authentication and source read permission
- [ ] If `source.ai_summary` exists and `regenerate=false`, return cached summary
- [ ] If `regenerate=true` or no cache: extract text (use existing PDF extraction or fetch URL content)
- [ ] Send to Claude with academic summarization prompt
- [ ] Response schema: `{abstract, key_findings[], methodology, limitations, keywords[], generated_at}`
- [ ] Save to `source.ai_summary` JSONField
- [ ] Log token usage via usage service
- [ ] Apply `@ai_rate_limit` decorator
- [ ] Typecheck passes

### US-007: Implement vault insights endpoint
**Description:** As a user, I want AI-generated insights about my vault so I can see themes and gaps across all sources.

**Acceptance Criteria:**
- [ ] `GET /api/v1/vaults/{id}/insights/` endpoint
- [ ] Requires authentication and vault read permission
- [ ] Return cached insights if `ai_insights_updated_at` < 24 hours old
- [ ] Gather all source summaries (or titles/abstracts if no summary)
- [ ] Send to Claude for thematic analysis
- [ ] Response: `{themes[], research_gaps[], cross_references[], suggested_searches[], generated_at}`
- [ ] Cache in vault's `ai_insights_cache` field
- [ ] Apply `@ai_rate_limit` decorator
- [ ] Typecheck passes

### US-008: Add cache invalidation for vault insights
**Description:** As a developer, I need to invalidate vault insights cache when sources change so insights stay fresh.

**Acceptance Criteria:**
- [ ] Django signal on Source post_save and post_delete
- [ ] If source's vault has `ai_insights_cache`, set `ai_insights_updated_at` to null
- [ ] Signal handler in `apps/ai/signals.py`
- [ ] Connect signals in `apps/ai/apps.py` ready()
- [ ] Typecheck passes

### US-009: Implement question answering endpoint
**Description:** As a user, I want to ask questions about my vault contents and get cited answers.

**Acceptance Criteria:**
- [ ] `POST /api/v1/vaults/{id}/ask/` endpoint with `{question, conversation_id?}` body
- [ ] Requires authentication and vault read permission
- [ ] Gather text from all sources in vault, chunk them
- [ ] Use `get_relevant_chunks()` to find relevant context
- [ ] Send question + context to Claude with citation instructions
- [ ] Response: `{answer, citations[{source_id, source_title, excerpt}], conversation_id}`
- [ ] Apply `@ai_rate_limit` decorator
- [ ] Log token usage
- [ ] Typecheck passes

### US-010: Implement chat history persistence
**Description:** As a user, I want my vault Q&A conversations saved so I can continue where I left off.

**Acceptance Criteria:**
- [ ] If `conversation_id` provided in ask request, append to existing conversation
- [ ] If not provided, create new ChatConversation
- [ ] Save user message and assistant response as ChatMessage records
- [ ] Store `sources_cited` in assistant message's JSONField
- [ ] Limit to 10 conversations per vault (delete oldest on overflow)
- [ ] `GET /api/v1/vaults/{id}/conversations/` lists conversations with preview
- [ ] `GET /api/v1/vaults/{id}/conversations/{conv_id}/` returns full message history
- [ ] Typecheck passes

### US-011: Add AI URL routes
**Description:** As a developer, I need to wire up all AI endpoints to the URL router.

**Acceptance Criteria:**
- [ ] Create `apps/ai/urls.py` with all AI routes
- [ ] Include in main `config/urls.py` under `/api/v1/`
- [ ] Routes: sources summarize, vault insights, vault ask, vault conversations
- [ ] Typecheck passes

### US-012: Create AISummaryCard component
**Description:** As a user, I want to see an expandable AI summary card on source pages.

**Acceptance Criteria:**
- [ ] Create `components/features/ai/AISummaryCard.tsx`
- [ ] Props: `sourceId`, `summary` (nullable), `onRegenerate`
- [ ] Collapsed state shows "AI Summary" header with expand chevron
- [ ] Expanded state shows collapsible sections: Key Findings, Methodology, Limitations, Keywords
- [ ] "Generate Summary" button if no summary exists
- [ ] "Regenerate" button in header when summary exists
- [ ] Follows Bitcoin DeFi design (glass card, orange accents)
- [ ] Typecheck passes

### US-013: Create AI loading skeleton
**Description:** As a user, I want to see a loading state while AI processes my request.

**Acceptance Criteria:**
- [ ] Create `components/features/ai/AILoadingSkeleton.tsx`
- [ ] Animated skeleton with "Analyzing..." text
- [ ] Pulsing orange accent animation
- [ ] Variants: `summary`, `insights`, `chat`
- [ ] Typecheck passes

### US-014: Integrate AISummaryCard into source detail page
**Description:** As a user, I want to see AI summaries on the source detail page.

**Acceptance Criteria:**
- [ ] Add AISummaryCard to source detail page layout
- [ ] Fetch summary from source data (already in API response)
- [ ] Wire "Generate" button to `POST /sources/{id}/summarize/`
- [ ] Wire "Regenerate" button with `regenerate=true`
- [ ] Show AILoadingSkeleton while request pending
- [ ] Handle rate limit error: show toast with "Limit reached" message
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-015: Create ResearchInsightsPanel component
**Description:** As a user, I want a panel showing AI insights about my vault's research themes.

**Acceptance Criteria:**
- [ ] Create `components/features/ai/ResearchInsightsPanel.tsx`
- [ ] Props: `vaultId`, `insights` (nullable), `onRefresh`
- [ ] Sections: Themes (tag cloud), Research Gaps (list), Cross-References (list), Suggested Searches
- [ ] "Generate Insights" button if none exist
- [ ] "Refresh" button with last-updated timestamp
- [ ] Empty state for vaults with < 2 sources
- [ ] Typecheck passes

### US-016: Create ThemeCloud component
**Description:** As a user, I want to visualize research themes as a tag cloud.

**Acceptance Criteria:**
- [ ] Create `components/features/ai/ThemeCloud.tsx`
- [ ] Props: `themes[{name, weight, source_count}]`
- [ ] Render as weighted tag cloud (larger = more common)
- [ ] Orange gradient coloring based on weight
- [ ] Hover shows source count tooltip
- [ ] Clickable tags (onClick prop for future filtering)
- [ ] Typecheck passes

### US-017: Integrate ResearchInsightsPanel into vault dashboard
**Description:** As a user, I want to see research insights on my vault dashboard.

**Acceptance Criteria:**
- [ ] Add "Insights" tab to vault dashboard tabs
- [ ] Fetch insights from `GET /vaults/{id}/insights/`
- [ ] Show ResearchInsightsPanel with fetched data
- [ ] Show AILoadingSkeleton while loading
- [ ] Handle rate limit: show cached insights with "Using cached data" badge
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-018: Create AskAIChat component
**Description:** As a user, I want a chat interface to ask questions about my vault.

**Acceptance Criteria:**
- [ ] Create `components/features/ai/AskAIChat.tsx`
- [ ] Props: `vaultId`, `conversationId?`, `onNewConversation`
- [ ] Input field with send button at bottom
- [ ] Message list showing user questions and AI responses
- [ ] AI responses show inline citations as clickable chips
- [ ] Auto-scroll to latest message
- [ ] Typecheck passes

### US-019: Create ChatMessage component
**Description:** As a user, I want nicely formatted chat messages with citations.

**Acceptance Criteria:**
- [ ] Create `components/features/ai/ChatMessage.tsx`
- [ ] Props: `role`, `content`, `citations[]`, `timestamp`
- [ ] User messages: right-aligned, subtle background
- [ ] Assistant messages: left-aligned, glass card style
- [ ] Citations rendered as orange pill badges linking to source
- [ ] Typecheck passes

### US-020: Create ChatHistory sidebar
**Description:** As a user, I want to see and switch between my past conversations.

**Acceptance Criteria:**
- [ ] Create `components/features/ai/ChatHistory.tsx`
- [ ] Props: `vaultId`, `conversations[]`, `activeId`, `onSelect`, `onNewChat`
- [ ] List of conversation previews (first message truncated)
- [ ] Active conversation highlighted
- [ ] "New Chat" button at top
- [ ] Shows relative timestamps
- [ ] Typecheck passes

### US-021: Integrate AskAI chat into vault sidebar
**Description:** As a user, I want to access the AI chat from my vault view.

**Acceptance Criteria:**
- [ ] Add "Ask AI" collapsible section to vault sidebar
- [ ] Fetch conversation list from `GET /vaults/{id}/conversations/`
- [ ] Load selected conversation messages
- [ ] Wire send to `POST /vaults/{id}/ask/`
- [ ] Update conversation list on new message
- [ ] Show loading skeleton while AI responds
- [ ] Handle rate limit: show message with retry time
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-022: Create TokenUsageDisplay component
**Description:** As a user, I want to see my AI usage stats in settings.

**Acceptance Criteria:**
- [ ] Create `components/features/ai/TokenUsageDisplay.tsx`
- [ ] Props: `usage{requests_today, requests_limit, tokens_today, resets_at}`
- [ ] Progress bar showing requests used / limit
- [ ] "Resets in X hours" countdown
- [ ] Token count display (informational)
- [ ] Warning state when > 80% used
- [ ] Typecheck passes

### US-023: Add AI usage endpoint
**Description:** As a user, I need an endpoint to fetch my current AI usage stats.

**Acceptance Criteria:**
- [ ] `GET /api/v1/ai/usage/` endpoint
- [ ] Returns `{requests_today, requests_limit, tokens_today, resets_at}`
- [ ] Requires authentication
- [ ] Typecheck passes

### US-024: Integrate TokenUsageDisplay into user settings
**Description:** As a user, I want to see my AI usage in my account settings.

**Acceptance Criteria:**
- [ ] Add "AI Usage" section to user settings page
- [ ] Fetch usage from `GET /api/v1/ai/usage/`
- [ ] Render TokenUsageDisplay component
- [ ] Typecheck passes
- [ ] Verify changes work in browser

### US-025: Add academic prompt templates
**Description:** As a developer, I need well-crafted prompts for academic rigor in AI responses.

**Acceptance Criteria:**
- [ ] Create `apps/ai/prompts.py` with prompt templates
- [ ] `SOURCE_SUMMARY_PROMPT`: extracts abstract, findings, methodology, limitations, keywords; handles non-English; flags preprints/retractions
- [ ] `VAULT_INSIGHTS_PROMPT`: identifies themes, gaps, cross-references across sources
- [ ] `QUESTION_ANSWER_PROMPT`: answers with citations, admits uncertainty, academic tone
- [ ] All prompts request JSON-formatted responses
- [ ] Typecheck passes

### US-026: Handle non-English sources and quality flags
**Description:** As a user, I want AI to handle non-English sources and flag potential issues.

**Acceptance Criteria:**
- [ ] Summary prompt includes instruction to detect and note source language
- [ ] Summary response includes `language` field
- [ ] Summary prompt instructs detection of: preprints, retracted papers, non-peer-reviewed
- [ ] Summary response includes `quality_flags[]` (e.g., "preprint", "not_peer_reviewed")
- [ ] AISummaryCard displays quality flags as warning badges
- [ ] Typecheck passes

## Non-Goals

- No vector database or embeddings in initial implementation (design for future migration)
- No real-time streaming of AI responses (full response only)
- No AI-powered citation generation (separate feature)
- No fine-tuning or custom model training
- No image/figure analysis from PDFs
- No automatic source recommendations beyond search suggestions
- No billing or paid tier enforcement (usage tracking only)

## Technical Considerations

- **Anthropic SDK**: Use official `anthropic` Python package for API calls
- **Token Counting**: Use `anthropic.count_tokens()` for accurate tracking
- **Chunking Strategy**: Simple overlap-based chunking now; interface designed for future vector search drop-in
- **Caching**: Use model JSONFields for summary/insights caching (no Redis for AI responses)
- **Error Handling**: All AI endpoints must gracefully handle API failures with user-friendly messages
- **PDF Extraction**: Reuse existing extraction from sources app (per user confirmation)
- **Rate Limit Reset**: Daily reset at midnight UTC
- **Conversation Limit**: FIFO deletion when vault exceeds 10 conversations
