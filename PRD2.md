# PRD: Knowledge Vault RBAC System

## Introduction

Create a secure, collaborative Knowledge Vault system where researchers can create shared repositories of verified sources with granular permission controls. Each vault supports multiple members with distinct roles (Owner, Contributor, Viewer) and comprehensive audit logging for research integrity.

## Goals

- Users can create unlimited vaults with full ownership
- Owners can invite members with appropriate role assignments
- Permission checks prevent unauthorized access to vault operations
- All vault mutations are logged in immutable audit trail
- API supports filtering, pagination, and role-based queries
- Archived vaults enter read-only mode with restore capability

## User Stories

### US-001: Create vaults Django app structure
**Description:** As a developer, I need the Django app scaffolding for vaults so subsequent stories have a place to live.

**Acceptance Criteria:**
- [x] Create `backend/apps/vaults/` directory with `__init__.py`, `apps.py`, `admin.py`
- [x] Create empty `models.py`, `serializers.py`, `permissions.py`, `views.py`, `urls.py`, `signals.py`
- [x] Create `tests/` directory with `__init__.py`, `test_models.py`, `test_views.py`, `test_audit_logs.py`
- [x] Register app in `INSTALLED_APPS` as `apps.vaults`
- [x] Typecheck passes

### US-002: Define RoleChoices enum and role weights
**Description:** As a developer, I need role definitions so membership permissions can reference them.

**Acceptance Criteria:**
- [x] Add `RoleChoices` TextChoices enum: OWNER, CONTRIBUTOR, VIEWER
- [x] Add `ROLE_WEIGHTS` dict: OWNER=3, CONTRIBUTOR=2, VIEWER=1
- [x] Typecheck passes

### US-003: Create Vault model
**Description:** As a developer, I need the Vault model to store knowledge repository data.

**Acceptance Criteria:**
- [x] UUID primary key with `default=uuid.uuid4`
- [x] `name` CharField max_length=255
- [x] `description` TextField blank=True
- [x] `owner` ForeignKey to User with CASCADE, related_name='owned_vaults'
- [x] `is_archived` BooleanField default=False
- [x] `created_at` DateTimeField auto_now_add=True
- [x] `updated_at` DateTimeField auto_now=True
- [x] Meta: ordering=['-created_at']
- [x] Index on ['owner', 'is_archived'] and ['created_at']
- [x] Typecheck passes

### US-004: Create VaultMembership model
**Description:** As a developer, I need the through model for vault members with roles.

**Acceptance Criteria:**
- [x] UUID primary key
- [x] `vault` ForeignKey to Vault with CASCADE
- [x] `user` ForeignKey to User with CASCADE
- [x] `role` CharField with RoleChoices, default CONTRIBUTOR
- [x] `added_at` DateTimeField auto_now_add=True
- [x] `added_by` ForeignKey to User, SET_NULL, null=True, related_name='memberships_created'
- [x] `get_role_weight()` method returns weight from ROLE_WEIGHTS
- [x] unique_together constraint on ['vault', 'user']
- [x] Index on ['vault', 'role'] and ['user']
- [x] Typecheck passes

### US-005: Add members ManyToMany to Vault
**Description:** As a developer, I need the members relationship on Vault using VaultMembership as through model.

**Acceptance Criteria:**
- [x] Add `members` ManyToManyField to User through='VaultMembership', related_name='vaults'
- [x] Typecheck passes

### US-006: Create AuditLog model
**Description:** As a developer, I need audit logging for research integrity tracking.

**Acceptance Criteria:**
- [x] UUID primary key
- [x] `vault` ForeignKey to Vault with CASCADE
- [x] `actor` ForeignKey to User, SET_NULL, null=True
- [x] `action` CharField max_length=100 (e.g., 'vault.created')
- [x] `metadata` JSONField default=dict
- [x] `created_at` DateTimeField auto_now_add=True
- [x] Meta: ordering=['-created_at']
- [x] Index on ['vault', '-created_at'] and ['action']
- [x] Typecheck passes

