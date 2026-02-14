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
- [x] Create `apps/ai/` Django app with models.py, views.py, urls.py, serializers.py
- [x] `AIUsageLog` model: user (FK), request_type (enum: summary/insights/question), tokens_used (int), created_at
- [x] `ChatConversation` model: vault (FK), user (FK), created_at, updated_at
- [x] `ChatMessage` model: conversation (FK), role (enum: user/assistant), content (text), sources_cited (JSONField), created_at
- [x] Add `ai_summary` JSONField to Source model (nullable)
- [x] Add `ai_insights_cache` JSONField + `ai_insights_updated_at` to Vault model (nullable)
- [x] Generate and run migrations
- [x] Register app in INSTALLED_APPS
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
- [x] Create `apps/ai/decorators.py` with `@ai_rate_limit` decorator
- [x] Decorator checks `get_remaining_requests(user)` before allowing request
- [x] Returns 429 with `{"error": "AI request limit reached", "resets_at": "<timestamp>", "cached_available": true}` when exceeded
- [x] Decorator is reusable across all AI views
- [x] Typecheck passes

### US-004: Implement Claude client service
**Description:** As a developer, I need a wrapper for Claude API calls with consistent error handling.

**Acceptance Criteria:**
- [x] Create `apps/ai/services/claude_client.py`
- [x] `ClaudeClient` class with `__init__` reading `ANTHROPIC_API_KEY` from settings
- [x] `summarize(text, source_type)` method with academic summarization prompt
- [x] `analyze_sources(sources_data)` method for vault insights
- [x] `answer_question(question, context_chunks)` method for Q&A
- [x] All methods return structured dict matching expected schema
- [x] Graceful error handling: return `{"error": "..."}` on API failure
- [x] Token counting using `anthropic` SDK's token counter
- [x] Typecheck passes

### US-005: Add source text chunking utility
**Description:** As a developer, I need to chunk source text intelligently so it fits in Claude's context window for Q&A.

**Acceptance Criteria:**
- [x] Create `apps/ai/services/chunking.py`
- [x] `chunk_text(text, max_tokens=2000, overlap=200)` splits text into overlapping chunks
- [x] `get_relevant_chunks(question, chunks, max_chunks=5)` returns most relevant chunks (keyword matching for now, vector-ready interface)
- [x] Handles empty text gracefully
- [x] Typecheck passes

### US-006: Implement source summarization endpoint
**Description:** As a user, I want to get an AI-generated summary of any source so I can quickly understand its contents.

**Acceptance Criteria:**
- [x] `POST /api/v1/sources/{id}/summarize/` endpoint
- [x] Requires authentication and source read permission
- [x] If `source.ai_summary` exists and `regenerate=false`, return cached summary
- [x] If `regenerate=true` or no cache: extract text (use existing PDF extraction or fetch URL content)
- [x] Send to Claude with academic summarization prompt
- [x] Response schema: `{abstract, key_findings[], methodology, limitations, keywords[], generated_at}`
- [x] Save to `source.ai_summary` JSONField
- [x] Log token usage via usage service
- [x] Apply `@ai_rate_limit` decorator
- [x] Typecheck passes

### US-007: Implement vault insights endpoint
**Description:** As a user, I want AI-generated insights about my vault so I can see themes and gaps across all sources.

**Acceptance Criteria:**
- [x] `GET /api/v1/vaults/{id}/insights/` endpoint
- [x] Requires authentication and vault read permission
- [x] Return cached insights if `ai_insights_updated_at` < 24 hours old
- [x] Gather all source summaries (or titles/abstracts if no summary)
- [x] Send to Claude for thematic analysis
- [x] Response: `{themes[], research_gaps[], cross_references[], suggested_searches[], generated_at}`
- [x] Cache in vault's `ai_insights_cache` field
- [x] Apply `@ai_rate_limit` decorator
- [x] Typecheck passes

### US-008: Add cache invalidation for vault insights
**Description:** As a developer, I need to invalidate vault insights cache when sources change so insights stay fresh.

**Acceptance Criteria:**
- [x] Django signal on Source post_save and post_delete
- [x] If source's vault has `ai_insights_cache`, set `ai_insights_updated_at` to null
- [x] Signal handler in `apps/ai/signals.py`
- [x] Connect signals in `apps/ai/apps.py` ready()
- [x] Typecheck passes

### US-009: Implement question answering endpoint
**Description:** As a user, I want to ask questions about my vault contents and get cited answers.

