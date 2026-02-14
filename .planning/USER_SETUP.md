# User Setup Requirements

## PostgreSQL Database
### Required For: Backend Django application
### Steps:
1. Install PostgreSQL 14+ from https://www.postgresql.org/download/
2. Create database for SyncScript:
   ```bash
   # Using psql command line
   createdb syncscript

   # Or using psql shell
   psql -U postgres
   CREATE DATABASE syncscript;
   \q
   ```
3. Verify connection:
   ```bash
   psql -U postgres -d syncscript -c "SELECT version();"
   ```

### Environment Variables:
- `DB_NAME`: syncscript
- `DB_USER`: postgres (or your PostgreSQL username)
- `DB_PASSWORD`: your PostgreSQL password
- `DB_HOST`: localhost
- `DB_PORT`: 5432

---

## Redis Server
### Required For: Caching and rate limiting
### Steps:
1. **Windows**:
   - Download Redis for Windows from https://github.com/microsoftarchive/redis/releases
   - Or use WSL2 and install via `sudo apt install redis-server`

2. **Linux/Mac**:
   ```bash
   # Ubuntu/Debian
   sudo apt install redis-server

   # macOS
   brew install redis
   ```

3. Start Redis:
   ```bash
   # Linux
   sudo systemctl start redis

   # macOS
   brew services start redis

   # Windows (WSL2)
   sudo service redis-server start
   ```

4. Verify Redis is running:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

### Environment Variables:
- `REDIS_URL`: redis://localhost:6379/0

---

## Email Configuration (SMTP)
### Required For: Email verification
### Option 1: Gmail (Development)
1. Create or use existing Gmail account
2. Enable 2-Factor Authentication on your Google account
3. Generate App Password:
   - Go to https://myaccount.google.com/security
   - Click "2-Step Verification"
   - Scroll to "App passwords"
   - Select "Mail" and "Other (Custom name)"
   - Generate password and copy it

### Option 2: Console Backend (Testing Only)
In `backend/config/settings.py`, change:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```
This will print emails to console instead of sending them.

### Environment Variables (for Gmail):
- `EMAIL_HOST`: smtp.gmail.com
- `EMAIL_PORT`: 587
- `EMAIL_USE_TLS`: True
- `EMAIL_HOST_USER`: your-email@gmail.com
- `EMAIL_HOST_PASSWORD`: your-16-character-app-password
- `DEFAULT_FROM_EMAIL`: noreply@syncscript.com

---

## Python Virtual Environment
### Required For: Backend dependencies isolation
### Steps:
1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate virtual environment:
   ```bash
   # Windows (Git Bash)
   source venv/Scripts/activate

   # Windows (CMD)
   venv\Scripts\activate.bat

   # Windows (PowerShell)
   venv\Scripts\Activate.ps1

   # Linux/Mac
   source venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Django Secret Key
### Required For: Django security
### Steps:
1. Generate a secret key:
   ```python
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. Copy the output and add to `.env` file

### Environment Variables:
- `SECRET_KEY`: <your-generated-secret-key>

---

## Site URL Configuration
### Required For: Email verification links
### Steps:
1. For development, use default: `http://localhost:3000`
2. For production, set to your actual domain: `https://yourdomain.com`

### Environment Variables:
- `SITE_URL`: http://localhost:3000 (development) or https://yourdomain.com (production)

---

## Initial Setup Checklist

After installing all dependencies and configuring environment variables:

1. Create `.env` file in project root:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your actual values (see above sections)

3. Apply database migrations:
   ```bash
   cd backend
   python manage.py migrate
   ```

4. Create Django superuser (for admin access):
   ```bash
   python manage.py createsuperuser
   ```

5. Run development server:
   ```bash
   python manage.py runserver
   ```

6. Access admin panel at: http://localhost:8000/admin/

7. Test API endpoints using Postman or curl

---

## Cloud Storage (AWS S3 / Cloudflare R2)
### Required For: PDF uploads and file storage
### Option 1: Cloudflare R2 (Recommended for this project)
1. Create Cloudflare account at https://dash.cloudflare.com/
2. Navigate to R2 Object Storage
3. Create a new bucket (e.g., "syncscript-pdfs")
4. Generate R2 API tokens:
   - Go to "Manage R2 API Tokens"
   - Create API token with "Edit" permissions
   - Copy Access Key ID and Secret Access Key
5. Get your account-specific endpoint URL:
   - Format: `https://<account_id>.r2.cloudflarestorage.com`
   - Find your account ID in Cloudflare dashboard

### Option 2: AWS S3
1. Create AWS account at https://aws.amazon.com/
2. Navigate to S3 service
3. Create a new bucket in your preferred region
4. Create IAM user with S3 access:
   - Go to IAM → Users → Create user
   - Attach policy: `AmazonS3FullAccess` (or create custom policy)
   - Generate access keys under "Security credentials"
5. Note your bucket region (e.g., us-east-1, eu-west-1)

### Option 3: Local Development (No Cloud Storage)
If you want to test without cloud storage, files will be stored locally in `backend/media/`.
Simply don't set the AWS environment variables, and Django will use local filesystem storage.

### Environment Variables:
- `AWS_ACCESS_KEY_ID`: Your S3/R2 access key ID
- `AWS_SECRET_ACCESS_KEY`: Your S3/R2 secret access key
- `AWS_STORAGE_BUCKET_NAME`: Your bucket name (e.g., "syncscript-pdfs")
- `AWS_S3_REGION_NAME`: Region name (use "auto" for Cloudflare R2, or actual region for AWS S3)
- `AWS_S3_ENDPOINT_URL`: Full endpoint URL (Required for Cloudflare R2, e.g., "https://abc123.r2.cloudflarestorage.com")

**Note:** If AWS environment variables are not set, the application will use local filesystem storage (`MEDIA_ROOT`). This is suitable for development but not recommended for production.

---

## Optional: Pusher (Real-time Notifications)
### Required For: WebSocket notifications (future feature)
### Steps:
Will be configured when implementing real-time collaboration (US-008)

### Environment Variables (for future):
- `PUSHER_APP_ID`: Your app ID
- `PUSHER_KEY`: Your key
- `PUSHER_SECRET`: Your secret
- `PUSHER_CLUSTER`: Your cluster (e.g., us2)
