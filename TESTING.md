# SyncScript Testing Guide

## Quick Start

### Prerequisites
Ensure Docker containers are running:
```bash
docker start syncscript-db syncscript-redis
```

### Start Backend
```bash
cd backend
source venv/Scripts/activate  # Windows Git Bash
python manage.py migrate
python manage.py seed_test_data  # Load test data
python manage.py runserver
```

### Start Frontend
```bash
cd frontend
npm install
npm run dev
```

**URLs:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1/
- Admin: http://localhost:8000/admin/

---

## Test Accounts

| Email | Password | Role | Description |
|-------|----------|------|-------------|
| `admin@syncscript.test` | `TestPass123!` | Admin | Superuser with admin access |
| `alice@syncscript.test` | `TestPass123!` | Researcher | Owns "AI Research Papers" vault |
| `bob@syncscript.test` | `TestPass123!` | Collaborator | Contributor to Alice's vault |
| `charlie@syncscript.test` | `TestPass123!` | Viewer | Viewer on Alice's vault |
| `diana@syncscript.test` | `TestPass123!` | New User | Fresh account for onboarding tests |

---

## Test Data Overview

### Vaults
1. **AI Research Papers 2025** (Owner: Alice)
   - 5 sources (arXiv papers, web articles)
   - 10+ annotations with threaded replies
   - Bob as Contributor, Charlie as Viewer

2. **Climate Science Review** (Owner: Bob)
   - 3 sources
   - Private vault (no collaborators)

3. **Empty Test Vault** (Owner: Alice)
   - No sources (for testing empty states)

### Sources Include
- arXiv paper links (real URLs)
- Web article URLs
- Sample PDF metadata

### Annotations
- Top-level annotations
- Threaded replies (max 2 levels)
- Different users commenting

---

## Manual Testing Flows

### 1. Authentication (PRD 11, 12)

#### Email Login
1. Go to http://localhost:3000/login
2. Enter `alice@syncscript.test` / `TestPass123!`
3. Verify redirect to dashboard
4. Check JWT token in cookies

#### OAuth Login (if configured)
1. Click "Continue with Google"
2. Complete OAuth flow
3. Verify account created/linked

#### Password Reset
1. Click "Forgot Password"
2. Enter `alice@syncscript.test`
3. Check console for email (dev mode)
4. Click reset link, set new password

### 2. Vaults (PRD 17)

#### Create Vault
1. Login as Alice
2. Click "New Vault"
3. Enter name: "Test Vault"
4. Verify vault appears in sidebar

#### Invite Member
1. Open "AI Research Papers 2025"
2. Click "Invite" or members icon
3. Enter `diana@syncscript.test`
4. Select role: Contributor
5. Login as Diana, verify vault access

#### Archive/Delete Vault
1. Open vault settings
2. Click "Archive Vault"
3. Verify vault moves to archived section

### 3. Sources (PRD 13)

#### Add URL Source
1. Open a vault
2. Click "Add Source"
3. Enter URL: `https://arxiv.org/abs/2301.00001`
4. Verify metadata extraction

#### Upload PDF
1. Click "Upload PDF"
2. Select a PDF file (< 10MB)
3. Verify upload progress
4. Check processing status
5. Verify thumbnail generated

#### View Source Details
1. Click on a source
2. Verify metadata display
3. Check "Generate AI Summary" button

### 4. Annotations (PRD 17)

#### Create Annotation
1. Open a source
2. Click "Add Annotation"
3. Enter text: "Key finding about X"
4. Submit and verify it appears

#### Reply to Annotation
1. Find existing annotation
2. Click "Reply"
3. Enter reply text
4. Verify threaded display

#### Edit/Delete Annotation
1. Find your annotation
2. Click edit icon
3. Modify text, save
4. Click delete, confirm

### 5. Search (PRD 18)

#### Global Search
1. Click search bar (Cmd/Ctrl + K)
2. Type "machine learning"
3. Verify results from sources and annotations
4. Click result to navigate

#### Filter Search
1. Open search
2. Select filter: "Sources only"
3. Verify filtered results

