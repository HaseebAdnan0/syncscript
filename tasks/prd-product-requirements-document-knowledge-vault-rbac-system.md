# Product Requirements Document: Knowledge Vault RBAC System

## 1. Overview

**Feature Name:** Knowledge Vault with Role-Based Access Control  
**Project:** SyncScript - Collaborative Research & Citation Engine  
**Target Release:** Hackfest x Datathon MVP  
**Document Version:** 1.0  
**Last Updated:** 2026-02-14  

### 1.1 Purpose
Create a secure, collaborative Knowledge Vault system where researchers can create shared repositories of verified sources with granular permission controls. Each vault supports multiple members with distinct roles (Owner, Contributor, Viewer) and comprehensive audit logging for research integrity.

### 1.2 Success Criteria
- ✅ Users can create unlimited vaults with full ownership
- ✅ Owners can invite members with appropriate role assignments
- ✅ Permission checks prevent unauthorized access to vault operations
- ✅ All vault mutations are logged in immutable audit trail
- ✅ API supports filtering, pagination, and role-based queries
- ✅ Archived vaults enter read-only mode with restore capability

---

## 2. User Stories

### US-1: Vault Creation
**As a** researcher  
**I want to** create a new Knowledge Vault with a name and description  
**So that** I can organize sources around a specific research topic  

**Acceptance Criteria:**
- User can create vault via POST `/api/v1/vaults/`
- Required fields: `name` (max 255 chars)
- Optional fields: `description` (text)
- Creator is automatically assigned OWNER role
- Response includes vault ID, timestamps, and creator info
- Audit log entry created: `vault.created`

### US-2: Vault Ownership Transfer
**As a** vault owner  
**I want to** transfer ownership to another existing member  
**So that** I can delegate vault management responsibilities  

**Acceptance Criteria:**
- Owner can PATCH `/api/v1/vaults/{id}/members/{user_id}/` with `role: "OWNER"`
- System validates target user is already a vault member
- Previous owner's role automatically downgraded to CONTRIBUTOR
- Only one OWNER allowed per vault (enforced by signal)
- Audit log entry created: `membership.role_changed`

### US-3: Member Invitation (Hybrid Flow)
**As a** vault owner  
**I want to** add existing platform users directly or invite external users via email  
**So that** I can quickly onboard collaborators  

**Acceptance Criteria:**
- POST `/api/v1/vaults/{id}/members/` with `user_id` or `email`
- If `user_id` provided: immediate membership creation (no confirmation)
- If `email` provided and user exists: immediate membership creation + notification
- If `email` provided and user not found: create pending invitation (requires notification system integration - future phase)
- Default role: CONTRIBUTOR (can override with `role` param)
- Audit log entry created: `membership.added`

### US-4: Role Management
**As a** vault owner  
**I want to** update member roles between OWNER/CONTRIBUTOR/VIEWER  
**So that** I can adjust permissions as project needs evolve  

**Acceptance Criteria:**
- PATCH `/api/v1/vaults/{id}/members/{user_id}/` with new `role`
- Only owners can change roles
- Cannot downgrade last owner (validation error)
- Role weights enforced: OWNER=3, CONTRIBUTOR=2, VIEWER=1
- Audit log entry created: `membership.role_changed`

### US-5: Member Removal
**As a** vault owner  
**I want to** remove members from the vault  
**So that** I can revoke access when collaborations end  

**Acceptance Criteria:**
- DELETE `/api/v1/vaults/{id}/members/{user_id}/`
- Only owners can remove members
- Cannot remove last owner (validation error)
- Member loses all vault access immediately
- Audit log entry created: `membership.removed`

### US-6: Vault Listing with Role Filtering
**As a** researcher  
**I want to** see all vaults I own or am a member of, filtered by my role  
**So that** I can quickly navigate to relevant projects  

**Acceptance Criteria:**
- GET `/api/v1/vaults/?role=OWNER&is_archived=false`
- Pagination: `page` and `page_size` (default 20)
- Filters: `role` (OWNER/CONTRIBUTOR/VIEWER), `is_archived` (true/false)
- Response includes vault metadata + user's role + member count
- Excludes vaults where user has no membership

### US-7: Vault Archive & Restore
**As a** vault owner  
**I want to** archive completed vaults and restore them later  
**So that** I can declutter active projects without losing data  

