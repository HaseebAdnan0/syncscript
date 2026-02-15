# SyncScript Testing Guide

## Evaluation Rubric Summary

| Category | Weight | Key Features to Demo |
|----------|--------|---------------------|
| **System Architecture & Data Modeling** | 25% | Many-to-many relationships, PostgreSQL, complex queries |
| **Real-Time & Performance** | 25% | WebSockets, Cloud Storage (R2), Redis caching, Pusher notifications |
| **Security & Access Control** | 20% | JWT auth, RBAC roles, rate-limiting, audit logs |
| **User Experience (UX/UI)** | 15% | Role-based UI, responsive design, dynamic updates |
| **Creativity & Edge** | 15% | AI citations, AI summaries, metadata extraction, search |

---

## Quick Start

### Prerequisites
```bash
# Start Docker containers
docker start syncscript-db syncscript-redis
```

### Start Backend (REST API)
```bash
cd backend
source venv/Scripts/activate  # Windows Git Bash
python manage.py migrate
python manage.py seed_test_data  # Load test data
python manage.py runserver
```

### Start Backend (WebSockets) - CRITICAL FOR 25% OF POINTS
```bash
cd backend
source venv/Scripts/activate
daphne -b 0.0.0.0 -p 8001 config.asgi:application
```
> **Note:** Run Daphne on port 8001, or use it instead of runserver on 8000

### Start Celery Worker (for async tasks)
```bash
cd backend
celery -A config worker -l info
```

### Start Frontend
```bash
cd frontend
npm run dev
```

**URLs:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1/
- Admin: http://localhost:8000/admin/

---

## Test Accounts

| Email | Password | Role | Use For |
|-------|----------|------|---------|
| `alice@syncscript.test` | `TestPass123!` | Owner | Main demo account |
| `bob@syncscript.test` | `TestPass123!` | Contributor | Real-time collaboration demo |
| `charlie@syncscript.test` | `TestPass123!` | Viewer | RBAC demo (read-only) |
| `diana@syncscript.test` | `TestPass123!` | New User | Onboarding demo |

---

## 7-MINUTE DEMO SCRIPT (Prioritized by Points)

### 1. REAL-TIME & PERFORMANCE (25% - DEMO FIRST)

#### 1.1 WebSocket Real-Time Collaboration (CRITICAL)
**Setup:** Open 2 browser windows side-by-side
1. Window 1: Login as `alice@syncscript.test`
2. Window 2: Login as `bob@syncscript.test`
3. Both open same vault: "AI Research Papers 2025"

