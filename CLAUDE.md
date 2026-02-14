# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SyncScript** is a collaborative research & citation engine for the Hackfest x Datathon hackathon. Researchers collaboratively build "Knowledge Vaults"—shared repositories of verified sources, annotated PDFs, and cross-referenced citations.

### Core Features
- Knowledge Vaults with RBAC (Owner/Contributor/Viewer)
- Real-time collaboration via WebSockets
- PDF uploads with cloud storage
- Citation management and annotations
- Audit logging for research integrity

## Tech Stack

### Backend (Django)
```
backend/
├── config/                 # Django project settings
├── apps/
│   ├── users/             # Auth, JWT, user management
│   ├── vaults/            # Knowledge Vault CRUD
│   ├── sources/           # URL/citation sources
│   ├── annotations/       # PDF annotations, notes
│   └── notifications/     # Pusher/notification logic
├── core/                  # Shared utilities, permissions
└── requirements.txt
```

### Frontend (Next.js)
```
frontend/
├── src/
│   ├── app/               # Next.js App Router
│   ├── components/
│   │   ├── ui/            # ShadCN UI components
│   │   └── features/      # Feature-specific components
│   ├── lib/               # Utilities, API client
│   ├── hooks/             # Custom React hooks
│   └── styles/            # Global styles, design tokens
├── package.json
└── tailwind.config.ts
```

## Development Commands

### Backend
```bash
# Setup
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt

# Database
python manage.py migrate
python manage.py createsuperuser

# Run server
python manage.py runserver

# Run tests
python manage.py test
python manage.py test apps.vaults.tests.TestVaultAPI  # Single test class

# Celery (for async tasks)
celery -A config worker -l info
```

### Frontend
```bash
# Setup
cd frontend
npm install

# Development
npm run dev

# Build
npm run build

# Lint
npm run lint

# Type check
npm run type-check
```

### Docker (Full Stack)
```bash
docker-compose up --build
docker-compose exec backend python manage.py migrate
```

## Architecture Decisions

### Database Schema (PostgreSQL)
- **Users**: Extended Django user with profile
- **Vaults**: Knowledge repositories (owner_id FK)
- **VaultMemberships**: Many-to-many with role enum (OWNER/CONTRIBUTOR/VIEWER)
- **Sources**: URLs, titles, metadata (vault_id FK)
- **Annotations**: Notes linked to sources (source_id FK, user_id FK)
- **AuditLogs**: Immutable change records for research integrity

### Real-Time (Django Channels + Redis)
- WebSocket consumers in `apps/vaults/consumers.py`
- Channel layers backed by Redis
- Frontend uses native WebSocket or socket.io-client

### Caching Strategy (Redis)
- Django cache framework with Redis backend
- Cache vault listings, source counts, user permissions
- Invalidate on write operations via signals

### File Storage (Cloudflare R2 or AWS S3)
- `django-storages` with S3-compatible backend
- Signed URLs for secure PDF access
- Multipart upload for large files

### Authentication
- `djangorestframework-simplejwt` for JWT tokens
- Access token (15min) + Refresh token (7 days)
- Frontend stores in httpOnly cookies

### Rate Limiting
- `django-ratelimit` on API views
- Redis-backed throttling

### Notifications
- Pusher Channels for browser push
- Optional Twilio for SMS

## Key Packages

### Backend (requirements.txt)
```
Django>=6.0,<7.0
djangorestframework>=3.16.1
djangorestframework-simplejwt>=5.5.1
django-cors-headers>=4.6
django-storages[s3]>=1.14
django-redis>=5.4
channels[daphne]>=4.3.1
channels-redis>=4.2
celery[redis]>=5.6.2
django-ratelimit>=4.1
psycopg[binary]>=3.2
pusher>=3.3
python-dotenv>=1.0
django-filter>=25.1
```

### Frontend (package.json dependencies)
```json
{
  "next": "^16.1",
  "react": "^19.2",
  "react-dom": "^19.2",
  "@tanstack/react-query": "^5.90",
  "axios": "^1.7",
  "tailwindcss": "^4.1",
  "class-variance-authority": "^0.7",
  "clsx": "^2.1",
  "tailwind-merge": "^3.0",
  "lucide-react": "^0.563",
  "zustand": "^5.0",
  "@radix-ui/react-dialog": "^1.1",
  "@radix-ui/react-dropdown-menu": "^2.1",
  "@radix-ui/react-tabs": "^1.1",
  "@radix-ui/react-toast": "^1.2"
}
```