**Acceptance Criteria:**
- POST `/api/v1/vaults/{id}/archive/` sets `is_archived=True`
- Archived vaults enter read-only mode:
  - All members can view vault/sources/annotations
  - No create/update/delete operations allowed (except restore)
- POST `/api/v1/vaults/{id}/restore/` sets `is_archived=False`
- Only owners can archive/restore
- Audit log entries: `vault.archived`, `vault.restored`

### US-8: Permission-Based Access Control
**As a** system  
**I want to** enforce role-based permissions on all vault operations  
**So that** users can only perform actions appropriate to their role  

**Acceptance Criteria:**
- Custom DRF permissions implemented:
  - `IsVaultOwner`: Checks user has OWNER role (weight=3)
  - `IsVaultContributor`: Checks user has CONTRIBUTOR or higher (weight≥2)
  - `IsVaultMember`: Checks user has any vault membership (weight≥1)
- Permissions applied to views:
  - Create vault: Authenticated
  - Update/Delete/Archive vault: IsVaultOwner
  - Add/Remove members: IsVaultOwner
  - View vault: IsVaultMember
- 403 Forbidden returned for unauthorized actions
- Failed permission checks logged in audit trail (optional for security monitoring)

### US-9: Audit Trail for Research Integrity
**As a** researcher  
**I want to** view a complete history of vault changes  
**So that** I can verify research integrity and collaboration history  

**Acceptance Criteria:**
- GET `/api/v1/vaults/{id}/audit-logs/`
- Logged events:
  - `vault.created`, `vault.updated`, `vault.archived`, `vault.restored`
  - `membership.added`, `membership.role_changed`, `membership.removed`
- Each entry includes: timestamp, actor (user), action, vault_id, metadata (JSON)
- Audit logs are immutable (no update/delete endpoints)
- Ordered by `created_at DESC`

---

## 3. Technical Specifications

### 3.1 Database Schema

#### Vault Model
```python
# backend/apps/vaults/models.py
class Vault(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        'users.User', 
        on_delete=models.CASCADE, 
        related_name='owned_vaults'
    )
    members = models.ManyToManyField(
        'users.User', 
        through='VaultMembership', 
        related_name='vaults'
    )
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'is_archived']),
            models.Index(fields=['created_at']),
        ]
```

#### VaultMembership Model
```python
class RoleChoices(models.TextChoices):
    OWNER = 'OWNER', 'Owner'
    CONTRIBUTOR = 'CONTRIBUTOR', 'Contributor'
    VIEWER = 'VIEWER', 'Viewer'

class VaultMembership(models.Model):
    ROLE_WEIGHTS = {
        RoleChoices.OWNER: 3,
        RoleChoices.CONTRIBUTOR: 2,
        RoleChoices.VIEWER: 1,
    }
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    vault = models.ForeignKey(Vault, on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20, 
        choices=RoleChoices.choices, 
        default=RoleChoices.CONTRIBUTOR
    )
    added_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(
        'users.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='memberships_created'
    )
    
    class Meta:
        unique_together = [('vault', 'user')]
        constraints = [
            models.CheckConstraint(
                check=models.Q(vault__vaultmembership__role='OWNER') | 
                      models.Q(role='OWNER'),
                name='at_least_one_owner',
                violation_error_message='Vault must have at least one owner'
            )
        ]
        indexes = [
            models.Index(fields=['vault', 'role']),
            models.Index(fields=['user']),
        ]
    
    def get_role_weight(self):
        return self.ROLE_WEIGHTS.get(self.role, 0)
```

#### AuditLog Model
```python
class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    vault = models.ForeignKey(Vault, on_delete=models.CASCADE)
    actor = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)  # e.g., 'vault.created'
    metadata = models.JSONField(default=dict)  # Store changeset details
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vault', '-created_at']),
            models.Index(fields=['action']),
        ]
```

