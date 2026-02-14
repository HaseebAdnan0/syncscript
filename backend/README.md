# SyncScript Backend

Django REST API for collaborative research and citation management.

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Redis 6+

### Installation

1. **Create virtual environment**
```bash
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash
# or
source venv/bin/activate       # Linux/Mac
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp ../.env.example ../.env
# Edit .env with your settings
```

4. **Create database**
```bash
# Using psql
createdb syncscript
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Run development server**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/v1/`

## Testing

Run all tests:
```bash
python manage.py test
```

Run specific test class:
```bash
python manage.py test apps.users.tests.RegistrationAPITests
```

Run with coverage:
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register/` - Register new user
- `POST /api/v1/auth/verify-email/` - Verify email with token
- `POST /api/v1/auth/resend-verification/` - Resend verification email
- `POST /api/v1/auth/login/` - Login (get JWT tokens)
- `POST /api/v1/auth/refresh/` - Refresh access token

### Admin
- `/admin/` - Django admin panel

## Email Configuration

For development, you can use Django's console email backend:

In `config/settings.py`, change:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

For production, configure SMTP in `.env`:
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Rate Limiting

Registration endpoints are rate-limited:
- Registration: 5 attempts/minute per IP
- Resend verification: 3 attempts/hour per IP

To disable rate limiting (e.g., for testing):
```python
RATELIMIT_ENABLE = False
```

## Project Structure

```
backend/
├── config/              # Django settings and URL routing
├── apps/
│   └── users/          # User authentication and management
│       ├── models.py   # User model with email verification
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       ├── permissions.py
│       ├── admin.py
│       └── tests.py
├── core/               # Shared utilities (future)
└── manage.py
```

## Development Tips

### Run with console email backend for testing
```bash
# In settings.py temporarily:
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### Create test user
```python
python manage.py shell
>>> from apps.users.models import User
>>> user = User.objects.create_user(email='test@example.com', username='testuser', password='TestPass123!')
>>> user.verify_email()  # Skip email verification for testing
```

### Check Redis connection
```bash
redis-cli ping
# Should return: PONG
```

## Real-Time WebSocket

SyncScript supports real-time collaboration through WebSocket connections powered by Django Channels.

### Connection Endpoint

Connect to vault rooms using WebSocket:
```
ws://localhost:8000/ws/vault/{vault_id}/?token={jwt_access_token}
```

**Parameters:**
- `vault_id`: UUID of the vault to connect to
- `token`: JWT access token from `/api/v1/auth/login/`

### Required Services

To run the WebSocket system, you need the following services running:

1. **Redis** (channel layer backend)
   ```bash
   redis-server
   ```

2. **Daphne** (ASGI server for WebSocket support)
   ```bash
   daphne -b 0.0.0.0 -p 8000 config.asgi:application
   ```

3. **Celery Worker** (for broadcasting events)
   ```bash
   celery -A config worker -l info -Q websocket_events
   ```

4. **Celery Beat** (for periodic cleanup tasks)
   ```bash
   celery -A config beat -l info
   ```

### Event Types

The WebSocket connection broadcasts the following real-time events:

- `source.created` - New source added to vault
- `source.updated` - Source metadata modified
- `source.deleted` - Source removed from vault
- `annotation.created` - New annotation added to source
- `member.added` - New member added to vault
- `presence.update` - User joined/left vault room

### Client Messages

Clients can send the following message types:

- `{"type": "heartbeat"}` - Keep connection alive (send every 30-60 seconds)
- `{"type": "replay_request", "since_seq": N}` - Request missed events after reconnection

### Rate Limiting

WebSocket connections have 4 layers of rate limiting:
- **Layer 1**: Max 5 connections per user
- **Layer 2**: Max 100 connections per vault
- **Layer 3**: Max 60 messages per minute per connection
- **Layer 4**: Automatic disconnect after 5 minutes without heartbeat
