---
  Batch 1: Independent Workstreams (Run All 6 Simultaneously)

  1. Backend: Users & Authentication

  Create a PRD for SyncScript's Django backend user authentication system. Features needed:
  - Custom User model extending AbstractUser with profile fields (avatar_url, bio, institution)
  - JWT authentication using djangorestframework-simplejwt (15min access, 7d refresh tokens)
  - Registration endpoint with email verification stub
  - Login/logout/refresh token endpoints
  - Password reset flow endpoints
  - User profile CRUD (GET/PATCH own profile)
  - Rate limiting on auth endpoints using django-ratelimit (5 attempts/minute)

  Tech: Django 4.2+, DRF, PostgreSQL, Redis for rate limit storage
  App location: backend/apps/users/
  Include proper serializers, views, urls, and model migrations.
  Reference CLAUDE.md for project structure.

  2. Backend: Vaults & RBAC Core

  Create a PRD for SyncScript's Knowledge Vault system with role-based access control. Features
  needed:
  - Vault model (name, description, owner FK, created_at, updated_at, is_archived)
  - VaultMembership model for many-to-many with role enum (OWNER/CONTRIBUTOR/VIEWER)
  - Vault CRUD API endpoints with permission checks
  - Member management endpoints (invite, update role, remove member)
  - Custom DRF permissions: IsVaultOwner, IsVaultContributor, IsVaultMember
  - List vaults for current user (owned + member of) with role filtering
  - Vault archive/restore functionality
  - Audit log entries on membership changes

  Tech: Django 4.2+, DRF, PostgreSQL
  App location: backend/apps/vaults/
  Include models, serializers, permissions, views, signals for audit logging.
  Reference CLAUDE.md for project structure.

  3. Backend: Sources & Annotations

  Create a PRD for SyncScript's source and annotation management system. Features needed:
  - Source model (vault FK, url, title, description, source_type enum, metadata JSON, created_by FK)
  - Annotation model (source FK, user FK, content text, page_number, position JSON, created_at)
  - Source CRUD with vault permission inheritance
  - Annotation CRUD with user ownership checks
  - Bulk source import endpoint (accept array of URLs)
  - Source metadata auto-extraction stub (title from URL)
  - Filter sources by vault, type, date range
  - Annotation threading (parent_id for replies)
  - Audit log entries for all source/annotation changes

  Tech: Django 4.2+, DRF, PostgreSQL
  App location: backend/apps/sources/ and backend/apps/annotations/
  Include models, serializers, views, filters using django-filter.
  Reference CLAUDE.md for project structure.

  4. Frontend: Project Setup & Design System

  Create a PRD for SyncScript's Next.js 14 frontend foundation with Bitcoin DeFi design system.
  Features needed:
  - Next.js 14 App Router project scaffold with TypeScript
  - Tailwind CSS config with design tokens from DESIGN_RULES.md (colors, fonts, shadows)
  - Google Fonts setup (Space Grotesk, Inter, JetBrains Mono)
  - ShadCN UI installation and customization to match Bitcoin DeFi aesthetic
  - Base components using CVA: Button (primary/outline/ghost), Card, Input, Badge
  - Global CSS with grid pattern, glow effects, glass morphism utilities
  - Layout component with responsive container (max-w-7xl)
  - Theme provider (dark mode only)
  - Axios API client setup with interceptors for JWT
  - React Query provider setup
  - Zustand store scaffold for auth state

  Location: frontend/
  Reference DESIGN_RULES.md for all styling decisions.
  Reference CLAUDE.md for folder structure.

  5. Backend: Real-time WebSockets

  Create a PRD for SyncScript's real-time collaboration infrastructure. Features needed:
  - Django Channels setup with Daphne ASGI server
  - Redis channel layer configuration
  - VaultConsumer WebSocket consumer for vault rooms
  - JWT authentication middleware for WebSocket connections
  - Room management (join vault room, leave, broadcast)
  - Event types: source.created, source.updated, source.deleted, annotation.created, member.added
  - Signal handlers to broadcast changes to vault rooms
  - Connection tracking (who's currently viewing a vault)
  - Presence indicators data structure

  Tech: Django Channels, channels-redis, Redis
  App location: backend/apps/vaults/consumers.py, routing.py
  Include ASGI config, channel layer settings, consumer classes.
  Reference CLAUDE.md for project structure.

  6. Backend: File Storage & Cloud Integration

  Create a PRD for SyncScript's cloud file storage system. Features needed:
  - django-storages configuration for S3-compatible storage (Cloudflare R2)
  - PDFUpload model (vault FK, source FK optional, file field, uploaded_by, file_size, mime_type)
  - Presigned URL generation for secure uploads (PUT) and downloads (GET)
  - Multipart upload initiation endpoint for large files
  - Upload completion webhook/callback endpoint
  - File validation (PDF only, max 50MB)
  - Celery task for post-upload processing stub
  - Storage usage tracking per vault
  - File deletion with soft-delete

  Tech: Django, django-storages, boto3, Celery
  App location: backend/apps/sources/storage.py, backend/apps/sources/tasks.py
  Include presigned URL views, storage backend config, Celery task stubs.
  Reference CLAUDE.md for project structure.

  ---
  Batch 2: Dependent Workstreams (Run After Batch 1 Completes)

  7. Frontend: Authentication & User Flows

  Create a PRD for SyncScript's frontend authentication pages and user flows. Features needed:
  - Login page with email/password form (Bitcoin DeFi styled inputs)
  - Registration page with validation
  - Forgot password / reset password pages
  - User profile page with edit capability
  - Auth context/hook using Zustand store
  - Protected route wrapper component
  - JWT token management (httpOnly cookie handling via API)
  - Auto-refresh token logic in axios interceptor
  - Logout functionality with token cleanup
  - Loading states and error handling with toast notifications

  Depends on: Backend Users & Auth API, Frontend Design System
  Location: frontend/src/app/(auth)/, frontend/src/hooks/useAuth.ts
  Use ShadCN components customized per DESIGN_RULES.md.
  All forms must have gradient buttons, bottom-border inputs, glass card containers.

  8. Frontend: Vaults Management UI

  Create a PRD for SyncScript's vault management interface. Features needed:
  - Vaults listing page with grid of vault cards (owned vs member badges)
  - Create vault modal/dialog with form
  - Vault detail page layout with tabs (Sources, Members, Settings)
  - Members management panel (invite by email, role dropdown, remove button)
  - Role-based UI rendering (show/hide edit buttons based on user role)
  - Vault settings page (rename, archive, delete for owners)
  - Empty states for no vaults / no sources
  - Search/filter vaults functionality
  - Responsive grid layout per DESIGN_RULES.md

  Depends on: Backend Vaults API, Frontend Design System
  Location: frontend/src/app/vaults/, frontend/src/components/features/vaults/
  Use React Query for data fetching, Zustand for UI state.
  Cards must have hover lift effect, orange glow on interaction.

  9. Frontend: Sources & Annotations UI

  Create a PRD for SyncScript's source and annotation management interface. Features needed:
  - Sources list view within vault (card grid or table toggle)
  - Add source modal (URL input with metadata preview)
  - Source detail page with PDF viewer integration stub
  - Annotation sidebar panel (list of annotations for current source)
  - Add annotation form (text input, optional page number)
  - Annotation thread view for replies
  - Bulk import sources modal (paste multiple URLs)
  - Source type badges with icons
  - Filter bar (by type, date, contributor)
  - Delete confirmation dialogs

  Depends on: Backend Sources/Annotations API, Frontend Design System, Vaults UI
  Location: frontend/src/app/vaults/[id]/sources/, frontend/src/components/features/sources/
  Annotations should have glass morphism cards, muted text for metadata.

  10. Integration: Real-time & Notifications

  Create a PRD for SyncScript's real-time updates and notification system integration. Features
  needed:
  - WebSocket client hook (useVaultSocket) for vault rooms
  - Real-time source/annotation updates in UI (optimistic + server reconciliation)
  - Presence indicators showing active collaborators in vault
  - Toast notifications for vault events (new source added, member joined)
  - Pusher integration for browser push notifications
  - Notification preferences panel in user settings
  - Unread notification badge in header
  - Notification dropdown/panel with history
  - Sound toggle for notifications
  - Connection status indicator (connected/reconnecting)

  Depends on: Backend WebSocket system, Backend Vaults API, All Frontend pages
  Location: frontend/src/hooks/useVaultSocket.ts, frontend/src/components/features/notifications/
  Presence dots should use animate-ping effect per DESIGN_RULES.md.

  ---
  Execution Order

  ┌─────────────────────────────────────────────────────────────────┐
  │                        BATCH 1 (Parallel)                       │
  ├─────────────┬─────────────┬─────────────┬─────────────┬─────────┤
  │  1. Users   │  2. Vaults  │  3. Sources │ 4. Frontend │ 5. WS   │
  │  & Auth     │  & RBAC     │  & Annot.   │ Design Sys  │ Realtime│
  │  (Backend)  │  (Backend)  │  (Backend)  │ (Frontend)  │ (Backend│
  ├─────────────┴─────────────┴─────────────┴─────────────┴─────────┤
  │                              + 6. File Storage (Backend)        │
  └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                        BATCH 2 (Parallel)                       │
  ├─────────────────┬─────────────────┬─────────────────┬───────────┤
  │  7. Auth UI     │  8. Vaults UI   │  9. Sources UI  │ 10. RT    │
  │  (Frontend)     │  (Frontend)     │  (Frontend)     │ Notifs    │
  │  needs: 1,4     │  needs: 2,4     │  needs: 3,4,8   │ needs:5,* │
  └─────────────────┴─────────────────┴─────────────────┴───────────┘
---

# PRD Summaries

## PRD 1: Backend Users & Authentication
**Status:** Complete (40/40 user stories)

**Overview:** Secure, production-ready authentication system for SyncScript using Django REST Framework with JWT-based auth, email verification, password reset, and rate limiting.

**Key Features:**
- Custom User model with email as primary identifier (avatar_url, bio, institution fields)
- JWT tokens: 15min access, 7-day refresh with rotation and blacklisting
- Email verification flow with 24-hour tokens
- Password reset via email (1-hour tokens)
- User profile CRUD (GET/PATCH)
- Redis-backed rate limiting: 5/min for auth endpoints, 3/hour for password reset
- Comprehensive test coverage (model, serializer, auth flow, profile, rate limiting)

**API Endpoints:**
| Endpoint | Method | Rate Limit |
|----------|--------|------------|
| /api/v1/auth/register/ | POST | 5/min |
| /api/v1/auth/verify-email/ | POST | 10/min |
| /api/v1/auth/login/ | POST | 5/min |
| /api/v1/auth/logout/ | POST | - |
| /api/v1/auth/refresh/ | POST | 20/min |
| /api/v1/auth/password-reset/ | POST | 3/hour |
| /api/v1/users/profile/ | GET/PATCH | - |

---

## PRD 2: Backend Vaults & RBAC
**Status:** Mostly Complete (34/38 user stories - tests pending)

**Overview:** Knowledge Vault system with role-based access control enabling researchers to create shared repositories with granular permission controls and audit logging.

**Key Features:**
- Vault model: name, description, owner, is_archived, timestamps
- VaultMembership through model with roles: OWNER (3), CONTRIBUTOR (2), VIEWER (1)
- Custom permissions: IsVaultOwner, IsVaultContributor, IsVaultMember
- Archive/restore functionality for vaults
- Member management: invite, update role, remove (prevents last owner removal)
- Ownership transfer logic
- Comprehensive audit logging via signals (vault.created, membership.added, role_changed, etc.)

**API Endpoints:**
- GET/POST /api/v1/vaults/ - List/create vaults
- GET/PATCH/DELETE /api/v1/vaults/{id}/ - Vault CRUD
- POST /api/v1/vaults/{id}/archive/ - Archive vault
- POST /api/v1/vaults/{id}/restore/ - Restore vault
- GET/POST /api/v1/vaults/{id}/members/ - Member management
- GET /api/v1/vaults/{id}/audit-logs/ - Audit history

---

## PRD 3: Backend Sources & Annotations
**Status:** Mostly Complete (36/43 user stories - audit signals pending)

**Overview:** Source and annotation management system for collaborative research with URL metadata extraction, threaded annotations, and comprehensive filtering.

**Key Features:**
- Source model: vault FK, URL, title, description, source_type (URL/PDF/BOOK/JOURNAL/DATASET), metadata JSON
- Annotation model: source FK, user FK, content, page_number, position JSON, parent (2-level threading max)
- newspaper3k integration for auto-extracting metadata (title, authors, abstract)
- Bulk import up to 50 URLs with validation and duplicate detection
- Soft-delete for sources with restore capability
- django-filter integration for vault, type, date range, tags, and search filters
- IsAuthorOrReadOnly permission for annotations

**API Endpoints:**
- GET/POST /api/v1/sources/ - Source CRUD
- GET/POST /api/v1/vaults/{id}/sources/ - Nested source creation
- POST /api/v1/sources/bulk_import/ - Bulk import URLs
- POST /api/v1/sources/{id}/restore/ - Restore soft-deleted source
- GET/POST /api/v1/annotations/ - Annotation CRUD
- GET/POST /api/v1/sources/{id}/annotations/ - Nested annotation endpoints

---

## PRD 4: Frontend Project Setup & Design System
**Status:** Complete (10/10 user stories)

**Overview:** Next.js 16 App Router foundation with Bitcoin DeFi-inspired design system, component library, and API/state management infrastructure.

**Key Features:**
- Next.js 16 with TypeScript strict mode
- Tailwind CSS v4 with design tokens (background #030304, primary #F7931A, accent #FFD600)
- Google Fonts: Space Grotesk (headings), Inter (body), JetBrains Mono (code)
- ShadCN UI with Radix primitives customized for Bitcoin DeFi aesthetic
- Core components: Button (primary/outline/ghost), Card, Input, Badge
- Glass morphism utilities, grid pattern backgrounds, glow effects
- Axios API client with JWT auto-refresh interceptors
- Zustand auth store with localStorage persistence
- React Query provider with sensible defaults
- ESLint 10 + Prettier configuration

---

## PRD 5: Backend Real-time WebSockets
**Status:** Complete (28/28 user stories)

**Overview:** Real-time collaboration infrastructure using Django Channels and Redis for live updates, presence tracking, and event broadcasting.

**Key Features:**
- Django Channels with Daphne ASGI server
- Redis channel layer (1500 capacity, 10s expiry)
- JWT authentication middleware for WebSocket connections
- VaultConsumer for vault room management
- Presence tracking with Redis sorted sets (active/idle status)
- Event types: source.created/updated/deleted, annotation.created, member.added, presence.update
- Event buffering in Redis (last 100 events, 1-hour TTL)
- Replay request handler for missed events after reconnection
- 4-layer rate limiting: connection limit per user (5), room limit (100), message throttling (60/min), heartbeat timeout (5min)
- Celery tasks for async broadcasting

**WebSocket Endpoint:** ws://localhost:8000/ws/vault/{id}/?token={jwt}

---

## PRD 6: Backend File Storage & Cloud Integration
**Status:** Complete (26/26 user stories)

**Overview:** Cloud file storage using Cloudflare R2 (S3-compatible) for secure PDF uploads, downloads, metadata extraction, and storage tracking.

**Key Features:**
- PDFUpload model: vault FK, file, original_filename, file_size, mime_type, processing_status
- VaultStorageUsage model for cached storage metrics per vault
- django-storages with boto3 for S3-compatible storage
- Presigned URL generation (1hr upload, 15min download)
- Strict PDF validation (MIME, magic number, structure, 50MB max)
- Multipart upload support for large files
- Celery task for post-upload processing: metadata extraction (pypdf), thumbnail generation (pdf2image)
- Soft-delete with 30-day retention
- Cleanup tasks for deleted PDFs and orphaned multipart uploads
- WebSocket notifications for upload/delete events
- Rate limiting: 10/min upload-url, 30/min download-url

**API Endpoints:**
- POST /api/v1/sources/pdfs/upload-url/ - Get presigned upload URL
- POST /api/v1/sources/pdfs/{id}/complete/ - Upload completion callback
- GET /api/v1/sources/pdfs/{id}/download-url/ - Get presigned download URL
- POST /api/v1/sources/pdfs/multipart-upload/initiate/ - Start multipart upload
- POST /api/v1/sources/pdfs/multipart-upload/{id}/complete/ - Complete multipart upload
- DELETE /api/v1/sources/pdfs/{id}/ - Soft-delete PDF
- GET /api/v1/vaults/{id}/pdfs/ - List vault PDFs

---

## PRD 7: Frontend Authentication & User Flows
**Status:** Complete (22/22 user stories)

**Overview:** Complete frontend authentication system with login, register, password reset, profile management, and protected routes.

**Key Features:**
- Zustand auth store with persist middleware
- Axios interceptors for auto token refresh
- useAuth hook: login, register, logout, refreshUser
- AuthProvider for session hydration on app load
- Bitcoin DeFi styled components: FormInput, GradientButton, GlassCard
- Auth layout with centered glass cards
- Login page with validation and remember-me
- Registration with password strength indicator
- Forgot/reset password flow
- ProtectedRoute wrapper with returnUrl support
- Toast notification system (Radix Toast)
- Profile page with tabs: Profile info + Security (password change)
- User dropdown with logout in header

---

## PRD 8: Frontend Vaults Management UI
**Status:** Complete (22/22 user stories - browser verification pending)

**Overview:** Vault management interface with responsive grid listing, vault detail pages, member management, and role-based UI rendering.

**Key Features:**
- TypeScript types and API client for vaults
- React Query hooks: useVaults, useVault, useCreateVault, useUpdateVault, useDeleteVault
- Vault members hooks: useVaultMembers, useAddMember, useInviteMember, useUpdateRole, useRemoveMember
- VaultCard component with role badges (Owner/Contributor/Viewer)
- Responsive grid: 1 col mobile, 2 tablet, 3 desktop
- Create vault modal with glass morphism
- Vault detail page with tabs: Sources, Members, Settings
- Member management: add existing users, invite by email, change roles, remove
- Settings: rename, archive, delete with type-to-confirm
- useVaultPermissions hook for role-based UI rendering
- Loading skeletons and empty states
- Server-side search with debounce

---

## PRD 9: Frontend Sources & Annotations UI
**Status:** Complete (32/32 user stories)

**Overview:** Source and annotation management interface with grid/table views, PDF viewer, threaded annotations, and real-time collaboration.

**Key Features:**
- SourceCard and SourceTableRow with SourceTypeBadge
- View toggle (grid/table) with localStorage persistence
- SourcesFilterBar: type, date, contributor filters with URL params
- AddSourceModal with metadata preview
- BulkImportModal for multiple URLs
- react-pdf integration for PDF viewing with zoom/navigation controls
- AnnotationSidebar with glass morphism cards
- AnnotationCard with reply threading (single level)
- AddAnnotationForm and AddReplyForm
- React Query hooks: useSourcesQuery, useAnnotationsQuery
- Mutation hooks with optimistic updates
- WebSocket hooks: useSourcesWebSocket, useAnnotationsWebSocket
- Keyboard shortcuts: n (add), b (bulk), g (grid), t (table), ? (help)
- Loading skeletons for sources and annotations

---

## PRD 10: Frontend Real-time & Notifications
**Status:** Complete (18/18 user stories - browser verification pending)

**Overview:** Real-time updates and notification system integration with WebSocket connection management, presence indicators, and push notifications.

**Key Features:**
- useVaultSocket hook with auto-reconnect (exponential backoff)
- ConnectionStatus indicator (green/yellow/red dot)
- useRealtimeUpdates hook for optimistic updates with server reconciliation
- Real-time source and annotation updates via WebSocket
- usePresence hook with 30s heartbeat
- PresenceIndicator with animate-ping effect for active members
- Toast notifications for vault events
- UnreadBadge in header with pulse animation
- NotificationPanel dropdown with mark-as-read
- NotificationPreferences: enable/disable, push, sound toggles
- Pusher integration for browser push notifications
- Sound notifications with global toggle
- WebSocket reconnection with state recovery