## Design System: Bitcoin DeFi Aesthetic

This project uses a dark, premium aesthetic inspired by Bitcoin/crypto platforms. **Not generic dark mode.**

### Color Tokens
```css
--background: #030304;      /* True Void */
--surface: #0F1115;         /* Dark Matter */
--foreground: #FFFFFF;      /* Pure Light */
--muted: #94A3B8;          /* Stardust */
--border: #1E293B;         /* Dim Boundary */
--primary: #F7931A;        /* Bitcoin Orange */
--secondary: #EA580C;      /* Burnt Orange */
--accent: #FFD600;         /* Digital Gold */
```

### Typography
- **Headings**: `Space Grotesk` (font-heading)
- **Body**: `Inter` (font-body)
- **Data/Mono**: `JetBrains Mono` (font-mono)

### Key Visual Rules
1. **Gradient text** on hero headlines: `bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent`
2. **Colored shadows** (orange/gold tints), never pure black shadows
3. **Glass morphism**: `backdrop-blur-lg bg-white/5 border border-white/10`
4. **Buttons**: Pill-shaped (`rounded-full`), gradient background, glow on hover
5. **Cards**: `bg-[#0F1115] border border-white/10 rounded-2xl`, lift on hover
6. **Inputs**: Bottom border only, `border-b-2 border-white/20`, orange on focus

### Component Patterns
```tsx
// Primary Button
<button className="bg-gradient-to-r from-[#EA580C] to-[#F7931A] text-white font-bold uppercase tracking-wider rounded-full px-6 py-3 shadow-[0_0_20px_-5px_rgba(234,88,12,0.5)] hover:scale-105 transition-all">
  Action
</button>

// Card
<div className="bg-[#0F1115] border border-white/10 rounded-2xl p-8 hover:-translate-y-1 hover:border-[#F7931A]/50 transition-all">
  {children}
</div>

// Input
<input className="bg-black/50 border-b-2 border-white/20 h-12 px-4 text-white focus:border-[#F7931A] focus:outline-none" />
```

### Layout
- Container: `max-w-7xl mx-auto`
- Section padding: `py-24`
- Grid gaps: `gap-8` or `gap-12`
- No `<hr>` dividers—use spacing and background alternation

### Animations
- Float: `animation: float 8s ease-in-out infinite` for hero elements
- Hover transitions: `transition-all duration-300`
- Pulsing indicators: `animate-ping` for live status

## API Conventions

### REST Endpoints
```
/api/v1/auth/register/
/api/v1/auth/login/
/api/v1/auth/refresh/
/api/v1/vaults/
/api/v1/vaults/{id}/
/api/v1/vaults/{id}/members/
/api/v1/vaults/{id}/sources/
/api/v1/sources/{id}/annotations/
```

### WebSocket Channels
```
ws://localhost:8000/ws/vault/{vault_id}/
```

Events: `source.created`, `source.updated`, `annotation.created`, `member.added`

## Environment Variables

### Backend (.env)
```
SECRET_KEY=
DEBUG=True
DATABASE_URL=postgres://user:pass@localhost:5432/syncscript
REDIS_URL=redis://localhost:6379/0
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
PUSHER_APP_ID=
PUSHER_KEY=
PUSHER_SECRET=
PUSHER_CLUSTER=
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_PUSHER_KEY=
NEXT_PUBLIC_PUSHER_CLUSTER=
```

## Task Management Rules

### Manual Verification Tasks
All tasks requiring manual user verification (testing flows, visual checks, integration confirmations) MUST be appended to:
```
.planning/MANUAL_VERIFICATION.md
```

Format:
```markdown
## [Feature Name] - [Date Added]
- [ ] Description of what to verify
- [ ] Expected behavior
- [ ] Steps to test
```

### User Setup Requirements
All setup steps requiring user action (env vars, external service accounts, local tools) MUST be appended to:
```
.planning/USER_SETUP.md
```

Format:
```markdown
## [Service/Tool Name]
### Required For: [Feature/Component]
### Steps:
1. Step-by-step instructions
### Environment Variables:
- `VAR_NAME`: Description
```

## Edge Features for Bonus Points

Consider implementing:
- **AI Metadata Extraction**: Use OpenAI/Claude API to auto-extract title, authors, abstract from PDFs
- **Auto-Citation Generation**: Generate BibTeX/APA citations from source URLs
- **Conflict Resolution**: Operational Transform or CRDT for concurrent annotation edits
- **Smart Search**: Full-text search with pg_trgm or Elasticsearch