**Acceptance Criteria:**
- [x] `POST /api/v1/vaults/{id}/ask/` endpoint with `{question, conversation_id?}` body
- [x] Requires authentication and vault read permission
- [x] Gather text from all sources in vault, chunk them
- [x] Use `get_relevant_chunks()` to find relevant context
- [x] Send question + context to Claude with citation instructions
- [x] Response: `{answer, citations[{source_id, source_title, excerpt}], conversation_id}`
- [x] Apply `@ai_rate_limit` decorator
- [x] Log token usage
- [x] Typecheck passes

### US-010: Implement chat history persistence
**Description:** As a user, I want my vault Q&A conversations saved so I can continue where I left off.

**Acceptance Criteria:**
- [x] If `conversation_id` provided in ask request, append to existing conversation
- [x] If not provided, create new ChatConversation
- [x] Save user message and assistant response as ChatMessage records
- [x] Store `sources_cited` in assistant message's JSONField
- [x] Limit to 10 conversations per vault (delete oldest on overflow)
- [x] `GET /api/v1/vaults/{id}/conversations/` lists conversations with preview
- [x] `GET /api/v1/vaults/{id}/conversations/{conv_id}/` returns full message history
- [x] Typecheck passes

### US-011: Add AI URL routes
**Description:** As a developer, I need to wire up all AI endpoints to the URL router.

**Acceptance Criteria:**
- [x] Create `apps/ai/urls.py` with all AI routes
- [x] Include in main `config/urls.py` under `/api/v1/`
- [x] Routes: sources summarize, vault insights, vault ask, vault conversations
- [x] Typecheck passes

### US-012: Create AISummaryCard component
**Description:** As a user, I want to see an expandable AI summary card on source pages.

**Acceptance Criteria:**
- [x] Create `components/features/ai/AISummaryCard.tsx`
- [x] Props: `sourceId`, `summary` (nullable), `onRegenerate`
- [x] Collapsed state shows "AI Summary" header with expand chevron
- [x] Expanded state shows collapsible sections: Key Findings, Methodology, Limitations, Keywords
- [x] "Generate Summary" button if no summary exists
- [x] "Regenerate" button in header when summary exists
- [x] Follows Bitcoin DeFi design (glass card, orange accents)
- [x] Typecheck passes

### US-013: Create AI loading skeleton
**Description:** As a user, I want to see a loading state while AI processes my request.

**Acceptance Criteria:**
- [x] Create `components/features/ai/AILoadingSkeleton.tsx`
- [x] Animated skeleton with "Analyzing..." text
- [x] Pulsing orange accent animation
- [x] Variants: `summary`, `insights`, `chat`
- [x] Typecheck passes

### US-014: Integrate AISummaryCard into source detail page
**Description:** As a user, I want to see AI summaries on the source detail page.

**Acceptance Criteria:**
- [x] Add AISummaryCard to source detail page layout
- [x] Fetch summary from source data (already in API response)
- [x] Wire "Generate" button to `POST /sources/{id}/summarize/`
- [x] Wire "Regenerate" button with `regenerate=true`
- [x] Show AILoadingSkeleton while request pending
- [x] Handle rate limit error: show toast with "Limit reached" message
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-015: Create ResearchInsightsPanel component
**Description:** As a user, I want a panel showing AI insights about my vault's research themes.

**Acceptance Criteria:**
- [x] Create `components/features/ai/ResearchInsightsPanel.tsx`
- [x] Props: `vaultId`, `insights` (nullable), `onRefresh`
- [x] Sections: Themes (tag cloud), Research Gaps (list), Cross-References (list), Suggested Searches
- [x] "Generate Insights" button if none exist
- [x] "Refresh" button with last-updated timestamp
- [x] Empty state for vaults with < 2 sources
- [x] Typecheck passes

### US-016: Create ThemeCloud component
**Description:** As a user, I want to visualize research themes as a tag cloud.

**Acceptance Criteria:**
- [x] Create `components/features/ai/ThemeCloud.tsx`
- [x] Props: `themes[{name, weight, source_count}]`
- [x] Render as weighted tag cloud (larger = more common)
- [x] Orange gradient coloring based on weight
- [x] Hover shows source count tooltip
- [x] Clickable tags (onClick prop for future filtering)
- [x] Typecheck passes

### US-017: Integrate ResearchInsightsPanel into vault dashboard
**Description:** As a user, I want to see research insights on my vault dashboard.

