# SyncScript

**Collaborative Research & Citation Engine** — Built for Hackfest x Datathon

> Real-time Knowledge Vaults where researchers collaboratively verify sources, annotate PDFs, and cross-reference citations.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 6 + DRF + Django Channels |
| Frontend | Next.js 16 + React 19 + TailwindCSS 4 |
| Database | PostgreSQL |
| Cache/Realtime | Redis |
| File Storage | Cloudflare R2 (S3-compatible) |
| Auth | JWT (SimpleJWT) |
| Async Tasks | Celery |

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker (Full Stack)
```bash
docker-compose up --build
```

## Architecture

```
┌─────────────┐     WebSocket      ┌─────────────┐
│   Next.js   │◄──────────────────►│   Django    │
│   Frontend  │     REST API       │   Channels  │
└─────────────┘                    └──────┬──────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
              ┌─────▼─────┐        ┌──────▼──────┐       ┌──────▼──────┐
              │ PostgreSQL │        │    Redis    │       │ Cloudflare  │
              │  Database  │        │ Cache/PubSub│       │     R2      │
              └───────────┘        └─────────────┘       └─────────────┘
```

## Data Model

```
Users ──┬── Vaults (owner)
        │
        └── VaultMemberships ──── Vaults
                │
                └── role: OWNER | CONTRIBUTOR | VIEWER

Vaults ──── Sources ──── Annotations
               │
               └── PDFs (R2 storage)
```

## Key Features

- **Knowledge Vaults** — Shared research repositories with RBAC
- **Real-Time Sync** — WebSocket updates via Django Channels + Redis
- **Cloud Storage** — PDF uploads with signed URLs (Cloudflare R2)
- **JWT Auth** — Access (15min) + Refresh (7 days) tokens
- **Rate Limiting** — Redis-backed API throttling
- **Audit Logs** — Immutable change tracking for research integrity

## API Endpoints

```
POST   /api/v1/auth/register/
POST   /api/v1/auth/login/
POST   /api/v1/auth/refresh/

GET    /api/v1/vaults/
POST   /api/v1/vaults/
GET    /api/v1/vaults/{id}/
PUT    /api/v1/vaults/{id}/
DELETE /api/v1/vaults/{id}/

GET    /api/v1/vaults/{id}/sources/
POST   /api/v1/vaults/{id}/sources/
GET    /api/v1/sources/{id}/annotations/
POST   /api/v1/sources/{id}/annotations/
```

## WebSocket

```
ws://localhost:8000/ws/vault/{vault_id}/
```

Events: `source.created`, `source.updated`, `annotation.created`, `member.added`

## Environment Variables

See `backend/.env.example` and `frontend/.env.example` for required configuration.

## License

MIT
