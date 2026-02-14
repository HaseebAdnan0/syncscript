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