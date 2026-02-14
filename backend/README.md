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
