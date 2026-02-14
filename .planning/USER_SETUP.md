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

## JWT Configuration
### Required For: JWT token authentication (access and refresh tokens)
### Steps:
1. JWT token lifetimes are configured in `backend/config/settings.py` with the following defaults:
   - Access Token: 15 minutes
   - Refresh Token: 7 days
   - Token Rotation: Enabled (old refresh token invalidated after use)
   - Token Blacklisting: Enabled (logout blacklists refresh tokens)

2. These settings are managed through SIMPLE_JWT configuration and can be customized via environment variables if needed.

3. No additional setup required - JWT settings are pre-configured in the project.

### Environment Variables (Optional):
- `JWT_ACCESS_TOKEN_LIFETIME`: Access token lifetime in minutes (default: 15)
- `JWT_REFRESH_TOKEN_LIFETIME`: Refresh token lifetime in days (default: 7)

**Note:** JWT tokens are signed using Django's `SECRET_KEY`, so ensure `SECRET_KEY` is set securely (see Django Secret Key section below).

---

## Site URL Configuration
### Required For: Email verification links and password reset links
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

## System Dependencies: Poppler Utils
### Required For: PDF thumbnail generation (pdf2image library)
### Steps:

**Windows:**
1. Download poppler for Windows from: https://github.com/oschwartz10612/poppler-windows/releases
2. Extract the archive (e.g., `poppler-24.08.0.zip`)
3. Add the `bin` folder to your system PATH:
   - Search for "Environment Variables" in Windows
   - Edit "Path" variable under System Variables
   - Add the full path to poppler's `bin` folder (e.g., `C:\Program Files\poppler\bin`)
4. Restart your terminal/IDE to pick up the PATH changes
5. Verify installation:
   ```bash
   pdftoppm -v
   # Should output version information
   ```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

**macOS:**
```bash
brew install poppler
```

**Why Needed:**
The `pdf2image` Python library uses poppler's `pdftoppm` tool to convert PDF pages to images for thumbnail generation. Without poppler installed, PDF processing will fail during thumbnail generation (though metadata extraction will still work).

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

---

## Google OAuth 2.0
### Required For: OAuth authentication (Google login)
### Steps:

1. **Go to Google Cloud Console:**
   - Navigate to https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create a new project (or use existing):**
   - Click "Select a project" → "New Project"
   - Enter project name: "SyncScript" (or any name)
   - Click "Create"

3. **Enable Google+ API:**
   - In the left sidebar, go to "APIs & Services" → "Library"
   - Search for "Google+ API"
   - Click on it and press "Enable"

4. **Configure OAuth consent screen:**
   - Go to "APIs & Services" → "OAuth consent screen"
   - Select "External" user type (for testing)
   - Click "Create"
   - Fill in required fields:
     - App name: SyncScript
     - User support email: your email
     - Developer contact: your email
   - Click "Save and Continue"
   - On "Scopes" page, click "Save and Continue" (default scopes are fine)
   - On "Test users" page, add your email for testing
   - Click "Save and Continue"

5. **Create OAuth 2.0 credentials:**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Select "Web application"
   - Enter name: "SyncScript Web Client"
   - Under "Authorized redirect URIs", add:
     - Development: `http://localhost:8000/api/v1/auth/google/callback/`
     - Production: `https://api.yourdomain.com/api/v1/auth/google/callback/`
   - Click "Create"
   - Copy the **Client ID** and **Client Secret**

6. **Add credentials to .env file:**
   ```
   GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret-here
   ```

### Environment Variables:
- `GOOGLE_CLIENT_ID`: OAuth 2.0 Client ID from Google Cloud Console
- `GOOGLE_CLIENT_SECRET`: OAuth 2.0 Client Secret from Google Cloud Console

### Callback URL Pattern:
- Development: `http://localhost:8000/api/v1/auth/google/callback/`
- Production: `https://api.yourdomain.com/api/v1/auth/google/callback/`

**Important Notes:**
- Keep your Client Secret confidential
- For production, move the OAuth consent screen from "Testing" to "Published" status
- Add your production domain to authorized redirect URIs before deploying