### 3.2 API Endpoints

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| POST | `/api/v1/vaults/` | Authenticated | Create vault |
| GET | `/api/v1/vaults/` | Authenticated | List user's vaults (with filters) |
| GET | `/api/v1/vaults/{id}/` | IsVaultMember | Retrieve vault details |
| PATCH | `/api/v1/vaults/{id}/` | IsVaultOwner | Update vault name/description |
| DELETE | `/api/v1/vaults/{id}/` | IsVaultOwner | Delete vault (hard delete) |
| POST | `/api/v1/vaults/{id}/archive/` | IsVaultOwner | Archive vault |
| POST | `/api/v1/vaults/{id}/restore/` | IsVaultOwner | Restore archived vault |
| GET | `/api/v1/vaults/{id}/members/` | IsVaultMember | List vault members |
| POST | `/api/v1/vaults/{id}/members/` | IsVaultOwner | Add member (user_id or email) |
| PATCH | `/api/v1/vaults/{id}/members/{user_id}/` | IsVaultOwner | Update member role |
| DELETE | `/api/v1/vaults/{id}/members/{user_id}/` | IsVaultOwner | Remove member |
| GET | `/api/v1/vaults/{id}/audit-logs/` | IsVaultMember | View audit trail |

### 3.3 Serializers

#### VaultSerializer
```python
class VaultSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    member_count = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    
    class Meta:
        model = Vault
        fields = [
            'id', 'name', 'description', 'owner', 'owner_username',
            'is_archived', 'created_at', 'updated_at', 
            'member_count', 'user_role'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.members.count()
    
    def get_user_role(self, obj):
        user = self.context['request'].user
        membership = obj.vaultmembership_set.filter(user=user).first()
        return membership.role if membership else None
```

#### VaultMembershipSerializer
```python
class VaultMembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = VaultMembership
        fields = ['id', 'user', 'username', 'email', 'role', 'added_at', 'added_by']
        read_only_fields = ['id', 'added_at', 'added_by']
```

### 3.4 Custom Permissions

```python
# backend/apps/vaults/permissions.py
from rest_framework import permissions
from .models import VaultMembership, RoleChoices

class IsVaultOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        vault = obj if isinstance(obj, Vault) else obj.vault
        membership = VaultMembership.objects.filter(
            vault=vault, user=request.user, role=RoleChoices.OWNER
        ).first()
        return membership is not None

class IsVaultContributor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        vault = obj if isinstance(obj, Vault) else obj.vault
        membership = VaultMembership.objects.filter(
            vault=vault, user=request.user
        ).first()
        if not membership:
            return False
        return membership.get_role_weight() >= VaultMembership.ROLE_WEIGHTS[RoleChoices.CONTRIBUTOR]

class IsVaultMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        vault = obj if isinstance(obj, Vault) else obj.vault
        return VaultMembership.objects.filter(
            vault=vault, user=request.user
        ).exists()
```

### 3.5 Views (ViewSet Structure)

```python
# backend/apps/vaults/views.py
class VaultViewSet(viewsets.ModelViewSet):
    serializer_class = VaultSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['is_archived']
    ordering_fields = ['created_at', 'name']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Vault.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct()
        
        # Role filter
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(
                vaultmembership__user=user,
                vaultmembership__role=role
            )
        
        return queryset
    
    def perform_create(self, serializer):
        vault = serializer.save(owner=self.request.user)
        # Create owner membership automatically via signal
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsVaultOwner()]
        elif self.action in ['retrieve', 'list']:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()
    
    @action(detail=True, methods=['post'], permission_classes=[IsVaultOwner])
    def archive(self, request, pk=None):
        vault = self.get_object()
        vault.is_archived = True
        vault.save()
        return Response({'status': 'archived'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsVaultOwner])
    def restore(self, request, pk=None):
        vault = self.get_object()
        vault.is_archived = False
        vault.save()
        return Response({'status': 'restored'})

class VaultMembershipViewSet(viewsets.ModelViewSet):
    serializer_class = VaultMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        vault_id = self.kwargs['vault_pk']
        return VaultMembership.objects.filter(vault_id=vault_id)
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsVaultOwner()]
        return [IsVaultMember()]
    
    def perform_create(self, serializer):
        vault = Vault.objects.get(pk=self.kwargs['vault_pk'])
        serializer.save(vault=vault, added_by=self.request.user)
```

### 3.6 Signals for Audit Logging