### US-007: Generate and run initial migration
**Description:** As a developer, I need database tables created for vaults app.

**Acceptance Criteria:**
- [ ] Run `python manage.py makemigrations vaults`
- [ ] Migration file created in `migrations/0001_initial.py`
- [ ] Run `python manage.py migrate`
- [ ] All tables created without errors
- [ ] Typecheck passes

### US-008: Register models in Django admin
**Description:** As a developer, I need admin access to manage vaults during development.

**Acceptance Criteria:**
- [x] Register Vault model with list_display=['name', 'owner', 'is_archived', 'created_at']
- [x] Register VaultMembership with list_display=['vault', 'user', 'role', 'added_at']
- [x] Register AuditLog with list_display=['vault', 'actor', 'action', 'created_at']
- [x] Typecheck passes

### US-009: Create VaultSerializer
**Description:** As a developer, I need serialization for vault API responses.

**Acceptance Criteria:**
- [x] ModelSerializer for Vault
- [x] Fields: id, name, description, owner, owner_username, is_archived, created_at, updated_at, member_count, user_role
- [x] read_only_fields: id, owner, created_at, updated_at
- [x] `owner_username` from source='owner.username'
- [x] `get_member_count()` returns obj.members.count()
- [x] `get_user_role()` returns current user's role from membership or None
- [x] Typecheck passes

### US-010: Create VaultMembershipSerializer
**Description:** As a developer, I need serialization for membership API responses.

**Acceptance Criteria:**
- [x] ModelSerializer for VaultMembership
- [x] Fields: id, user, username, email, role, added_at, added_by
- [x] read_only_fields: id, added_at, added_by
- [x] `username` from source='user.username'
- [x] `email` from source='user.email'
- [x] Typecheck passes

### US-011: Create AuditLogSerializer
**Description:** As a developer, I need serialization for audit log API responses.

**Acceptance Criteria:**
- [x] ModelSerializer for AuditLog
- [x] Fields: id, vault, actor, action, metadata, created_at
- [x] All fields read_only (immutable logs)
- [x] Typecheck passes

### US-012: Create IsVaultOwner permission
**Description:** As a developer, I need owner-only permission for vault management actions.

**Acceptance Criteria:**
- [x] Extends BasePermission
- [x] `has_object_permission` checks if user has OWNER role in vault membership
- [x] Handles both Vault objects and objects with `.vault` attribute
- [x] Returns True only if membership exists with role=OWNER
- [x] Typecheck passes

### US-013: Create IsVaultContributor permission
**Description:** As a developer, I need contributor+ permission for write operations.

**Acceptance Criteria:**
- [x] Extends BasePermission
- [x] `has_object_permission` checks role weight >= CONTRIBUTOR weight (2)
- [x] Returns False if no membership exists
- [x] Typecheck passes

### US-014: Create IsVaultMember permission
**Description:** As a developer, I need member permission for read access.

**Acceptance Criteria:**
- [x] Extends BasePermission
- [x] `has_object_permission` returns True if any membership exists
- [x] Uses `.exists()` for efficiency
- [x] Typecheck passes

### US-015: Create VaultViewSet with CRUD
**Description:** As a developer, I need the main vault API endpoints.

**Acceptance Criteria:**
- [x] ModelViewSet with VaultSerializer
- [x] Default permission: IsAuthenticated
- [x] PageNumberPagination
- [x] filter_backends: DjangoFilterBackend, OrderingFilter
- [x] filterset_fields: ['is_archived']
- [x] ordering_fields: ['created_at', 'name']
- [x] `get_queryset` filters to user's vaults (owned or member)
- [x] `perform_create` sets owner to request.user
- [x] Typecheck passes

### US-016: Add role filter to vault list
**Description:** As a user, I want to filter vaults by my role so I can find owned vs contributed vaults.

**Acceptance Criteria:**
- [x] `get_queryset` reads `role` from query_params
- [x] Filters by `vaultmembership__user=user, vaultmembership__role=role`
- [x] Works with values: OWNER, CONTRIBUTOR, VIEWER
- [x] Typecheck passes