### 6. AI Features (PRD 14, 15)

#### Generate Source Summary
1. Open a source with content
2. Click "Generate AI Summary"
3. Wait for processing
4. Verify summary sections appear

#### Vault Insights
1. Open vault with 3+ sources
2. Go to "Insights" tab
3. Click "Generate Insights"
4. Verify themes, gaps, cross-references

#### Ask AI
1. Open vault sidebar
2. Find "Ask AI" section
3. Type: "What are the main themes?"
4. Verify cited response

#### Rate Limiting
1. Make 20 AI requests rapidly
2. Verify rate limit error
3. Check "resets at" time

### 7. Notifications (PRD 19)

#### Check Notifications
1. Look for bell icon in header
2. Click to open notification panel
3. Verify unread count badge

#### Notification Settings
1. Go to Settings > Notifications
2. Toggle email preferences
3. Change digest frequency
4. Mute a vault

### 8. Onboarding (PRD 20)

#### New User Flow
1. Logout completely
2. Register new account
3. Verify welcome modal appears
4. Select "Explore Demo Vault"
5. Complete tutorial steps
6. Verify confetti on completion

#### Restart Tutorial
1. Login as existing user
2. Go to Settings > Onboarding
3. Click "Restart Tutorial"
4. Verify tutorial restarts

---

## API Testing with cURL

### Get JWT Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@syncscript.test", "password": "TestPass123!"}'
```

### List Vaults
```bash
curl http://localhost:8000/api/v1/vaults/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Create Source
```bash
curl -X POST http://localhost:8000/api/v1/vaults/<VAULT_ID>/sources/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/paper", "title": "Test Paper"}'
```

### Search
```bash
curl "http://localhost:8000/api/v1/search/?q=machine+learning" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## Running Automated Tests

### Backend Tests
```bash
cd backend
source venv/Scripts/activate

# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.vaults
python manage.py test apps.sources
python manage.py test apps.users

# Run with coverage
pip install coverage
coverage run manage.py test
coverage report -m
```

### Frontend Tests
```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- src/components/VaultCard.test.tsx
```

### Type Checking
```bash
# Backend
cd backend
mypy apps/

# Frontend
cd frontend
npm run type-check
```

---

## Debugging Tips

### Check Database
```bash
# Connect to PostgreSQL
docker exec -it syncscript-db psql -U postgres -d syncscript

# List tables
\dt

# Check users
SELECT email, email_verified FROM users;

# Check vaults
SELECT name, owner_id FROM vaults;
```

### Check Redis
```bash
docker exec -it syncscript-redis redis-cli

# List keys
KEYS *

# Check cache
GET cache:vaults:list
```

### Check Logs
```bash
# Django logs
tail -f backend/debug.log

# Celery worker
celery -A config worker -l debug
```

### Reset Test Data
```bash
cd backend
python manage.py flush --no-input
python manage.py seed_test_data
```

---

## Environment-Specific Notes

### Email Testing
- In development, emails are logged to console
- Check Django shell: `python manage.py shell`
- Or use MailHog: http://localhost:8025

### File Uploads
- Ensure Cloudflare R2 credentials in `.env`
- Check `AWS_S3_ENDPOINT_URL` is correct
- Files stored in `syncscript-files` bucket

### WebSocket Testing
- Open browser console
- Check for WS connection to `/ws/vault/{id}/`
- Verify real-time updates between tabs

---

## Common Issues

### "CORS error"
- Check `CORS_ALLOWED_ORIGINS` in backend `.env`
- Ensure frontend URL is listed

### "JWT expired"
- Frontend should auto-refresh tokens
- Check refresh token in cookies
- Try logging out and back in

### "Redis connection refused"
- Run `docker start syncscript-redis`
- Check `REDIS_URL` uses port 6380

### "Database connection error"
- Run `docker start syncscript-db`
- Check `DATABASE_URL` in `.env`

### "File upload failed"
- Check R2 credentials
- Verify bucket exists
- Check CORS on R2 bucket