```python
# backend/apps/vaults/signals.py
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Vault, VaultMembership, AuditLog

@receiver(post_save, sender=Vault)
def log_vault_mutation(sender, instance, created, **kwargs):
    action = 'vault.created' if created else 'vault.updated'
    AuditLog.objects.create(
        vault=instance,
        actor=instance.owner,  # or get from request context
        action=action,
        metadata={'name': instance.name, 'is_archived': instance.is_archived}
    )

@receiver(post_save, sender=VaultMembership)
def log_membership_added(sender, instance, created, **kwargs):
    if created:
        AuditLog.objects.create(
            vault=instance.vault,
            actor=instance.added_by,
            action='membership.added',
            metadata={
                'user_id': str(instance.user.id),
                'role': instance.role
            }
        )

@receiver(pre_save, sender=VaultMembership)
def log_role_change(sender, instance, **kwargs):
    if instance.pk:
        old_instance = VaultMembership.objects.get(pk=instance.pk)
        if old_instance.role != instance.role:
            AuditLog.objects.create(
                vault=instance.vault,
                actor=None,  # Set via middleware or context
                action='membership.role_changed',
                metadata={
                    'user_id': str(instance.user.id),
                    'old_role': old_instance.role,
                    'new_role': instance.role
                }
            )

@receiver(post_delete, sender=VaultMembership)
def log_membership_removed(sender, instance, **kwargs):
    AuditLog.objects.create(
        vault=instance.vault,
        actor=None,
        action='membership.removed',
        metadata={'user_id': str(instance.user.id)}
    )

# Ensure at least one owner on membership creation
@receiver(post_save, sender=Vault)
def create_owner_membership(sender, instance, created, **kwargs):
    if created:
        VaultMembership.objects.create(
            vault=instance,
            user=instance.owner,
            role=RoleChoices.OWNER,
            added_by=instance.owner
        )
```

---

## 4. Implementation Plan

### Phase 1: Models & Migrations (Day 1)
1. Create `backend/apps/vaults/` app
2. Define `Vault`, `VaultMembership`, `AuditLog` models
3. Add database constraints (unique_together, CHECK constraint)
4. Run migrations: `python manage.py makemigrations vaults && python manage.py migrate`
5. Test model validations in Django shell

### Phase 2: Serializers & Permissions (Day 1)
1. Create serializers: `VaultSerializer`, `VaultMembershipSerializer`, `AuditLogSerializer`
2. Implement custom permissions: `IsVaultOwner`, `IsVaultContributor`, `IsVaultMember`
3. Add role weight validation in `VaultMembership.get_role_weight()`

### Phase 3: API Views (Day 2)
1. Create `VaultViewSet` with CRUD operations
2. Add custom actions: `archive`, `restore`
3. Create nested `VaultMembershipViewSet` (routed under `/vaults/{id}/members/`)
4. Add filtering/pagination to vault list endpoint
5. Wire up permissions to view actions

### Phase 4: Signals & Audit Logging (Day 2)
1. Implement signal handlers in `signals.py`
2. Connect signals in `apps.py` (`ready()` method)
3. Add `AuditLogViewSet` (read-only) with vault filtering
4. Test audit log generation via API calls

### Phase 5: URL Routing (Day 2)
1. Configure DRF router in `urls.py`
2. Register nested routes for memberships (using `drf-nested-routers` or manual config)
3. Add to main `config/urls.py`: `path('api/v1/', include('apps.vaults.urls'))`

### Phase 6: Testing (Day 3)
1. Write unit tests for models (constraints, validation)
2. Write API tests for each endpoint (success + permission failures)
3. Test edge cases: last owner deletion, role weight comparisons, archive read-only enforcement
4. Verify audit log entries for all mutation operations

### Phase 7: Integration (Day 3)
1. Add to `.planning/USER_SETUP.md`: Database migration steps
2. Add to `.planning/MANUAL_VERIFICATION.md`: 
   - Test vault creation + member invitation flow
   - Verify role permissions (try VIEWER editing vault)
   - Check audit logs in Django admin
3. Document API endpoints in project README

---

## 5. Testing Strategy

### 5.1 Unit Tests
**File:** `backend/apps/vaults/tests/test_models.py`
- Test `Vault` creation with required fields
- Test `VaultMembership` unique constraint (duplicate user in vault)
- Test CHECK constraint: deleting last owner raises error
- Test role weight calculation