### US-017: Add owner-only permissions to vault mutations
**Description:** As a system, I need to restrict update/delete to owners only.

**Acceptance Criteria:**
- [x] `get_permissions` returns [IsVaultOwner()] for update, partial_update, destroy actions
- [x] Other actions use IsAuthenticated
- [x] Non-owners get 403 Forbidden on PATCH/DELETE
- [x] Typecheck passes

### US-018: Add archive action to VaultViewSet
**Description:** As a vault owner, I want to archive completed vaults for decluttering.

**Acceptance Criteria:**
- [x] @action(detail=True, methods=['post'], permission_classes=[IsVaultOwner])
- [x] Sets vault.is_archived = True and saves
- [x] Returns {'status': 'archived'}
- [x] Typecheck passes

### US-019: Add restore action to VaultViewSet
**Description:** As a vault owner, I want to restore archived vaults.

**Acceptance Criteria:**
- [x] @action(detail=True, methods=['post'], permission_classes=[IsVaultOwner])
- [x] Sets vault.is_archived = False and saves
- [x] Returns {'status': 'restored'}
- [x] Typecheck passes

### US-020: Create VaultMembershipViewSet
**Description:** As a developer, I need member management API endpoints.

**Acceptance Criteria:**
- [x] ModelViewSet with VaultMembershipSerializer
- [x] Default permission: IsAuthenticated
- [x] `get_queryset` filters by vault_pk from URL kwargs
- [x] Typecheck passes

### US-021: Add permissions to VaultMembershipViewSet
**Description:** As a system, I need proper access control for member management.

**Acceptance Criteria:**
- [x] `get_permissions` returns [IsVaultOwner()] for create, update, partial_update, destroy
- [x] List/retrieve uses [IsVaultMember()]
- [x] Typecheck passes

### US-022: Add perform_create to membership viewset
**Description:** As a system, I need to auto-set vault and added_by on member creation.

**Acceptance Criteria:**
- [x] Get vault from kwargs['vault_pk']
- [x] Call serializer.save(vault=vault, added_by=request.user)
- [x] Typecheck passes

### US-023: Create AuditLogViewSet (read-only)
**Description:** As a researcher, I need to view audit history for research integrity.

**Acceptance Criteria:**
- [x] ReadOnlyModelViewSet with AuditLogSerializer
- [x] Permission: IsVaultMember
- [x] `get_queryset` filters by vault_pk from URL
- [x] Ordered by '-created_at'
- [x] Typecheck passes

### US-024: Create vault creation signal for owner membership
**Description:** As a system, I need to auto-create owner membership when vault is created.

**Acceptance Criteria:**
- [x] post_save signal on Vault
- [x] On created=True, create VaultMembership with role=OWNER
- [x] Sets added_by to vault.owner
- [x] Typecheck passes

### US-025: Create vault mutation audit signal
**Description:** As a system, I need to log vault creation and updates.

**Acceptance Criteria:**
- [x] post_save signal on Vault
- [x] Creates AuditLog with action='vault.created' or 'vault.updated'
- [x] Metadata includes name and is_archived
- [x] Actor set to vault.owner
- [x] Typecheck passes

### US-026: Create membership added audit signal
**Description:** As a system, I need to log when members are added.

**Acceptance Criteria:**
- [x] post_save signal on VaultMembership
- [x] On created=True, creates AuditLog with action='membership.added'
- [x] Metadata includes user_id and role
- [x] Actor set to added_by
- [x] Typecheck passes

### US-027: Create role change audit signal
**Description:** As a system, I need to log role changes.

**Acceptance Criteria:**
- [x] pre_save signal on VaultMembership
- [x] If pk exists and role changed, create AuditLog
- [x] Action: 'membership.role_changed'
- [x] Metadata includes user_id, old_role, new_role
- [x] Typecheck passes

### US-028: Create membership removed audit signal
**Description:** As a system, I need to log when members are removed.

**Acceptance Criteria:**
- [x] post_delete signal on VaultMembership
- [x] Creates AuditLog with action='membership.removed'
- [x] Metadata includes user_id
- [x] Typecheck passes

