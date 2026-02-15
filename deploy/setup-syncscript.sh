#!/bin/bash
# ==============================================================================
# SyncScript VPS Setup Script
# Sets up SyncScript on a VPS with shared Nginx reverse proxy
#
# Prerequisites:
#   - VPS with Docker installed (use setup-multiapp-vps.sh first if needed)
#   - DNS A record pointing to VPS IP: syncscript.haseebadnan.com
#   - Git repo cloned: /opt/apps/syncscript
#   - proxy_network Docker network exists
#
# Usage:
#   chmod +x setup-syncscript.sh
#   sudo ./setup-syncscript.sh
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step()  { echo -e "\n${BLUE}==> $1${NC}"; }

# ==============================================================================
# Configuration
# ==============================================================================
APPS_DIR="/opt/apps"
SYNCSCRIPT_DIR="$APPS_DIR/syncscript"
PROXY_DIR="$APPS_DIR/nginx-proxy"
DEPLOY_USER="deploy"
DOMAIN="syncscript.haseebadnan.com"

# ==============================================================================
# Helper functions
# ==============================================================================
generate_secret() {
    openssl rand -hex "$1"
}

# ==============================================================================
# Preflight checks
# ==============================================================================
preflight() {
    log_step "Preflight checks..."

    if [ "$EUID" -ne 0 ]; then
        log_error "Run as root: sudo ./setup-syncscript.sh"
        exit 1
    fi

    if [ ! -d "$SYNCSCRIPT_DIR" ]; then
        log_error "SyncScript not found at $SYNCSCRIPT_DIR"
        log_error "Clone it first: git clone <repo> $SYNCSCRIPT_DIR"
        exit 1
    fi

    if ! docker network ls | grep -q "proxy_network"; then
        log_error "proxy_network not found. Run setup-multiapp-vps.sh first."
        exit 1
    fi

    read -p "Enter email for SSL certificate (press Enter if cert already exists): " CERTBOT_EMAIL

    log_info "SyncScript: $SYNCSCRIPT_DIR"
    log_info "Domain: $DOMAIN"
}

# ==============================================================================
# Setup environment
# ==============================================================================
setup_env() {
    log_step "Setting up environment..."

    if [ ! -f "$SYNCSCRIPT_DIR/.env" ]; then
        log_info "Creating .env file..."
        cat > "$SYNCSCRIPT_DIR/.env" <<EOF
# Database
DB_NAME=syncscript_db
DB_USER=syncscript
DB_PASSWORD=$(generate_secret 16)

# Django
SECRET_KEY=$(generate_secret 32)
DEBUG=False
ALLOWED_HOSTS=$DOMAIN
CORS_ALLOWED_ORIGINS=https://$DOMAIN
CSRF_TRUSTED_ORIGINS=https://$DOMAIN
SITE_URL=https://$DOMAIN

# Email (Hostinger SMTP)
EMAIL_HOST=smtp.hostinger.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@$DOMAIN

# OAuth (fill in your credentials)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# Cloudflare R2 Storage (fill in your credentials)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=syncscript-files
AWS_S3_ENDPOINT_URL=
AWS_S3_REGION_NAME=auto

# AI (fill in your key)
ANTHROPIC_API_KEY=
AI_DAILY_LIMIT=20

# Docker
IMAGE_TAG=latest

# Host ports (for debug access, nginx uses Docker network)
POSTGRES_PORT=5436
BACKEND_PORT=8005
FRONTEND_PORT=3005
REDIS_PORT=6380
EOF
        log_info ".env created - fill in missing values"
    else
        log_warn ".env already exists, preserving existing values"
    fi

    chown -R $DEPLOY_USER:$DEPLOY_USER "$SYNCSCRIPT_DIR/.env"
}

# ==============================================================================
# Create Docker volumes
# ==============================================================================
create_volumes() {
    log_step "Creating Docker volumes..."

    docker volume create syncscript_postgres_data 2>/dev/null || true
    docker volume create syncscript_redis_data 2>/dev/null || true
    docker volume create syncscript_static 2>/dev/null || true
    docker volume create syncscript_media 2>/dev/null || true
    docker volume create syncscript_logs 2>/dev/null || true

    log_info "Volumes created"
}