**Demo:**
- [ ] Alice adds a new source → Bob sees it appear instantly (no refresh)
- [ ] Bob adds annotation → Alice sees it appear instantly
- [ ] Show presence indicators (who's online in vault)
- [ ] Show connection status indicator (green dot)

**If WebSocket not working:** Start Daphne server (see Quick Start)

#### 1.2 Cloud Storage (Cloudflare R2)
1. Open any vault
2. Click "Add Source" → "Upload PDF"
3. Upload a PDF file (< 10MB)
- [ ] Verify upload progress bar
- [ ] Verify file stored in cloud (not local)
- [ ] Verify presigned URL download works
- [ ] Verify thumbnail generation

#### 1.3 Redis Caching
- [ ] Load vault list → Note speed
- [ ] Reload page → Should be faster (cached)
- [ ] Check Redis: `docker exec -it syncscript-redis redis-cli KEYS "*"`

#### 1.4 Pusher Notifications
1. Login as Alice in one browser
2. Login as Bob in another browser
3. Alice invites Charlie to vault
- [ ] Bob receives browser notification
- [ ] Notification bell shows unread count
- [ ] Click notification to navigate

---

### 2. SYSTEM ARCHITECTURE & DATA MODELING (25%)

#### 2.1 Many-to-Many Relationships
**Demo the data model:**
1. Show vault with multiple members (Alice owns, Bob contributes, Charlie views)
2. Show user belonging to multiple vaults
3. Show source with multiple annotations from different users

**In Django Admin (http://localhost:8000/admin/):**
- [ ] Show VaultMembership table (user ↔ vault with role)
- [ ] Show Source → Annotations relationship
- [ ] Show AuditLog entries for data integrity

#### 2.2 Complex Queries
1. Use global search (Ctrl+K): Search "machine learning"
- [ ] Results span vaults, sources, annotations
- [ ] Full-text search with PostgreSQL tsvector
- [ ] Results respect permissions (only accessible vaults)

#### 2.3 Data Integrity
1. Open vault audit log (Settings → Activity)
- [ ] Show immutable logs of all changes
- [ ] Timestamps, user, action type, before/after

---

### 3. SECURITY & ACCESS CONTROL (20%)

#### 3.1 JWT Authentication
1. Login as Alice
2. Open DevTools → Application → Cookies
- [ ] Show `access_token` cookie (httpOnly)
- [ ] Show `refresh_token` cookie
- [ ] Explain: 15min access, 7-day refresh, auto-refresh

#### 3.2 RBAC Roles Demo (CRITICAL)
**As Owner (Alice):**
- [ ] Can edit vault settings
- [ ] Can invite/remove members
- [ ] Can delete vault
- [ ] Can change member roles

**As Contributor (Bob):**
- [ ] Can add sources
- [ ] Can add annotations
- [ ] CANNOT edit vault settings
- [ ] CANNOT remove members

**As Viewer (Charlie):**
- [ ] Can view sources
- [ ] Can view annotations
- [ ] CANNOT add sources
- [ ] CANNOT add annotations
- [ ] Settings tab hidden/disabled

#### 3.3 Rate Limiting
```bash
# Test rate limiting (5 requests/minute on auth endpoints)
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"email":"wrong@test.com","password":"wrong"}' \
    -w "\nStatus: %{http_code}\n"
done
```
- [ ] 6th request returns 429 Too Many Requests

#### 3.4 Audit Logs
1. Perform actions as different users
2. Go to vault Settings → Activity Log
- [ ] Show who did what and when
- [ ] Immutable record for research integrity

---

### 4. USER EXPERIENCE (15%)

#### 4.1 Role-Based Dynamic UI
- [ ] Owner sees: Edit, Delete, Settings, Invite buttons
- [ ] Contributor sees: Add Source, Add Annotation (no Settings)
- [ ] Viewer sees: Read-only view (no action buttons)

#### 4.2 Responsive Design
- [ ] Desktop view (full sidebar)
- [ ] Tablet view (collapsed sidebar)
- [ ] Mobile view (bottom nav or hamburger)

#### 4.3 Real-Time UI Updates
- [ ] Sources list updates without refresh
- [ ] Annotations appear instantly
- [ ] Notification badge updates in real-time
- [ ] Presence indicators show active users

---

### 5. CREATIVITY & EDGE FEATURES (15%)

#### 5.1 AI Auto-Citation (BIG DIFFERENTIATOR)
1. Open any source
2. Click citation button (quote icon)
3. Select format (APA, MLA, BibTeX, etc.)
- [ ] Citation generated automatically
- [ ] Copy to clipboard works
- [ ] Batch export all vault citations

#### 5.2 AI Metadata Extraction
1. Add a new source by URL (arXiv paper)
- [ ] Title auto-extracted
- [ ] Authors auto-extracted
- [ ] Abstract auto-extracted
- [ ] Publication date detected

#### 5.3 AI Source Summary
1. Open a source with content
2. Click "Generate AI Summary"
- [ ] Key findings extracted
- [ ] Methodology identified
- [ ] Limitations noted

#### 5.4 AI Vault Insights
1. Open vault with 3+ sources
2. Go to "Insights" tab
3. Click "Generate Insights"
- [ ] Common themes identified
- [ ] Research gaps suggested
- [ ] Cross-references found

#### 5.5 Ask AI (Q&A over vault)
1. Open vault sidebar → "Ask AI"
2. Type: "What are the main themes in this research?"
- [ ] AI responds with citations
- [ ] Sources referenced inline

#### 5.6 Full-Text Search
1. Press Ctrl+K
2. Search across all content
- [ ] Searches vaults, sources, annotations
- [ ] PostgreSQL full-text search
- [ ] Results ranked by relevance

---

## API Testing with cURL

### Get JWT Token
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@syncscript.test", "password": "TestPass123!"}' \
  | jq -r '.access')
echo $TOKEN
```

### Test RBAC - List Vaults
```bash
curl http://localhost:8000/api/v1/vaults/ \
  -H "Authorization: Bearer $TOKEN"
```

### Test Rate Limiting
```bash
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}' \
    -w "Request $i: %{http_code}\n" -o /dev/null -s
done
```

### Test Audit Logs
```bash
curl http://localhost:8000/api/v1/vaults/{VAULT_ID}/audit-logs/ \
  -H "Authorization: Bearer $TOKEN"
```

### Test Citation Export
```bash
curl "http://localhost:8000/api/v1/vaults/{VAULT_ID}/citations/export/?format=bibtex" \
  -H "Authorization: Bearer $TOKEN" \
  --output citations.bib
```

---

## Pre-Demo Checklist

### Infrastructure
- [ ] Docker containers running (`docker ps`)
- [ ] PostgreSQL accessible (port 5432)
- [ ] Redis accessible (port 6379 or 6380)
- [ ] Backend server running (port 8000)
- [ ] Daphne/WebSocket server running (port 8001 or 8000)
- [ ] Frontend running (port 3000)
- [ ] Celery worker running (for async tasks)

### Test Data
- [ ] Run `python manage.py seed_test_data`
- [ ] Verify test accounts exist
- [ ] Verify demo vault has sources and annotations

### Browser Setup
- [ ] Two browser windows ready (Alice + Bob)
- [ ] DevTools open for JWT/cookie demo
- [ ] Clear cache if needed

### Environment
- [ ] `.env` files configured
- [ ] Cloudflare R2 credentials set (for file upload demo)
- [ ] Pusher credentials set (for notifications demo)
- [ ] Anthropic API key set (for AI features demo)

---

## Troubleshooting

### WebSocket Not Connecting
```bash
# Check if Daphne is running
ps aux | grep daphne

# Start Daphne
cd backend && daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

### Redis Connection Error
```bash
docker start syncscript-redis
# Check connection
docker exec -it syncscript-redis redis-cli ping
```

### Database Connection Error
```bash
docker start syncscript-db
# Check connection
docker exec -it syncscript-db psql -U postgres -d syncscript -c "SELECT 1"
```

### Rate Limiting Not Working
- Check Redis is running
- Check `RATELIMIT_ENABLE = True` in settings
- Rate limits reset after time window expires

### AI Features Not Working
- Check `ANTHROPIC_API_KEY` in `.env`
- Check AI usage quota in Settings → AI Usage
- Rate limit: 20 requests/day per user

---

## Key Files for Code Review

### Data Modeling (25%)
- `backend/apps/vaults/models.py` - Vault, VaultMembership
- `backend/apps/sources/models.py` - Source, Annotation
- `backend/apps/users/models.py` - Custom User model

### Real-Time (25%)
- `backend/apps/vaults/consumers.py` - WebSocket consumer
- `backend/apps/vaults/routing.py` - WebSocket routing
- `backend/config/asgi.py` - ASGI configuration
- `frontend/src/hooks/useVaultSocket.ts` - WebSocket client

### Security (20%)
- `backend/apps/vaults/permissions.py` - RBAC permissions
- `backend/apps/users/views.py` - JWT auth views
- `backend/core/audit.py` - Audit logging

### AI Features (15%)
- `backend/apps/citations/` - Citation generation
- `backend/apps/ai/` - AI summaries and insights
- `frontend/src/components/features/ai/` - AI UI components