### US-029: Register signals in apps.py ready()
**Description:** As a developer, I need signals connected on app startup.

**Acceptance Criteria:**
- [x] Override ready() in VaultsConfig
- [x] Import signals module to connect handlers
- [x] Typecheck passes

### US-030: Configure URL router for vaults
**Description:** As a developer, I need REST endpoints routed properly.

**Acceptance Criteria:**
- [x] Create DefaultRouter in urls.py
- [x] Register VaultViewSet at 'vaults'
- [x] Export urlpatterns from router.urls
- [x] Typecheck passes

### US-031: Configure nested routes for members and audit-logs
**Description:** As a developer, I need nested endpoints under each vault.

**Acceptance Criteria:**
- [ ] Add path for members: `vaults/<uuid:vault_pk>/members/`
- [ ] Add path for audit-logs: `vaults/<uuid:vault_pk>/audit-logs/`
- [ ] Both use appropriate ViewSets
- [ ] Typecheck passes

### US-032: Include vaults URLs in main config
**Description:** As a developer, I need vaults API accessible at /api/v1/vaults/.

**Acceptance Criteria:**
- [ ] Add to config/urls.py: `path('api/v1/', include('apps.vaults.urls'))`
- [ ] Endpoints accessible at /api/v1/vaults/
- [ ] Typecheck passes

### US-033: Add last owner validation to membership
**Description:** As a system, I need to prevent removing/downgrading the last owner.

**Acceptance Criteria:**
- [ ] Before role change or delete, check if user is last OWNER
- [ ] If last owner, raise ValidationError
- [ ] Returns 400 with message "Vault must have at least one owner"
- [ ] Typecheck passes

### US-034: Add ownership transfer logic
**Description:** As a vault owner, I want to transfer ownership to another member.

**Acceptance Criteria:**
- [ ] When setting role=OWNER on a member, validate they are already a member
- [ ] Previous owner's role automatically set to CONTRIBUTOR
- [ ] Only one OWNER allowed (enforced before save)
- [ ] Typecheck passes

### US-035: Write model unit tests
**Description:** As a developer, I need tests to verify model behavior.

**Acceptance Criteria:**
- [ ] Test Vault creation with required fields
- [ ] Test VaultMembership unique constraint (duplicate user)
- [ ] Test role weight calculation
- [ ] Test AuditLog creation
- [ ] Tests pass with `python manage.py test apps.vaults.tests.test_models`

### US-036: Write vault API tests
**Description:** As a developer, I need tests for vault CRUD operations.

**Acceptance Criteria:**
- [ ] Test vault creation assigns owner membership
- [ ] Test vault list filtering by role and archived
- [ ] Test permission denial for non-owners on update/delete
- [ ] Test archive and restore actions
- [ ] Tests pass with `python manage.py test apps.vaults.tests.test_views`

### US-037: Write membership API tests
**Description:** As a developer, I need tests for member management.

**Acceptance Criteria:**
- [ ] Test add member creates membership
- [ ] Test role update changes membership role
- [ ] Test member removal deletes membership
- [ ] Test last owner deletion returns 400
- [ ] Tests pass

### US-038: Write audit log tests
**Description:** As a developer, I need tests for audit logging.

**Acceptance Criteria:**
- [ ] Test vault.created log on creation
- [ ] Test membership.added log on member add
- [ ] Test membership.role_changed log on role update
- [ ] Test membership.removed log on member delete
- [ ] Tests pass with `python manage.py test apps.vaults.tests.test_audit_logs`

## Non-Goals

- Email invitation flow for non-existent users (requires notification system)
- Bulk member import via CSV
- Vault templates for common research types
- Activity analytics dashboard
- Soft delete with recovery window (hard delete only for MVP)
- WebSocket real-time updates for membership changes
- Full-text search on vault contents

## Technical Considerations

- Use PostgreSQL for UUID primary keys and JSONField
- django-filter already in requirements for filtering
- DRF pagination classes available
- Existing User model in apps.users
- Follow existing project patterns from CLAUDE.md