# ==============================================================================
# Update nginx proxy config
# ==============================================================================
setup_nginx() {
    log_step "Configuring nginx proxy..."

    # Add upstream to main nginx.conf if not already present
    if ! grep -q "syncscript_backend" "$PROXY_DIR/nginx.conf" 2>/dev/null; then
        log_info "Adding SyncScript upstreams to nginx.conf..."
        # Insert before the include line
        sed -i '/include \/etc\/nginx\/conf.d\/\*.conf;/i\
    upstream syncscript_backend {\
        server syncscript_backend:8000;\
        keepalive 32;\
    }\
\
    upstream syncscript_frontend {\
        server syncscript_frontend:3000;\
        keepalive 32;\
    }' "$PROXY_DIR/nginx.conf"
    fi

    # Copy site config (HTTP only initially)
    log_info "Creating HTTP-only nginx config..."
    cat > "$PROXY_DIR/conf.d/syncscript.conf" <<'NGINX'
server {
    listen 80;
    server_name syncscript.haseebadnan.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    client_max_body_size 100M;

    # Frontend (Next.js)
    location / {
        proxy_pass http://syncscript_frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://syncscript_backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Django Admin
    location /admin/ {
        proxy_pass http://syncscript_backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # OAuth callbacks
    location /accounts/ {
        proxy_pass http://syncscript_backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket connections
    location /ws/ {
        proxy_pass http://syncscript_backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Static files
    location /static/ {
        alias /var/www/syncscript/static/;
        expires 30d;
    }

    # Media files
    location /media/ {
        alias /var/www/syncscript/media/;
        expires 7d;
    }
}
NGINX

    # Update proxy docker-compose.yml to mount syncscript volumes
    if ! grep -q "syncscript_static" "$PROXY_DIR/docker-compose.yml" 2>/dev/null; then
        log_info "Adding SyncScript volumes to nginx proxy..."
        # Add to volumes section
        sed -i '/volumes:/a\
      - syncscript_static:/var/www/syncscript/static:ro\
      - syncscript_media:/var/www/syncscript/media:ro' "$PROXY_DIR/docker-compose.yml"

        # Add external volume definitions
        echo "  syncscript_static:" >> "$PROXY_DIR/docker-compose.yml"
        echo "    external: true" >> "$PROXY_DIR/docker-compose.yml"
        echo "    name: syncscript_static" >> "$PROXY_DIR/docker-compose.yml"
        echo "  syncscript_media:" >> "$PROXY_DIR/docker-compose.yml"
        echo "    external: true" >> "$PROXY_DIR/docker-compose.yml"
        echo "    name: syncscript_media" >> "$PROXY_DIR/docker-compose.yml"
    fi

    log_info "Nginx configured"
}

# ==============================================================================
# Start containers
# ==============================================================================
start_containers() {
    log_step "Starting SyncScript containers..."

    cd "$SYNCSCRIPT_DIR"
    sudo -u $DEPLOY_USER docker compose -f docker-compose.yml -f docker-compose.multiapp.yml up -d

    log_info "Waiting for services to start..."
    sleep 20

    # Restart nginx proxy to pick up new config
    cd "$PROXY_DIR"
    sudo -u $DEPLOY_USER docker compose up -d --force-recreate

    sleep 5
    log_info "Containers started"
}

# ==============================================================================
# Setup SSL
# ==============================================================================
setup_ssl() {
    log_step "Setting up SSL certificate..."

    if [ -z "$CERTBOT_EMAIL" ]; then
        log_warn "Skipping SSL setup (no email provided)"
        log_warn "Run manually: certbot certonly --webroot -w $PROXY_DIR/certbot -d $DOMAIN"
        return
    fi

    if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
        log_info "Certificate already exists for $DOMAIN"
    else
        log_info "Requesting certificate for $DOMAIN..."
        certbot certonly --webroot \
            -w "$PROXY_DIR/certbot" \
            -d "$DOMAIN" \
            --email "$CERTBOT_EMAIL" \
            --agree-tos --non-interactive \
            || log_warn "Failed to get cert - DNS may not be pointing here yet"
    fi

    # If cert exists, upgrade to HTTPS config
    if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
        log_info "Upgrading nginx config to HTTPS..."
        cat > "$PROXY_DIR/conf.d/syncscript.conf" <<'NGINX'
server {
    listen 80;
    server_name syncscript.haseebadnan.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name syncscript.haseebadnan.com;

    ssl_certificate /etc/letsencrypt/live/syncscript.haseebadnan.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/syncscript.haseebadnan.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    client_max_body_size 100M;

    # Frontend (Next.js)
    location / {
        proxy_pass http://syncscript_frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://syncscript_backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Django Admin
    location /admin/ {
        proxy_pass http://syncscript_backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # OAuth callbacks
    location /accounts/ {
        proxy_pass http://syncscript_backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket connections
    location /ws/ {
        proxy_pass http://syncscript_backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Static files
    location /static/ {
        alias /var/www/syncscript/static/;
        expires 30d;
    }

    # Media files
    location /media/ {
        alias /var/www/syncscript/media/;
        expires 7d;
    }
}
NGINX

        docker exec nginx_proxy nginx -s reload 2>/dev/null || true
        log_info "HTTPS enabled"
    fi
}

# ==============================================================================
# Print removal instructions
# ==============================================================================
print_removal() {
    cat > "$SYNCSCRIPT_DIR/REMOVE.md" <<'EOF'
# SyncScript Removal Instructions

To completely remove SyncScript from the VPS without affecting other projects:

```bash
# 1. Stop and remove containers
cd /opt/apps/syncscript
docker compose -f docker-compose.yml -f docker-compose.multiapp.yml down

# 2. Remove Docker volumes (WARNING: deletes all data!)
docker volume rm syncscript_postgres_data
docker volume rm syncscript_redis_data
docker volume rm syncscript_static
docker volume rm syncscript_media
docker volume rm syncscript_logs

# 3. Remove nginx config
rm /opt/apps/nginx-proxy/conf.d/syncscript.conf

# 4. Remove upstreams from nginx.conf (manual edit)
nano /opt/apps/nginx-proxy/nginx.conf
# Delete the syncscript_backend and syncscript_frontend upstream blocks

# 5. Remove volume mounts from nginx docker-compose.yml (manual edit)
nano /opt/apps/nginx-proxy/docker-compose.yml
# Remove syncscript_static and syncscript_media volume references

# 6. Reload nginx
docker exec nginx_proxy nginx -s reload

# 7. Remove SSL certificate (optional)
sudo certbot delete --cert-name syncscript.haseebadnan.com

# 8. Remove project directory
rm -rf /opt/apps/syncscript

# 9. Clean up Docker images
docker image prune -a
```
EOF
    log_info "Removal instructions saved to REMOVE.md"
}

# ==============================================================================
# Print summary
# ==============================================================================
print_summary() {
    VPS_IP=$(curl -sf ifconfig.me 2>/dev/null || echo "YOUR_VPS_IP")

    echo ""
    echo -e "${GREEN}================================================================${NC}"
    echo -e "${GREEN}              SYNCSCRIPT SETUP COMPLETE                        ${NC}"
    echo -e "${GREEN}================================================================${NC}"
    echo ""
    echo -e "${BLUE}Containers running:${NC}"
    docker ps --format "  {{.Names}}  {{.Status}}" 2>/dev/null | grep -E "syncscript|nginx"
    echo ""
    echo -e "${BLUE}URL:${NC}"
    echo "  https://$DOMAIN"
    echo ""
    echo -e "${BLUE}GitHub Secrets to configure:${NC}"
    echo "  VPS_HOST:              $VPS_IP"
    echo "  VPS_USER:              $DEPLOY_USER"
    echo "  VPS_SSH_KEY:           (use existing deploy key from other projects)"
    echo "  NEXT_PUBLIC_API_URL:   https://$DOMAIN/api/v1"
    echo "  NEXT_PUBLIC_WS_URL:    wss://$DOMAIN/ws"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Add GitHub Secrets to the repository"
    echo "  2. Edit .env file to add missing credentials:"
    echo "     nano $SYNCSCRIPT_DIR/.env"
    echo "  3. Push a commit with [deploy] prefix to trigger auto-deploy"
    echo "  4. See REMOVE.md for removal instructions"
    echo ""
}

# ==============================================================================
# Main
# ==============================================================================
main() {
    echo -e "${GREEN}"
    echo "================================================================"
    echo "  SyncScript VPS Setup"
    echo "  Shared Nginx | PostgreSQL | Redis | Auto-Deploy"
    echo "================================================================"
    echo -e "${NC}"

    preflight
    setup_env
    create_volumes
    setup_nginx
    start_containers
    setup_ssl
    print_removal
    print_summary
}

main "$@"
