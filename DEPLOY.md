# SyncScript Deployment Guide

This guide covers deploying SyncScript to a VPS with Docker, alongside existing projects.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        VPS (16GB / 4 CPU)                        │
├─────────────────────────────────────────────────────────────────┤
│  nginx-proxy (central)                                          │
│  ├── Port 80/443                                                │
│  ├── SSL termination                                            │
│  └── Routes to all apps                                         │
├─────────────────────────────────────────────────────────────────┤
│  syncscript_backend    │  syncscript_frontend   │  syncscript_db │
│  (Django + Daphne)     │  (Next.js standalone)  │  (PostgreSQL)  │
│  Port 8000 (internal)  │  Port 3000 (internal)  │  Port 5432     │
├─────────────────────────────────────────────────────────────────┤
│  syncscript_redis      │  syncscript_celery                     │
│  (Cache + Channels)    │  (Async tasks)                         │
│  Port 6379 (internal)  │                                        │
├─────────────────────────────────────────────────────────────────┤
│  Other projects: pakbearings, hitec, digitalise-agency          │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **VPS with Docker** - Should already have:
   - Docker & Docker Compose
   - Central nginx-proxy at `/opt/apps/nginx-proxy/`
   - `proxy_network` Docker network
   - `deploy` user with SSH key

2. **DNS Configuration**:
   - A record: `syncscript.haseebadnan.com` → VPS IP

3. **GitHub Repository** with Actions enabled

## Initial VPS Setup

### 1. Clone the Repository

```bash
ssh deploy@YOUR_VPS_IP
cd /opt/apps
git clone https://github.com/HaseebAdnan0/syncscript.git
cd syncscript
```

### 2. Run Setup Script

```bash
sudo ./deploy/setup-syncscript.sh
```

This will:
- Generate `.env` with random secrets
- Create Docker volumes
- Configure nginx proxy
- Start containers
- Obtain SSL certificate

### 3. Configure Environment Variables

```bash
nano /opt/apps/syncscript/.env
```

Fill in the required values:
- `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` - SMTP credentials
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - Google OAuth
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` - GitHub OAuth
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` - Cloudflare R2
- `ANTHROPIC_API_KEY` - Claude API key

### 4. Restart Services

```bash
cd /opt/apps/syncscript
docker compose -f docker-compose.yml -f docker-compose.multiapp.yml up -d
```

## GitHub Actions Setup

### Required Secrets

Add these secrets to your GitHub repository (Settings → Secrets → Actions):

| Secret | Value |
|--------|-------|
| `VPS_HOST` | Your VPS IP address |
| `VPS_USER` | `deploy` |
| `VPS_SSH_KEY` | SSH private key (from existing setup) |
| `NEXT_PUBLIC_API_URL` | `https://syncscript.haseebadnan.com/api/v1` |
| `NEXT_PUBLIC_WS_URL` | `wss://syncscript.haseebadnan.com/ws` |
| `NEXT_PUBLIC_PUSHER_KEY` | (optional) Pusher key |
| `NEXT_PUBLIC_PUSHER_CLUSTER` | (optional) Pusher cluster |

### Triggering Deployments

Deployments are triggered by commit message prefixes:

```bash
# Fast deploy (no tests)
git commit -m "[deploy] Add new feature"

# Tested deploy (runs tests first)
git commit -m "[test-deploy] Fix critical bug"
```

## Manual Operations

### View Logs

```bash
# Backend logs
docker logs -f syncscript_backend

# Frontend logs
docker logs -f syncscript_frontend

# Celery logs
docker logs -f syncscript_celery
```

### Run Django Commands

```bash
docker exec -it syncscript_backend python manage.py shell
docker exec -it syncscript_backend python manage.py createsuperuser
docker exec -it syncscript_backend python manage.py migrate
```

### Database Backup

```bash
docker exec syncscript_db pg_dump -U syncscript syncscript_db > backup.sql
```

### Container Status

```bash
docker ps --format "table {{.Names}}\t{{.Status}}" | grep syncscript
```

## Removal

To completely remove SyncScript without affecting other projects, see the auto-generated `REMOVE.md` in the project directory, or:

```bash
# Stop containers
cd /opt/apps/syncscript
docker compose -f docker-compose.yml -f docker-compose.multiapp.yml down

# Remove volumes (WARNING: deletes all data!)
docker volume rm syncscript_postgres_data syncscript_redis_data syncscript_static syncscript_media syncscript_logs

# Remove nginx config
rm /opt/apps/nginx-proxy/conf.d/syncscript.conf
docker exec nginx_proxy nginx -s reload

# Remove project
rm -rf /opt/apps/syncscript
```

## Troubleshooting

### Backend won't start

1. Check logs: `docker logs syncscript_backend`
2. Verify database is running: `docker exec syncscript_db pg_isready`
3. Check .env file has all required values

### Frontend 404 errors

1. Ensure `output: 'standalone'` is in `next.config.mjs`
2. Rebuild: `docker compose build frontend`

### WebSocket connection failed

1. Check nginx config has `/ws/` location
2. Verify `ALLOWED_HOSTS` includes the domain
3. Check Redis is running: `docker exec syncscript_redis redis-cli ping`

### SSL certificate issues

```bash
# Check certificate status
sudo certbot certificates

# Renew manually
sudo certbot renew

# Request new certificate
sudo certbot certonly --webroot -w /opt/apps/nginx-proxy/certbot -d syncscript.haseebadnan.com
```

## Local Development with Docker

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

Access at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1/
- Django Admin: http://localhost:8000/admin/