### 5.2 API Tests
**File:** `backend/apps/vaults/tests/test_views.py`
- Test vault creation (authenticated user becomes owner)
- Test vault list filtering by role and archived status
- Test permission denial: VIEWER cannot add members
- Test ownership transfer: old owner downgraded to CONTRIBUTOR
- Test archive read-only: CONTRIBUTOR cannot create source in archived vault
- Test member removal: last owner deletion returns 400 error

### 5.3 Integration Tests
**File:** `backend/apps/vaults/tests/test_audit_logs.py`
- Test audit log created on vault creation
- Test membership role change logged correctly
- Test audit logs immutable (no update/delete endpoints)

### 5.4 Manual Verification Checklist
```markdown
## Vault RBAC System - 2026-02-14
- [ ] Create vault via API, verify owner membership auto-created
- [ ] Add member as CONTRIBUTOR, check they can view but not delete vault
- [ ] Transfer ownership, verify previous owner becomes CONTRIBUTOR
- [ ] Archive vault, attempt to edit sources (should fail)
- [ ] Restore vault, verify edit permissions restored
- [ ] Check audit logs in `/api/v1/vaults/{id}/audit-logs/`
- [ ] Attempt to remove last owner (should fail with 400 error)
```

---

## 6. Dependencies

### 6.1 Backend Packages
```plaintext
Django>=4.2,<5.0
djangorestframework>=3.14
django-filter>=23.0
psycopg2-binary>=2.9
```

### 6.2 Database
- PostgreSQL 14+ (for CHECK constraints and JSON fields)

### 6.3 Future Integrations
- Notification system (for email invitations in US-3)
- WebSocket channels (for real-time membership updates)

---

## 7. Security Considerations

1. **Permission Checks:** All vault mutations enforce role-based permissions via DRF
2. **Audit Trail:** Immutable logs prevent tampering with collaboration history
3. **Ownership Transfer:** Requires explicit owner action, cannot be forced by contributors
4. **Archived Vault Safety:** Read-only mode prevents accidental data loss
5. **Database Constraints:** CHECK constraint ensures vault integrity (at least one owner)

---

## 8. Open Questions & Future Enhancements

1. **Pending Invitations:** Email invite flow for non-existent users (requires notification system)
2. **Bulk Member Management:** Import CSV of collaborators with roles
3. **Vault Templates:** Pre-defined vault structures for common research types
4. **Analytics:** Dashboard showing vault activity metrics (member contributions, source growth)
5. **Soft Delete:** Change vault deletion to soft delete with 30-day recovery window

---

## 9. Acceptance Criteria Summary

### Must-Have (MVP)
- ✅ Vault CRUD with owner/contributor/viewer roles
- ✅ Member management (add, update role, remove)
- ✅ Custom DRF permissions with role weight hierarchy
- ✅ Vault archive/restore with read-only enforcement
- ✅ Audit logging for all mutations
- ✅ API filtering by role and archived status

### Should-Have (Post-MVP)
- Email invitation flow for external users
- Bulk member import
- Audit log export (CSV/JSON)

### Could-Have (Future)
- Vault templates
- Activity analytics dashboard
- Soft delete with recovery window

---

## 10. Appendix

### File Structure
```
backend/apps/vaults/
├── __init__.py
├── apps.py                    # Register signal handlers
├── models.py                  # Vault, VaultMembership, AuditLog
├── serializers.py             # DRF serializers
├── permissions.py             # Custom permission classes
├── views.py                   # ViewSets
├── urls.py                    # Router configuration
├── signals.py                 # Audit log signal handlers
├── admin.py                   # Django admin registration
├── migrations/
│   └── 0001_initial.py
└── tests/
    ├── test_models.py
    ├── test_views.py
    └── test_audit_logs.py
```

### Environment Variables
None required for this feature (uses existing DATABASE_URL, SECRET_KEY from project config)

### Related Documentation
- CLAUDE.md: Project architecture and tech stack
- Django DRF Permissions: https://www.django-rest-framework.org/api-guide/permissions/
- PostgreSQL CHECK Constraints: https://www.postgresql.org/docs/current/ddl-constraints.html

---

**PRD Status:** ✅ Ready for Implementation  
**Estimated Effort:** 3 days (1 developer)  
**Risk Level:** Low (standard Django patterns, well-defined requirements)