**Acceptance Criteria:**
- [x] Add "Insights" tab to vault dashboard tabs
- [x] Fetch insights from `GET /vaults/{id}/insights/`
- [x] Show ResearchInsightsPanel with fetched data
- [x] Show AILoadingSkeleton while loading
- [x] Handle rate limit: show cached insights with "Using cached data" badge
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-018: Create AskAIChat component
**Description:** As a user, I want a chat interface to ask questions about my vault.

**Acceptance Criteria:**
- [x] Create `components/features/ai/AskAIChat.tsx`
- [x] Props: `vaultId`, `conversationId?`, `onNewConversation`
- [x] Input field with send button at bottom
- [x] Message list showing user questions and AI responses
- [x] AI responses show inline citations as clickable chips
- [x] Auto-scroll to latest message
- [x] Typecheck passes

### US-019: Create ChatMessage component
**Description:** As a user, I want nicely formatted chat messages with citations.

**Acceptance Criteria:**
- [x] Create `components/features/ai/ChatMessage.tsx`
- [x] Props: `role`, `content`, `citations[]`, `timestamp`
- [x] User messages: right-aligned, subtle background
- [x] Assistant messages: left-aligned, glass card style
- [x] Citations rendered as orange pill badges linking to source
- [x] Typecheck passes

### US-020: Create ChatHistory sidebar
**Description:** As a user, I want to see and switch between my past conversations.

**Acceptance Criteria:**
- [x] Create `components/features/ai/ChatHistory.tsx`
- [x] Props: `vaultId`, `conversations[]`, `activeId`, `onSelect`, `onNewChat`
- [x] List of conversation previews (first message truncated)
- [x] Active conversation highlighted
- [x] "New Chat" button at top
- [x] Shows relative timestamps
- [x] Typecheck passes

### US-021: Integrate AskAI chat into vault sidebar
**Description:** As a user, I want to access the AI chat from my vault view.

**Acceptance Criteria:**
- [x] Add "Ask AI" collapsible section to vault sidebar
- [x] Fetch conversation list from `GET /vaults/{id}/conversations/`
- [x] Load selected conversation messages
- [x] Wire send to `POST /vaults/{id}/ask/`
- [x] Update conversation list on new message
- [x] Show loading skeleton while AI responds
- [x] Handle rate limit: show message with retry time
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-022: Create TokenUsageDisplay component
**Description:** As a user, I want to see my AI usage stats in settings.

**Acceptance Criteria:**
- [x] Create `components/features/ai/TokenUsageDisplay.tsx`
- [x] Props: `usage{requests_today, requests_limit, tokens_today, resets_at}`
- [x] Progress bar showing requests used / limit
- [x] "Resets in X hours" countdown
- [x] Token count display (informational)
- [x] Warning state when > 80% used
- [x] Typecheck passes

### US-023: Add AI usage endpoint
**Description:** As a user, I need an endpoint to fetch my current AI usage stats.

**Acceptance Criteria:**
- [x] `GET /api/v1/ai/usage/` endpoint
- [x] Returns `{requests_today, requests_limit, tokens_today, resets_at}`
- [x] Requires authentication
- [x] Typecheck passes

### US-024: Integrate TokenUsageDisplay into user settings
**Description:** As a user, I want to see my AI usage in my account settings.

**Acceptance Criteria:**
- [x] Add "AI Usage" section to user settings page
- [x] Fetch usage from `GET /api/v1/ai/usage/`
- [x] Render TokenUsageDisplay component
- [x] Typecheck passes
- [x] Verify changes work in browser

### US-025: Add academic prompt templates
**Description:** As a developer, I need well-crafted prompts for academic rigor in AI responses.

**Acceptance Criteria:**
- [x] Create `apps/ai/prompts.py` with prompt templates
- [x] `SOURCE_SUMMARY_PROMPT`: extracts abstract, findings, methodology, limitations, keywords; handles non-English; flags preprints/retractions
- [x] `VAULT_INSIGHTS_PROMPT`: identifies themes, gaps, cross-references across sources
- [x] `QUESTION_ANSWER_PROMPT`: answers with citations, admits uncertainty, academic tone
- [x] All prompts request JSON-formatted responses
- [x] Typecheck passes

### US-026: Handle non-English sources and quality flags
**Description:** As a user, I want AI to handle non-English sources and flag potential issues.

**Acceptance Criteria:**
- [x] Summary prompt includes instruction to detect and note source language
- [x] Summary response includes `language` field
- [x] Summary prompt instructs detection of: preprints, retracted papers, non-peer-reviewed
- [x] Summary response includes `quality_flags[]` (e.g., "preprint", "not_peer_reviewed")
- [x] AISummaryCard displays quality flags as warning badges
- [x] Typecheck passes

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
